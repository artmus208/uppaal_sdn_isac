"""Capture software regression checks in a new immutable diagnostics directory."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import sysconfig
import time


ROOT = Path(__file__).resolve().parents[3]
STAMP = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
OUTPUT = Path(__file__).resolve().parent / f"checks-{STAMP}"
OUTPUT.mkdir()
ENV = os.environ.copy()
OVERRIDES = {
    "PYTHONDONTWRITEBYTECODE": "1",
    "UPPAAL_VERIFYTA_PATH": str(OUTPUT / "missing-verifyta"),
    "UPPAAL_MCP_WORKSPACE": str(OUTPUT / "unused-workspace"),
}
ENV.update(OVERRIDES)
SUFFIX = ".exe" if os.name == "nt" else ""
CONSOLE = str(Path(sysconfig.get_path("scripts")) / f"uppaal-verifyta{SUFFIX}")
WHEELS = Path(sys.prefix) / f"cli-build-{STAMP}"
COMMANDS = [
    ("pip-check", [sys.executable, "-m", "pip", "check"], 0),
    ("pip-freeze", [sys.executable, "-m", "pip", "freeze"], 0),
    ("unit-tests", [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], 0),
    ("coordination", [sys.executable, "scripts/check_coordination.py"], 0),
    ("build-mcp", [sys.executable, "-c", "from uppaal_mcp.server import build_mcp; print(type(build_mcp()).__name__)"], 0),
    ("list-examples", [CONSOLE, "list-examples"], 0),
    ("version-missing-tool", [CONSOLE, "version"], 2),
    ("wheel-build", [sys.executable, "-m", "build", "--wheel", "--outdir", str(WHEELS)], 0),
    ("diff-check", ["git", "diff", "--check"], 0),
]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


records = []
for name, command, expected in COMMANDS:
    print(f"Running {name}", flush=True)
    started = time.perf_counter()
    completed = subprocess.run(command, cwd=ROOT, env=ENV, capture_output=True, timeout=300, check=False)
    stdout = OUTPUT / f"{name}.stdout.txt"
    stderr = OUTPUT / f"{name}.stderr.txt"
    stdout.write_bytes(completed.stdout)
    stderr.write_bytes(completed.stderr)
    records.append({
        "name": name, "command": command, "cwd": str(ROOT), "environment_overrides": OVERRIDES,
        "exit_code": completed.returncode, "expected_exit_code": expected,
        "matches_expectation": completed.returncode == expected,
        "elapsed_seconds": round(time.perf_counter() - started, 3),
        "stdout": stdout.name, "stdout_sha256": digest(stdout),
        "stderr": stderr.name, "stderr_sha256": digest(stderr),
    })

source_paths = [
    "src/uppaal_mcp/cli.py", "tests/test_cli.py", "pyproject.toml",
    "manifests/v1.md", "manifests/collaboration-v1.yaml", "manifests/baselines/reviewer-r1.yaml",
]
metadata = {
    "run_id": f"cli-regression-{STAMP}",
    "evidence_class": "software regression diagnostics; no model checking performed",
    "issue": "https://github.com/artmus208/uppaal_sdn_isac/issues/4",
    "base_commit": "11bd69bdca9a1209f820258b3732b3c865f79035",
    "head_at_capture": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
    "git_status_at_capture": subprocess.check_output(["git", "status", "--short"], cwd=ROOT, text=True),
    "source_snapshot": "Exact working-file hashes; pending software changes are committed with this evidence.",
    "python": sys.version, "python_executable": sys.executable,
    "platform": platform.platform(), "processor": platform.processor(), "cpu_count": os.cpu_count(),
    "setup_command": "python -m venv .venv; .venv/Scripts/python.exe -m pip install -e . 'mcp>=1,<2' build",
    "setup_note": "MCP 1.x was constrained explicitly because the separate dependency fix is Issue #3.",
    "verification_evidence": "N/A; version availability and synthetic response tests do not verify properties",
    "files_sha256": {path: digest(ROOT / path) for path in source_paths},
    "files_git_object_ids": {
        path: subprocess.check_output(["git", "hash-object", f"--path={path}", path], cwd=ROOT, text=True).strip()
        for path in source_paths
    },
    "wheel_sha256": {path.name: digest(path) for path in WHEELS.glob("*.whl")},
    "commands": records,
    "all_commands_matched_expectations": all(record["matches_expectation"] for record in records),
}
(OUTPUT / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"output": str(OUTPUT), "all_commands_matched_expectations": metadata["all_commands_matched_expectations"]}))
raise SystemExit(0 if metadata["all_commands_matched_expectations"] else 1)
