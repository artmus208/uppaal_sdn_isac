"""Record #104 software checks without invoking a licensed verifier."""
import argparse
from datetime import datetime, timezone
import hashlib
from importlib.metadata import version
import json
import locale
import os
from pathlib import Path
import platform
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
SOURCES = ("src/uppaal_mcp/phy/artifacts.py", "tests/test_phy_artifacts.py")
BASE_FAILURES = (
    "test_coordination.HashAuditTests.test_exact_bytes_and_committed_manifest",
    "test_coordination_activation.CoordinationActivationTests.test_current_v2_and_historical_v1_coexist",
    "test_coordination_activation.CoordinationActivationTests.test_migration_ids_remain_unique_and_conditional",
    "test_family_baseline.FamilyBaselineTests.test_paths_and_symlink_escape_rejected",
    "test_sdn_layer.IntegratedRecorderTests.test_windows_compile_only_forwards_flag_and_translates_paths",
    "test_verification_manager.ManagerTests.test_memory_limit_measures_real_child",
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--baseline-root", type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    record = {
        "evidence_class": "software_regression_diagnostics",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "python": sys.version, "platform": platform.platform(),
        "locale_encoding": locale.getpreferredencoding(False),
        "packages": {name: version(name) for name in ("mcp", "PyYAML")},
        "source_hashes": {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in SOURCES},
        "checks": [],
    }

    def run(name, command, cwd=ROOT, test_root=None):
        env = dict(os.environ, PYTHONPATH=os.pathsep.join([str(cwd / "src"), str(test_root or cwd / "tests")]),
                   PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8", PYTHONUTF8="0")
        started = time.monotonic()
        with (output / (name + ".log")).open("wb") as log:
            try:
                result = subprocess.run(command, cwd=cwd, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=300)
                code = result.returncode
            except subprocess.TimeoutExpired:
                code = "timeout"
        data = (output / (name + ".log")).read_bytes()
        record["checks"].append({"name": name, "command": command, "cwd": str(cwd),
                                 "environment": {k: env[k] for k in ("PYTHONPATH", "PYTHONDONTWRITEBYTECODE", "PYTHONIOENCODING", "PYTHONUTF8")},
                                 "exit_code": code, "elapsed_sec": round(time.monotonic() - started, 3),
                                 "log": name + ".log", "sha256": hashlib.sha256(data).hexdigest()})
        (output / "checks.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8", newline="\n")
        print(f"{name}: exit {code}", flush=True)

    py = [sys.executable, "-B"]
    run("focused", py + ["-m", "unittest", "-v", "test_phy_artifacts", "test_phy_layer"])
    run("full-suite", py + ["-m", "unittest", "discover", "-s", "tests", "-v"])
    run("coordination", py + ["scripts/check_coordination.py"])
    run("baseline-hashes", py + ["scripts/check_coordination.py", "--audit-hashes", "--commit", "HEAD",
                                "--output", str(output / "baseline-audit.json")])
    run("phy-static-benchmarks", py + ["-m", "uppaal_mcp.cli", "phy-validate-benchmarks"])
    run("mcp-smoke", py + ["-c", "from uppaal_mcp.server import build_mcp; print(type(build_mcp()).__name__)"])
    run("cli-smoke", py + ["-m", "uppaal_mcp.cli", "list-examples"])
    run("pip-check", py + ["-m", "pip", "check"])
    if args.baseline_root:
        baseline = args.baseline_root.resolve()
        record["comparison_base"] = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=baseline, text=True).strip()
        run("baseline-regressions", py + ["-m", "unittest", "-v", "test_phy_artifacts"], baseline, ROOT / "tests")
        run("baseline-failures", py + ["-m", "unittest", "-v", *BASE_FAILURES], baseline)
    return int(any(c["exit_code"] != 0 for c in record["checks"]))


if __name__ == "__main__":
    raise SystemExit(main())
