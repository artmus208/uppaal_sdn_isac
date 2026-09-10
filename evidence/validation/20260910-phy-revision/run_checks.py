"""Record required repository checks for this documentation-only proposal."""

from datetime import datetime, timezone
from pathlib import Path
import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
import time


package = Path(__file__).resolve().parent
root = package.parents[2]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--output-dir", type=Path, default=package)
args = parser.parse_args()
output = args.output_dir.resolve()
if (output / "checks.json").exists() or (output / "checks").exists():
    parser.error("Refusing to overwrite saved checks; select a fresh --output-dir.")
logs = output / "checks"
logs.mkdir(parents=True)
python = sys.executable
env = os.environ.copy()
env["PYTHONDONTWRITEBYTECODE"] = "1"
commands = [
    ("python-version", [python, "--version"], 10),
    ("dependencies", [python, "-m", "pip", "freeze"], 30),
    ("pip-check", [python, "-m", "pip", "check"], 30),
    ("publication-audit", [python, str(package / "check_publication.py")], 30),
    ("coordination", [python, "scripts/check_coordination.py"], 30),
    ("full-suite", [python, "-m", "unittest", "discover", "-s", "tests", "-v"], 300),
    ("mcp-construction", [python, "-c", "from uppaal_mcp.server import build_mcp; print(type(build_mcp()).__name__)"], 30),
    ("examples", [str(Path(python).parent / "uppaal-verifyta"), "list-examples"], 30),
    ("verifier-version", [str(Path(python).parent / "uppaal-verifyta"), "version"], 20),
    ("whitespace", ["git", "diff", "--check", "4480f1087b93f48541a925590ae82ca86fa4b808", "HEAD"], 30),
]
report = {
    "kind": "documentation_and_software_checks",
    "started_at_utc": datetime.now(timezone.utc).isoformat(),
    "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip(),
    "initial_git_status": subprocess.check_output(["git", "status", "--short"], cwd=root, text=True),
    "operating_environment": platform.platform(),
    "python": sys.version,
    "cwd": str(root),
    "environment_overrides": {"PYTHONDONTWRITEBYTECODE": "1"},
    "verification": "not_run",
    "commands": [],
}

for name, argv, timeout in commands:
    started = time.monotonic()
    with (logs / f"{name}.stdout.txt").open("wb") as stdout, (logs / f"{name}.stderr.txt").open("wb") as stderr:
        try:
            result = subprocess.run(argv, cwd=root, env=env, stdout=stdout, stderr=stderr, timeout=timeout)
            status, code = "completed", result.returncode
        except subprocess.TimeoutExpired:
            status, code = "timeout", None
        except OSError as error:
            stderr.write(str(error).encode("utf-8"))
            status, code = "launch_error", None
    record = {"name": name, "argv": argv, "timeout_s": timeout, "duration_s": round(time.monotonic() - started, 3), "status": status, "exit_code": code}
    for channel in ("stdout", "stderr"):
        path = logs / f"{name}.{channel}.txt"
        record[channel] = {"path": str(path.relative_to(output)), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    report["commands"].append(record)
    (output / "checks.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{name}: {status}, exit={code}, {record['duration_s']}s", flush=True)

report["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
(output / "checks.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
raise SystemExit(any(item["exit_code"] != 0 for item in report["commands"]))
