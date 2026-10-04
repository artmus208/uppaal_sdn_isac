"""Record software checks for #99; never invokes the licensed verifier."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import locale
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[3]
SCOPED_TESTS = ("tests/test_coordination.py", "tests/test_coordination_activation.py")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--full", action="store_true")
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    env = dict(os.environ, PYTHONPATH=os.pathsep.join([str(ROOT / "src"), str(ROOT / "tests")]),
               PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8", PYTHONUTF8="0")
    record = {
        "evidence_class": "software_regression_diagnostics",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "root": str(ROOT), "python": sys.version, "platform": platform.platform(),
        "locale_encoding": locale.getencoding(),
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "source_hashes": {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in SCOPED_TESTS},
        "environment": {k: env[k] for k in ("PYTHONPATH", "PYTHONDONTWRITEBYTECODE", "PYTHONIOENCODING", "PYTHONUTF8")},
        "checks": [],
    }

    def run(name, command, extra_env=None):
        started = time.monotonic()
        result = subprocess.run(command, cwd=ROOT, env={**env, **(extra_env or {})},
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=300)
        log = output / (name + ".log")
        log.write_bytes(result.stdout)
        record["checks"].append({"name": name, "command": command, "environment_overrides": extra_env or {},
                                 "exit_code": result.returncode, "elapsed_sec": round(time.monotonic() - started, 3),
                                 "log": log.name, "sha256": hashlib.sha256(result.stdout).hexdigest()})
        (output / "checks.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        print(f"{name}: exit {result.returncode}", flush=True)

    py = [sys.executable, "-B"]
    focused = py + ["-m", "unittest", "-v", "test_coordination", "test_coordination_activation"]
    run("git-autocrlf", ["git", "config", "--show-origin", "--get-all", "core.autocrlf"])
    run("git-system-autocrlf", ["git", "config", "--system", "--get-all", "core.autocrlf"])
    run("child-locale", py + ["-c", "import locale,sys; print(locale.getencoding()); print(sys.flags.utf8_mode)"])
    run("focused-native", focused)
    with tempfile.TemporaryDirectory() as folder:
        for setting in ("false", "true", "input"):
            config = Path(folder) / (setting + ".gitconfig")
            content = f"[core]\n\tautocrlf = {setting}\n"
            config.write_text(content, encoding="utf-8")
            record.setdefault("global_git_configs", {})[setting] = content
            run("focused-autocrlf-" + setting, focused,
                {"GIT_CONFIG_GLOBAL": str(config), "GIT_CONFIG_NOSYSTEM": "1"})
    if args.full:
        run("full-suite", py + ["-m", "unittest", "discover", "-s", "tests", "-v"])
        run("coordination", py + ["scripts/check_coordination.py"])
        run("baseline-hashes", py + ["scripts/check_coordination.py", "--audit-hashes", "--commit", "HEAD",
                                    "--output", str(output / "baseline-audit.json")])
        run("mcp-smoke", py + ["-c", "from uppaal_mcp.server import build_mcp; print(type(build_mcp()).__name__)"])
        run("cli-smoke", py + ["-m", "uppaal_mcp", "list-examples"])
        run("pip-check", py + ["-m", "pip", "check"])
    # Expected failures in the before record are preserved verbatim, not hidden.
    return int(any(c["exit_code"] for c in record["checks"] if not c["name"].startswith("git-")))


if __name__ == "__main__":
    raise SystemExit(main())
