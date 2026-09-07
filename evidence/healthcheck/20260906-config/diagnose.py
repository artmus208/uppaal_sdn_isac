"""Read-only configuration diagnostics; use a new output directory per run.

Requires Python 3.11+ (tomllib) and a compatible MCP 1.x SDK in this interpreter.
No model checking or verifier/license configuration changes are performed.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
import tomllib

import anyio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


PROVENANCE = """
import hashlib, importlib.metadata, json, sys
from pathlib import Path
import uppaal_mcp.config, uppaal_mcp.server
print(json.dumps({
    'python': sys.version, 'executable': sys.executable,
    'mcp': importlib.metadata.version('mcp'),
    'config_source': uppaal_mcp.config.__file__,
    'config_sha256': hashlib.sha256(Path(uppaal_mcp.config.__file__).read_bytes()).hexdigest(),
    'server_source': uppaal_mcp.server.__file__,
    'server_sha256': hashlib.sha256(Path(uppaal_mcp.server.__file__).read_bytes()).hexdigest(),
    'resolved_verifyta': uppaal_mcp.config.UppaalConfig.from_env().verifyta_path,
}, indent=2))
"""


def save(path: Path, value: object) -> None:
    path.write_bytes((json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(out: Path, label: str, command: list[str], cwd: Path, env: dict[str, str]) -> subprocess.CompletedProcess:
    started = time.monotonic()
    result = subprocess.run(command, cwd=cwd, env=env, capture_output=True, timeout=180)
    stdout = out / f"{label}.stdout.txt"
    stderr = out / f"{label}.stderr.txt"
    stdout.write_bytes(result.stdout)
    stderr.write_bytes(result.stderr)
    save(out / f"{label}.command.json", {
        "command": command, "cwd": str(cwd), "returncode": result.returncode,
        "duration_seconds": time.monotonic() - started,
        "environment_overrides": {key: env[key] for key in (
            "PYTHONDONTWRITEBYTECODE", "PYTHONIOENCODING", "UPPAAL_VERIFYTA_PATH",
            "VERIFYTA_PATH", "UPPAAL_MCP_WORKSPACE", "UPPAAL_TIMEOUT_SEC",
        ) if key in env},
        "PYTHONPATH_removed": "PYTHONPATH" not in env,
        "stdout": stdout.name, "stdout_sha256": digest(stdout),
        "stderr": stderr.name, "stderr_sha256": digest(stderr),
    })
    print(f"{label}: exit {result.returncode}", flush=True)
    if result.returncode:
        raise RuntimeError(f"{label} failed; see saved stdout/stderr")
    return result


def value(response: object) -> object:
    data = response.model_dump(mode="json")
    structured = data.get("structuredContent")
    if structured is None:
        blocks = [json.loads(block["text"]) for block in data["content"] if block["type"] == "text"]
        structured = blocks[0] if len(blocks) == 1 else blocks
    if isinstance(structured, dict) and set(structured) == {"result"}:
        return structured["result"]
    return structured


async def smoke(out: Path, label: str, server: dict, env: dict[str, str]) -> None:
    destination = out / label
    destination.mkdir()
    child_env = env | server["env"]
    provenance = run(destination, "provenance", [server["command"], "-B", "-c", PROVENANCE], Path(server["cwd"]), child_env)
    save(destination / "launch.json", {"config": server, "provenance": json.loads(provenance.stdout)})
    params = StdioServerParameters(command=server["command"], args=server["args"], cwd=server["cwd"], env=child_env)
    checks = []
    with (destination / "server.stderr.txt").open("wb") as errlog:
        with anyio.fail_after(60):
            async with stdio_client(params, errlog=errlog) as (read, write):
                async with ClientSession(read, write) as session:
                    initialized = await session.initialize()
                    save(destination / "initialize.json", initialized.model_dump(mode="json"))
                    listing = await session.list_tools()
                    save(destination / "tools.json", listing.model_dump(mode="json"))
                    names = [tool.name for tool in listing.tools]
                    assert len(names) == len(set(names)) and "uppaal_version" in names
                    checks.append({"check": "initialize/list_tools", "ok": True, "tools": len(names)})

                    async def call(name: str, arguments: dict | None = None) -> object:
                        response = await session.call_tool(name, arguments or {})
                        save(destination / f"{name}.json", {"arguments": arguments or {}, "response": response.model_dump(mode="json")})
                        assert not response.isError, name
                        return value(response)

                    version = await call("uppaal_version")
                    assert version["status"] == "ok" and version["returncode"] == 0 and version["stdout"].strip()
                    checks.append({"check": "version", "ok": True, "command": version["command"]})
                    examples = await call("uppaal_list_examples")
                    assert examples
                    example = await call("uppaal_get_example", {"name": "deadlock_free"})
                    validation = await call("uppaal_validate_model", {"model_xml": example["model_xml"], "queries": example["queries"]})
                    assert validation["ok"] is True
                    checks.append({"check": "read_only_examples_and_static_validation", "ok": True})
    save(destination / "summary.json", {"classification": "version, MCP transport, and static diagnostics only", "status": "success", "checks": checks, "session_closed": True})
    print(f"{label}: initialized, {len(names)} tools, 4 read-only calls, closed", flush=True)


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    repo, out = args.repo.resolve(), args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    server = tomllib.loads((repo / "mcp_conf.conf").read_text(encoding="utf-8"))["mcp_servers"]["uppaal"]
    env = dict(os.environ)
    for key in ("PYTHONPATH", "UPPAAL_VERIFYTA_PATH", "VERIFYTA_PATH", "UPPAAL_MCP_WORKSPACE", "UPPAAL_TIMEOUT_SEC"):
        env.pop(key, None)
    env.update(PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8")
    python = str(repo / ".venv/Scripts/python.exe") if os.name == "nt" else str(repo / ".venv/bin/python")
    original = Path(server["cwd"])
    before = run(out, "configured-checkout-before", ["git", "status", "--short"], original, env).stdout
    save(out / "metadata.json", {
        "classification": "software configuration diagnostics; no model checking",
        "started_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo).decode().strip(),
        "base_commit": "11bd69bdca9a1209f820258b3732b3c865f79035",
        "platform": platform.platform(), "machine": platform.machine(), "processor": platform.processor(),
        "logical_cpu_count": os.cpu_count(), "driver_python": sys.version,
        "config_sha256": digest(repo / "src/uppaal_mcp/config.py"),
        "mcp_conf_sha256": digest(repo / "mcp_conf.conf"),
        "manifest_hashes": {path: digest(repo / path) for path in (
            "manifests/v1.md", "manifests/collaboration-v1.yaml", "manifests/baselines/reviewer-r1.yaml",
        )},
        "command": [sys.executable, *sys.argv],
    })
    worktree = json.loads(run(out, "worktree-provenance", [python, "-B", "-c", PROVENANCE], repo, env).stdout)
    assert Path(worktree["config_source"]).resolve() == repo / "src/uppaal_mcp/config.py"
    assert 1 == int(worktree["mcp"].split(".")[0]) and int(worktree["mcp"].split(".")[1]) >= 28
    assert Path(worktree["resolved_verifyta"]).resolve() == Path(server["env"]["UPPAAL_VERIFYTA_PATH"]).resolve()
    for label, command in (
        ("pip-check", [python, "-m", "pip", "check"]),
        ("pip-freeze", [python, "-m", "pip", "freeze"]),
        ("unit-tests", [python, "-B", "-m", "unittest", "discover", "-s", "tests", "-v"]),
        ("coordination", [python, "-B", "scripts/check_coordination.py"]),
        ("build-mcp", [python, "-B", "-c", "from uppaal_mcp.server import build_mcp; print(type(build_mcp()).__name__)"]),
        ("list-examples", [python, "-B", "-m", "uppaal_mcp.cli", "list-examples"]),
        ("version-default", [python, "-B", "-m", "uppaal_mcp.cli", "version"]),
        ("version-native-raw", [worktree["resolved_verifyta"], "--version"]),
    ):
        run(out, label, command, repo, env)
    await smoke(out, "configured-original-environment", server, env)
    changed_server = server | {"command": python, "cwd": str(repo), "env": {
        "UPPAAL_MCP_WORKSPACE": str(out / "unused-workspace"), "UPPAAL_TIMEOUT_SEC": "60",
    }}
    await smoke(out, "changed-worktree-environment", changed_server, env)
    after = run(out, "configured-checkout-after", ["git", "status", "--short"], original, env).stdout
    assert before == after, "Configured checkout status changed during diagnostics"
    save(out / "summary.json", {"status": "success", "classification": "software configuration diagnostics only", "configured_checkout_status_unchanged": True})
    hashes = {str(path.relative_to(out)).replace("\\", "/"): digest(path) for path in sorted(out.rglob("*")) if path.is_file()}
    save(out / "SHA256.json", hashes)


if __name__ == "__main__":
    anyio.run(main)
