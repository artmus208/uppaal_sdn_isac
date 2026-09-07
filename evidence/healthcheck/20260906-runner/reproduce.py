"""Record software regression diagnostics; no model checking is performed."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import runpy
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch


REPO = Path(__file__).resolve().parents[3]


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True, help="New directory; existing paths are rejected.")
    parser.add_argument("--install", action="store_true", help="Install this checkout and a compatible MCP 1.x SDK.")
    args = parser.parse_args()
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=False)
    checks = []
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONUTF8="1")

    def command(name: str, argv: list[str]) -> subprocess.CompletedProcess:
        started = datetime.now(timezone.utc).isoformat()
        result = subprocess.run(argv, cwd=REPO, env=env, capture_output=True, text=True, encoding="utf-8", timeout=300)
        (output / f"{name}.stdout.txt").write_text(result.stdout, encoding="utf-8")
        (output / f"{name}.stderr.txt").write_text(result.stderr, encoding="utf-8")
        checks.append({
            "name": name, "command": argv, "cwd": str(REPO), "started_at_utc": started,
            "exit_code": result.returncode, "stdout": f"{name}.stdout.txt", "stderr": f"{name}.stderr.txt",
        })
        write_json(output / "checks.json", checks)
        print(f"{name}: exit {result.returncode}", flush=True)
        return result

    if args.install:
        installed = command("install", [sys.executable, "-m", "pip", "install", "--disable-pip-version-check", "-e", ".", "mcp>=1,<2"])
        if installed.returncode:
            return installed.returncode

    # Select this checkout even when editable installation happened in this process
    # (its new .pth file is otherwise loaded only by the next Python process).
    sys.path.insert(0, str(REPO / "src"))
    from uppaal_mcp.config import UppaalConfig
    from uppaal_mcp.verifyta import VerifytaRunner

    fixtures = runpy.run_path(str(REPO / "tests/test_verifyta_parser.py"))
    one = fixtures["FIRST_SUCCESS"]
    two = fixtures["COMPLETE_SUCCESS"]
    cases = [
        ("complete_success_control", 0, two, "", "satisfied", None),
        ("error_after_first_success", 1, one + "Verifying formula 2 at queries.q:2\n", "syntax error in second query\n", "error", None),
        ("incomplete_output_returncode_zero", 0, one, "", "error", None),
        ("error_after_success_returncode_zero", 0, one, "error: second query failed\n", "error", None),
        ("error_without_outcomes_control", 2, "", "syntax error\n", "error", None),
        ("timeout_after_first_success_control", None, one, "synthetic timeout\n", "timeout", "TimeoutExpired"),
        ("missing_tool_control", None, "", "synthetic missing verifier", "tool_not_found", "FileNotFoundError"),
    ]
    diagnostics = []
    for name, returncode, stdout, stderr, expected, exception in cases:
        runner = VerifytaRunner(UppaalConfig("mock-verifyta", output / "mock-workspace", timeout_sec=1))
        mock = {"return_value": subprocess.CompletedProcess(["mock-verifyta"], returncode, stdout, stderr)}
        if exception == "TimeoutExpired":
            mock = {"side_effect": subprocess.TimeoutExpired(["mock-verifyta"], 1, output=stdout.encode(), stderr=stderr.encode())}
        elif exception == "FileNotFoundError":
            mock = {"side_effect": FileNotFoundError(stderr)}
        with patch("uppaal_mcp.verifyta.subprocess.run", **mock):
            result = runner.verify(model_xml=fixtures["MODEL_XML"], queries=fixtures["QUERIES"])
        diagnostics.append({
            "case": name, "expected_status": expected, "matches_expectation": result.status == expected,
            "synthetic_input": {"returncode": returncode, "stdout": stdout, "stderr": stderr, "exception": exception},
            "result": result.to_dict(),
        })
    write_json(output / "synthetic_runner_results.json", {
        "evidence_class": "synthetic software regression diagnostics; not model checking",
        "real_verifyta_executed": False, "requested_query_count": 2, "cases": diagnostics,
    })
    required = [
        command("focused-tests", [sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests", "-p", "test_verifyta_parser.py", "-v"]),
        command("full-tests", [sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests", "-v"]),
        command("coordination", [sys.executable, "-B", "scripts/check_coordination.py"]),
        command("build-mcp", [sys.executable, "-B", "-c", "from uppaal_mcp.server import build_mcp; print(type(build_mcp()).__name__)"]),
        command("list-examples", [sys.executable, "-B", "-m", "uppaal_mcp.cli", "list-examples"]),
        command("pip-check", [sys.executable, "-m", "pip", "check"]),
    ]
    command("version-default", [sys.executable, "-B", "-m", "uppaal_mcp.cli", "version"])
    if Path("D:/UPPAAL/app/bin/verifyta.exe").is_file():
        command("version-explicit", [sys.executable, "-B", "-m", "uppaal_mcp.cli", "--verifyta-path", "D:/UPPAAL/app/bin/verifyta.exe", "version"])
    packages = command("pip-freeze", [sys.executable, "-m", "pip", "freeze"])
    revision = command("source-commit", ["git", "rev-parse", "HEAD"])
    files = ["src/uppaal_mcp/verifyta.py", "tests/test_verifyta_parser.py", "manifests/baselines/reviewer-r1.yaml", "evidence/healthcheck/20260906-runner/reproduce.py"]
    write_json(output / "metadata.json", {
        "issue": "https://github.com/artmus208/uppaal_sdn_isac/issues/2",
        "evidence_class": "software regression diagnostics; no model checking",
        "base_commit": "11bd69bdca9a1209f820258b3732b3c865f79035",
        "source_commit": revision.stdout.strip(), "source_snapshot": "worktree files identified by exact hashes below",
        "source_hashes": {name: hashlib.sha256((REPO / name).read_bytes()).hexdigest() for name in files},
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "python": sys.version, "python_executable": sys.executable, "platform": platform.platform(),
        "machine": platform.machine(), "processor": platform.processor(), "logical_cpu_count": os.cpu_count(),
        "environment_overrides": {"PYTHONDONTWRITEBYTECODE": "1", "PYTHONUTF8": "1"},
        "installed_packages": packages.stdout.splitlines(),
        "synthetic_cases_match": all(item["matches_expectation"] for item in diagnostics),
        "required_commands_exit_zero": all(item.returncode == 0 for item in required),
        "limitations": [
            "Windows/Python environment, not the Ubuntu/Python 3.12 CI environment.",
            "MCP 1.x installed explicitly for the independent base; dependency policy belongs to issue #3.",
            "Default-path and CLI exit-code problems are outside issue #2 and recorded without treating shell exit zero as verifier success.",
            "Version probes are availability diagnostics, not model checking runs.",
        ],
    })
    return 0 if all(item["matches_expectation"] for item in diagnostics) and all(item.returncode == 0 for item in required) else 1


if __name__ == "__main__":
    raise SystemExit(main())
