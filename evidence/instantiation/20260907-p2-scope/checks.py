"""Record isolated installation and relevant checks without overwriting logs."""
import argparse
import datetime
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--python", type=Path, required=True)
    parser.add_argument("--install", action="store_true")
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    python = str(args.python.resolve())
    cli = str(Path(python).parent / ("uppaal-verifyta.exe" if os.name == "nt" else "uppaal-verifyta"))
    script = lambda name: str(HERE / name)
    commands = []
    if args.install:
        commands.append(("install", [python, "-m", "pip", "install", "-e", ".", "PyYAML"]))
    commands.extend([
        ("pip-check", [python, "-m", "pip", "check"]),
        ("inventory", [python, "-B", script("inventory.py"), "--check"]),
        ("specification", [python, "-B", script("check_spec.py")]),
        ("coordination", [python, "-B", "scripts/check_coordination.py"]),
        ("yaml", [python, "-c", "import pathlib,yaml; files=sorted(pathlib.Path('manifests').rglob('*.yaml')); [yaml.safe_load(p.read_text(encoding='utf-8')) for p in files]; print(str(len(files))+' YAML files parsed; static only')"]),
        ("unit-tests", [python, "-B", "-m", "unittest", "discover", "-s", "tests", "-v"]),
        ("mcp-construction", [python, "-c", "from uppaal_mcp.server import build_mcp; print(type(build_mcp()).__name__)"]),
        ("examples", [cli, "list-examples"]),
        ("diff-check", ["git", "diff", "--check"]),
    ])
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    # Preserve existing process Git overrides and append this one last.
    index = int(env.get("GIT_CONFIG_COUNT", "0"))
    env[f"GIT_CONFIG_KEY_{index}"] = "core.autocrlf"
    env[f"GIT_CONFIG_VALUE_{index}"] = "false"
    env["GIT_CONFIG_COUNT"] = str(index + 1)
    report = {"evidence_class": "software_and_static_specification_checks_not_verification",
              "cwd": str(ROOT), "python": python, "platform": platform.platform(),
              "processor": platform.processor(), "cpu_count": os.cpu_count(),
              "head_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
              "worktree_status_at_start": subprocess.check_output(["git", "status", "--short"], cwd=ROOT, text=True),
              "process_environment_overrides": {"PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1", "core.autocrlf": "false"},
              "git_override_reason": "Native Windows hash-audit fixture is sensitive to system core.autocrlf=input; override is per process only.",
              "commands": []}
    report["artifact_hashes_at_start"] = {str(p.relative_to(HERE)).replace("\\", "/"): hashlib.sha256(p.read_bytes()).hexdigest()
                                           for p in sorted(HERE.iterdir()) if p.is_file()}
    for name, command in commands:
        start = time.monotonic()
        utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
        timed_out = False
        try:
            proc = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, timeout=300)
            code, stdout, stderr = proc.returncode, proc.stdout, proc.stderr
        except subprocess.TimeoutExpired as e:
            code, stdout, stderr, timed_out = None, e.stdout or b"", e.stderr or b"", True
        except OSError as e:
            code, stdout, stderr = None, b"", str(e).encode("utf-8")
        record = {"name": name, "command": command, "started_at_utc": utc,
                  "runtime_seconds": time.monotonic()-start, "exit_code": code, "timed_out": timed_out}
        for stream, content in (("stdout", stdout), ("stderr", stderr)):
            path = output / f"{name}.{stream}.log"
            path.write_bytes(content)
            record[f"{stream}_path"] = path.name
            record[f"{stream}_sha256"] = hashlib.sha256(content).hexdigest()
        report["commands"].append(record)
        (output / "checks.json").write_bytes((json.dumps(report, indent=2) + "\n").encode("utf-8"))
        print(f"{name}: exit={code}; timeout={timed_out}", flush=True)
    return 1 if any(r["exit_code"] != 0 for r in report["commands"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
