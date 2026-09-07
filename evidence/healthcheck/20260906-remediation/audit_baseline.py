"""Read-only exact-byte baseline audit; software diagnostic, not verification.

Requires PyYAML. Exit 0 means all recorded hashes match, 1 means drift/missing
inputs, and 2 means invocation/parse failure. Never rewrites a manifest.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--commit", help="Hash exact Git blobs at this ref instead of checkout bytes")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    repo = args.repo.resolve()
    commit = subprocess.check_output(
        ["git", "rev-parse", "--verify", f"{args.commit or 'HEAD'}^{{commit}}"], cwd=repo, text=True
    ).strip()

    def read(path: str) -> bytes | None:
        if args.commit:
            result = subprocess.run(
                ["git", "show", f"{commit}:{path}"], cwd=repo, capture_output=True, check=False
            )
            return result.stdout if result.returncode == 0 else None
        target = (repo / path).resolve()
        if not target.is_relative_to(repo):
            raise ValueError(f"Input escapes repository: {path}")
        return target.read_bytes() if target.is_file() else None

    manifest_path = "manifests/baselines/reviewer-r1.yaml"
    manifest_bytes = read(manifest_path)
    if manifest_bytes is None:
        raise ValueError(f"Missing {manifest_path}")
    manifest = yaml.safe_load(manifest_bytes)
    pairs: list[dict] = []

    def walk(node: object, key: str = "") -> None:
        if isinstance(node, dict):
            if isinstance(node.get("path"), str) and isinstance(node.get("sha256"), str):
                content = read(node["path"])
                actual = sha256(content) if content is not None else None
                pairs.append({"field": key, "path": node["path"],
                              "expected_sha256": node["sha256"], "actual_sha256": actual,
                              "exists": content is not None, "matches": actual == node["sha256"]})
            for name, value in node.items():
                walk(value, f"{key}.{name}" if key else name)
        elif isinstance(node, list):
            for index, value in enumerate(node):
                walk(value, f"{key}[{index}]")

    walk(manifest)
    common: list[dict] = []
    for name, definition in manifest["hashing"]["common_hashes"].items():
        if not isinstance(definition, dict) or "inputs" not in definition:
            continue
        paths = definition["inputs"]
        if "bytewise path order" in definition["construction"]:
            paths = sorted(paths, key=lambda path: path.encode("utf-8"))
        records = []
        inputs = []
        for path in paths:
            content = read(path)
            digest = sha256(content) if content is not None else None
            inputs.append({"path": path, "sha256": digest})
            if digest is not None:
                records.append(f"{digest}  {path}\n")
        actual = sha256("".join(records).encode("utf-8")) if len(records) == len(paths) else None
        common.append({"name": name, "expected_sha256": definition["value"],
                       "actual_sha256": actual, "matches": actual == definition["value"],
                       "inputs": inputs})
    drift = sum(not pair["matches"] for pair in pairs)
    aggregate_drift = sum(not item["matches"] for item in common)
    result = {
        "diagnostic_class": "read_only_hash_audit_not_model_checking",
        "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_root": str(repo), "source_commit": commit,
        "input_mode": "exact_git_blobs" if args.commit else "exact_checkout_bytes",
        "command": [sys.executable, *sys.argv], "python": sys.version,
        "platform": platform.platform(), "pyyaml_version": yaml.__version__,
        "manifest_path": manifest_path, "manifest_sha256": sha256(manifest_bytes),
        "baseline_id": manifest["metadata"]["id"],
        "baseline_frozen": manifest["metadata"]["frozen"],
        "gate_1_status": manifest["gate_1"]["status"],
        "file_pairs": pairs, "common_hashes": common,
        "recorded_file_count": len(pairs), "mismatch_count": drift,
        "common_hash_mismatch_count": aggregate_drift,
        "hash_status": "mismatch" if drift or aggregate_drift else "match",
        "acceptance": "No scientific verification or gate acceptance implied by hash equality.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    # A rerun must select a new destination to preserve the original evidence.
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, indent=2, ensure_ascii=False)
        stream.write("\n")
    print(f"{len(pairs)} files; {drift} file mismatches; {aggregate_drift} aggregate mismatches")
    return 1 if drift or aggregate_drift else 0


if __name__ == "__main__":
    raise SystemExit(main())
