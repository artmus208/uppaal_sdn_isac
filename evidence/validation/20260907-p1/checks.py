#!/usr/bin/env python3
"""Record repository/P1 checks to a NEW output directory; never model checking."""
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--verifyta-cwd", type=Path,
                        help="Optional actual installation cwd for the version diagnostic only")
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONPATH=str(ROOT / "src"))
    # All incidental runner output belongs to this new diagnostic directory.
    env["UPPAAL_MCP_WORKSPACE"] = str(output / "workspace")
    commands = [
        ("inventory", [sys.executable, str(HERE / "inventory.py"), "--check"], ROOT, 0),
        ("coordination", [sys.executable, "scripts/check_coordination.py"], ROOT, 0),
        ("unittest", [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], ROOT, 0),
        ("mcp-build", [sys.executable, "-c", "from uppaal_mcp.server import build_mcp; print(type(build_mcp()).__name__)"], ROOT, 0),
        ("examples", [sys.executable, "-m", "uppaal_mcp.cli", "list-examples"], ROOT, 0),
        ("baseline-audit", [sys.executable, "scripts/check_coordination.py", "--audit-hashes", "--commit",
         "f2f714a26d6b9d9f538ef1a16b53c3e060768a11", "--output", str(output / "baseline-audit.json")], ROOT, None),
    ]
    if args.verifyta_cwd:
        commands.append(("verifyta-version", [sys.executable, "-m", "uppaal_mcp.cli", "--timeout-sec", "15", "version"], args.verifyta_cwd.resolve(), None))
    results = []
    for name, command, cwd, expected in commands:
        start = time.time()
        try:
            run = subprocess.run(command, cwd=cwd, env=env, capture_output=True, timeout=180)
            rc, stdout, stderr = run.returncode, run.stdout, run.stderr
        except subprocess.TimeoutExpired as exc:
            rc, stdout, stderr = None, exc.stdout or b"", exc.stderr or b""
        record = {"name": name, "command": command, "cwd": str(cwd), "exit_code": rc,
                  "expected_exit_code": expected, "elapsed_s": round(time.time() - start, 3)}
        for stream, content in (("stdout", stdout), ("stderr", stderr)):
            path = output / f"{name}.{stream}.log"
            path.write_bytes(content)
            record[stream] = {"path": path.name, "sha256": hashlib.sha256(content).hexdigest()}
        results.append(record)
        print(name, "exit", rc, flush=True)
    metadata = {"evidence_kind": "source_and_software_checks_not_model_checking",
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "python": sys.version, "platform": platform.platform(), "machine": platform.machine(),
        "packages": {name: importlib.metadata.version(name) for name in ("mcp", "PyYAML")},
        "environment_overrides": {k: env[k] for k in ("PYTHONPATH", "PYTHONDONTWRITEBYTECODE", "UPPAAL_MCP_WORKSPACE")},
        "results": results, "verification": "not_run"}
    (output / "checks.json").write_text(json.dumps(metadata, indent=2) + "\n")
    raise SystemExit(1 if any(x["expected_exit_code"] is not None and x["exit_code"] != x["expected_exit_code"] for x in results) else 0)


if __name__ == "__main__":
    main()
