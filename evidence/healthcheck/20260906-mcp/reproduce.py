"""Install and check Issue #3 in a new venv, saving commands and raw logs.

Run from the repository root. --output must name a new directory.
The disposable venv is retained under the operating system's temp directory.
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
import tempfile
import time


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--sdk", help="Optional exact supported SDK version to exercise")
    args = parser.parse_args()
    repository = Path(__file__).resolve().parents[3]
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    venv_root = Path(tempfile.mkdtemp(prefix="uppaal-mcp-issue3-")) / "venv"
    python = venv_root / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    env_overrides = {"PYTHONDONTWRITEBYTECODE": "1", "PYTHONUTF8": "1"}
    env = dict(os.environ, **env_overrides)
    # A clean venv must not inherit an external PYTHONPATH/package override.
    env.pop("PYTHONPATH", None)
    env.pop("PYTHONHOME", None)
    source_paths = [
        "pyproject.toml", "src/uppaal_mcp/server.py", "tests/test_phy_layer.py",
        "tests/test_mcp_startup.py", "manifests/baselines/reviewer-r1.yaml",
        "evidence/healthcheck/20260906-mcp/reproduce.py",
        "evidence/healthcheck/20260906-mcp/smoke.py",
    ]
    metadata = {
        "run_id": output.name,
        "issue": "https://github.com/artmus208/uppaal_sdn_isac/issues/3",
        "evidence_class": "software diagnostics; no model checking or gate acceptance",
        "base_commit": "11bd69bdca9a1209f820258b3732b3c865f79035",
        "source_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=repository, text=True
        ).strip(),
        "initial_git_status": subprocess.check_output(
            ["git", "status", "--short"], cwd=repository, text=True
        ),
        "source_sha256": {path: sha256(repository / path) for path in source_paths},
        "environment": {
            "platform": platform.platform(), "python": sys.version,
            "bootstrap_executable": sys.executable, "cpu": platform.processor(),
            "logical_cpu_count": os.cpu_count(), "venv": str(venv_root),
            "overrides": env_overrides, "removed": ["PYTHONPATH", "PYTHONHOME"],
        },
        "sdk_requested": args.sdk or "pyproject.toml constraint, normal resolution",
        "started_at_utc": datetime.now(timezone.utc).isoformat(),
        "commands": [],
    }

    def capture(name: str, command: list[str], timeout: int = 300) -> None:
        started = time.monotonic()
        result = subprocess.run(
            command, cwd=repository, env=env, capture_output=True, timeout=timeout
        )
        stdout = output / f"{name}.stdout.txt"
        stderr = output / f"{name}.stderr.txt"
        stdout.write_bytes(result.stdout)
        stderr.write_bytes(result.stderr)
        metadata["commands"].append({
            "name": name, "command": command, "cwd": str(repository),
            "exit_code": result.returncode, "elapsed_sec": time.monotonic() - started,
            "stdout": stdout.name, "stdout_sha256": sha256(stdout),
            "stderr": stderr.name, "stderr_sha256": sha256(stderr),
        })
        (output / "run.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        print(f"{name}: exit {result.returncode}", flush=True)
        if result.returncode:
            raise RuntimeError(f"{name} failed; see {stdout} and {stderr}")

    try:
        capture("create-venv", [sys.executable, "-m", "venv", str(venv_root)])
        install = [str(python), "-m", "pip", "install", "-e", "."]
        if args.sdk:
            install.append(f"mcp=={args.sdk}")
        capture("install", install)
        capture("pip-check", [str(python), "-m", "pip", "check"])
        capture("pip-freeze", [str(python), "-m", "pip", "freeze", "--all"])
        capture("build-mcp", [str(python), "-c", (
            "import asyncio,json; from importlib.metadata import version; "
            "from uppaal_mcp.server import build_mcp; server=build_mcp(); "
            "print(json.dumps({'sdk_version':version('mcp'),'server_name':server.name,"
            "'tools':[tool.name for tool in asyncio.run(server.list_tools())]},indent=2))"
        )])
        capture("unit-tests", [str(python), "-m", "unittest", "discover", "-s", "tests", "-v"])
        capture("coordination", [str(python), "scripts/check_coordination.py"])
        capture("stdio", [str(python), str(Path(__file__).with_name("smoke.py"))], timeout=45)
        metadata["status"] = "success"
        return 0
    except Exception as error:
        metadata["status"] = "error"
        metadata["error"] = str(error)
        print(error, file=sys.stderr)
        return 1
    finally:
        metadata["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
        (output / "run.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
