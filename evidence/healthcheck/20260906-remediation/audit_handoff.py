"""Audit committed fix scopes and preserve a snapshot of the original checkout."""
from __future__ import annotations

import fnmatch
import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


DIRECTORY = Path(__file__).resolve().parent
REPOSITORY = DIRECTORY.parents[2]


def git(*args: str, cwd: Path = REPOSITORY) -> bytes:
    return subprocess.check_output(["git", *args], cwd=cwd)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DIRECTORY / "scope-and-artifact-audit.json")
    args = parser.parse_args()
    index = json.loads((DIRECTORY / "results.json").read_text(encoding="utf-8"))
    results = []
    for task in index["tasks"]:
        files = git("diff", "--name-only", index["base_commit"], task["head"]).decode("utf-8").splitlines()
        outside = [path for path in files if not any(fnmatch.fnmatchcase(path, pattern) for pattern in task["write_scope"])]
        files_and_hashes = {path: hashlib.sha256(git("show", f"{task['head']}:{path}")).hexdigest() for path in files}
        whitespace = subprocess.run(["git", "diff", "--check", index["base_commit"], task["head"]], cwd=Path(task["worktree"]), capture_output=True)
        results.append({"issue": task["issue"], "head": task["head"], "changed_file_count": len(files),
                        "outside_scope": outside, "git_diff_check_exit_code": whitespace.returncode,
                        "git_diff_check_stdout": whitespace.stdout.decode("utf-8", errors="replace"),
                        "git_diff_check_stderr": whitespace.stderr.decode("utf-8", errors="replace"),
                        "committed_file_sha256": files_and_hashes})
        if outside or whitespace.returncode:
            raise RuntimeError(f"Scope/whitespace check failed for Issue {task['issue']}")

    original = Path("D:/uppaal_mcp")
    before = json.loads((DIRECTORY / "original-checkout-before.json").read_text(encoding="utf-8"))
    after = {"status": git("status", "--short", cwd=original).decode("utf-8"),
             "files": {path: hashlib.sha256((original / path).read_bytes()).hexdigest() if (original / path).is_file() else None for path in before["files"]}}
    original_unchanged = before == after
    report = {"observed_at_utc": datetime.now(timezone.utc).isoformat(), "tasks": results,
              "original_checkout_unchanged": original_unchanged,
              "protected_file_count": len(before["files"]), "original_checkout_after": after}
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(report, stream, indent=2, ensure_ascii=False)
        stream.write("\n")
    if not original_unchanged:
        raise RuntimeError("Original checkout differs from the initial snapshot; inspect external edits.")
    print(f"{len(results)} scoped commits checked; {len(before['files'])} original files unchanged")


if __name__ == "__main__":
    main()
