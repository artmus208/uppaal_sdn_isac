"""Exact-byte audit of the historical candidate; never changes the baseline."""
from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

MANIFEST = "manifests/baselines/reviewer-r1.yaml"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def audit(repo, ref=None):
    import yaml  # Optional dependency of the explicit audit, not structural CI.

    repo = Path(repo).resolve()
    commit = subprocess.check_output(
        ["git", "rev-parse", "--verify", f"{ref or 'HEAD'}^{{commit}}"],
        cwd=repo, text=True, stderr=subprocess.PIPE).strip()

    def read(path):
        parts = PurePosixPath(path)
        if parts.is_absolute() or ".." in parts.parts or "\\" in path:
            raise ValueError(f"Invalid repository path: {path}")
        if ref:
            result = subprocess.run(["git", "show", f"{commit}:{path}"], cwd=repo,
                                    capture_output=True)
            return result.stdout if result.returncode == 0 else None
        target = (repo / path).resolve()
        if not target.is_relative_to(repo):
            raise ValueError(f"Path escapes repository: {path}")
        return target.read_bytes() if target.is_file() else None

    raw = read(MANIFEST)
    if raw is None:
        raise ValueError(f"Missing manifest: {MANIFEST}")
    try:
        manifest = yaml.safe_load(raw)
    except yaml.YAMLError as error:
        raise ValueError(f"Invalid YAML: {error}") from error
    pairs = []

    def walk(node, field=""):
        if isinstance(node, dict):
            if isinstance(node.get("path"), str) and isinstance(node.get("sha256"), str):
                data = read(node["path"])
                actual = digest(data) if data is not None else None
                pairs.append(dict(field=field, path=node["path"],
                                  expected_sha256=node["sha256"], actual_sha256=actual,
                                  matches=actual == node["sha256"]))
            for key, value in node.items():
                walk(value, f"{field}.{key}" if field else key)
        elif isinstance(node, list):
            for index, value in enumerate(node):
                walk(value, f"{field}[{index}]")

    walk(manifest)
    if not pairs:
        raise ValueError("Manifest contains no file hashes")
    aggregates = []
    constructions = {
        "sha256 of concatenated sha256sum records in the listed order": False,
        "sha256 of concatenated sha256sum records for the listed files in bytewise path order": True,
    }
    definitions = manifest["hashing"]["common_hashes"]
    for name in ("source_hash", "generator_hash"):
        definition = definitions[name]
        construction = definition["construction"]
        if construction not in constructions:
            raise ValueError(f"Unsupported hash construction: {construction}")
        paths = definition["inputs"]
        if not paths or not all(isinstance(path, str) for path in paths):
            raise ValueError(f"Invalid aggregate inputs: {name}")
        if constructions[construction]:
            paths = sorted(paths, key=lambda path: path.encode("utf-8"))
        inputs = []
        for path in paths:
            data = read(path)
            inputs.append(dict(path=path, sha256=digest(data) if data is not None else None))
        actual = None
        if all(item["sha256"] is not None for item in inputs):
            actual = digest("".join(f'{item["sha256"]}  {item["path"]}\n'
                                    for item in inputs).encode("utf-8"))
        aggregates.append(dict(name=name, expected_sha256=definition["value"],
                               actual_sha256=actual, matches=actual == definition["value"],
                               inputs=inputs))
    drift = sum(not item["matches"] for item in pairs)
    aggregate_drift = sum(not item["matches"] for item in aggregates)
    return dict(diagnostic_class="hash_identity_not_verification", source_root=str(repo),
                source_commit=commit, input_mode="exact_git_blobs" if ref else "exact_checkout_bytes",
                observed_at_utc=datetime.now(timezone.utc).isoformat(),
                command=[sys.executable, *sys.argv], python=sys.version,
                platform=platform.platform(), pyyaml_version=yaml.__version__,
                manifest_path=MANIFEST, manifest_sha256=digest(raw),
                baseline_id=manifest["metadata"]["id"],
                baseline_frozen=manifest["metadata"]["frozen"],
                gate_1_status=manifest["gate_1"]["status"],
                file_pairs=pairs, common_hashes=aggregates,
                recorded_file_count=len(pairs), mismatch_count=drift,
                common_hash_mismatch_count=aggregate_drift,
                hash_status="mismatch" if drift or aggregate_drift else "match")


def run(repo, ref, output):
    try:
        result = audit(repo, ref)
        output = Path(output)
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(result, stream, indent=2, ensure_ascii=False)
            stream.write("\n")
    except (OSError, ValueError, KeyError, TypeError, ImportError, subprocess.CalledProcessError) as error:
        print(f"Hash audit error: {error}", file=sys.stderr)
        return 2
    print(f'{result["recorded_file_count"]} file hashes; {result["mismatch_count"]} mismatches; '
          f'{result["common_hash_mismatch_count"]} aggregate mismatches (not verification).')
    return int(result["hash_status"] != "match")
