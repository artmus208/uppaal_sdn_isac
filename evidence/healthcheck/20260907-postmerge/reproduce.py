"""Capture post-merge software diagnostics into a new directory; never run model checking."""
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

ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--environment-label", required=True)
    parser.add_argument("--version-only", action="store_true")
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "UPPAAL_MCP_WORKSPACE": str(output / "workspace")}
    records = []

    def capture(name, command, timeout=180):
        start = time.monotonic()
        try:
            proc = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, timeout=timeout)
            code, stdout, stderr = proc.returncode, proc.stdout, proc.stderr
        except subprocess.TimeoutExpired as error:
            code, stdout, stderr = "timeout", error.stdout or b"", error.stderr or b""
        item = {"name": name, "command": command, "cwd": str(ROOT), "exit_code": code,
                "runtime_seconds": time.monotonic() - start}
        for kind, data in [("stdout", stdout), ("stderr", stderr)]:
            path = output / f"{name}.{kind}.txt"
            path.write_bytes(data)
            item[kind] = {"path": path.name, "sha256": hashlib.sha256(data).hexdigest()}
        records.append(item)
        print(f"{name}: {code}", flush=True)
        return code

    py = sys.executable
    cli = str(Path(py).parent / ("uppaal-verifyta.exe" if os.name == "nt" else "uppaal-verifyta"))
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    capture("tracked-diff", ["git", "diff", "HEAD", "--", ".", ":(exclude)evidence/healthcheck/20260907-postmerge/**"])
    if not args.version_only:
        capture("install", [py, "-m", "pip", "install", "-e", "."], timeout=180)
        capture("audit-dependency", [py, "-m", "pip", "install", "PyYAML==6.0.3"])
        capture("pip-check", [py, "-m", "pip", "check"])
        capture("packages", [py, "-m", "pip", "list", "--format=json"])
        capture("structural", [py, "scripts/check_coordination.py"])
        capture("yaml", [py, "-c", 'from pathlib import Path; import yaml; [yaml.safe_load(p.read_bytes()) for p in Path("manifests").rglob("*.yaml")]; print("YAML parsed")'])
        capture("unit", [py, "-m", "unittest", "discover", "-s", "tests", "-v"])
        capture("build-mcp", [py, "-c", 'from uppaal_mcp.server import build_mcp; print(type(build_mcp()).__name__)'])
        capture("examples", [cli, "list-examples"])
        capture("stdio", [py, str(SCRIPT_DIR / "stdio_smoke.py")], timeout=60)
        capture("baseline-audit", [py, "scripts/check_coordination.py", "--audit-hashes", "--commit", commit,
                                   "--output", str(output / "baseline-hashes.json")])
    capture("version", [cli, "version"], timeout=30)
    result = {"diagnostic_class": "software_checks_not_model_checking", "source_commit": commit,
              "environment_label": args.environment_label, "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
              "platform": platform.platform(), "python": sys.version, "cpu_count": os.cpu_count(),
              "workspace_override": env["UPPAAL_MCP_WORKSPACE"], "commands": records}
    (output / "results.json").write_text(json.dumps(result, indent=2) + "\n")
    # The report preserves failures; callers must inspect individual commands.
    return 0 if all(r["exit_code"] == 0 for r in records) else 1


if __name__ == "__main__":
    raise SystemExit(main())
