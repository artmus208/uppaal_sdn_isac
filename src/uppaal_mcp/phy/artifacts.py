from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .alpha import default_profile
from .reports import generate_report_bundle


GENERATOR_VERSION = "phy-generator-v0.6-readable-layout"
CACHE_FORMAT_VERSION = 2
CHECKSUM_FILE = "artifact_checksums.json"
REPORT_FILES = ("report.md", "traceability_matrix.md", "model_summary.md",
                "model_map.md", "template_map.md", "channels_map.md")


def build_run_metadata(
    *,
    source_text: str | None,
    contract_json: dict,
    model_xml: str,
    queries: str,
    profile: dict | None = None,
    result_json: dict | None = None,
    verifyta_version: str | None = None,
    verifyta_command: list[str] | None = None,
    options: list[str] | None = None,
    trace_text: str | None = None,
) -> dict:
    profile = profile or default_profile()
    source_hash = _sha_text(source_text or "")
    contract_hash = _sha_json(contract_json)
    model_hash = _sha_text(model_xml)
    query_hash = _sha_text(queries)
    profile_hash = _sha_json(profile)
    result_hash = _sha_json(result_json) if result_json is not None else None
    cache_key = _sha_json(
        {
            "cache_format_version": CACHE_FORMAT_VERSION,
            "source_hash": source_hash,
            "has_source": source_text is not None,
            "contract_hash": contract_hash,
            "model_hash": model_hash,
            "profile_hash": profile_hash,
            "result_hash": result_hash,
            "trace_hash": _sha_text(trace_text) if trace_text is not None else None,
            "generator_version": GENERATOR_VERSION,
            "verifyta_version": verifyta_version or "unknown",
            "verifyta_command": list(verifyta_command or []),
            "query_hash": query_hash,
            "options": options or [],
        }
    )
    run_id = _run_id(cache_key)
    return {
        "run_id": run_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "generator_version": GENERATOR_VERSION,
        "cache_key": cache_key,
        "hashes": {
            "source_hash": source_hash,
            "contract_hash": contract_hash,
            "model_hash": model_hash,
            "query_hash": query_hash,
            "profile_hash": profile_hash,
            "result_hash": result_hash,
        },
        "verifyta": {
            "version": verifyta_version or "unknown",
            "command": list(verifyta_command or []),
            "options": list(options or []),
        },
        "profile": profile,
        "result_status": result_json.get("status") if result_json else None,
    }


def export_run_artifacts(
    output_root: str | Path,
    *,
    source_text: str | None,
    contract_json: dict,
    model_xml: str,
    queries: str,
    profile: dict | None = None,
    result_json: dict | None = None,
    trace_text: str | None = None,
    verifyta_version: str | None = None,
    verifyta_command: list[str] | None = None,
    options: list[str] | None = None,
    force: bool = False,
) -> dict:
    metadata = build_run_metadata(
        source_text=source_text,
        contract_json=contract_json,
        model_xml=model_xml,
        queries=queries,
        profile=profile,
        result_json=result_json,
        verifyta_version=verifyta_version,
        verifyta_command=verifyta_command,
        options=options,
        trace_text=trace_text,
    )
    root = Path(output_root)
    artifact_dir = root / "artifacts" / metadata["run_id"]
    expected_files = set(REPORT_FILES) | {"contract.json", "model.xml", "queries.q", "run_metadata.json"}
    for name, present in (("source.tex", source_text is not None),
                          ("results.json", result_json is not None),
                          ("trace.txt", trace_text is not None),
                          ("trace_explanation.md", bool(trace_text))):
        if present:
            expected_files.add(name)
    # Never follow a substituted bundle/file symlink, including during repair.
    if artifact_dir.is_symlink() or any((artifact_dir / name).is_symlink()
                                      for name in expected_files | {CHECKSUM_FILE}):
        raise ValueError(f"Invalid PHY artifact cache at {artifact_dir}: symlink in bundle; use a new output root")
    cached = artifact_dir.exists() and not force
    if cached:
        cached_metadata = _read_cached_metadata(artifact_dir, metadata, expected_files)
        return {
            "artifact_dir": str(artifact_dir),
            "run_id": cached_metadata["run_id"],
            "cache_key": cached_metadata["cache_key"],
            "cache_hit": True,
            "files": [str(artifact_dir / name) for name in sorted(expected_files | {CHECKSUM_FILE})],
            "metadata": cached_metadata,
        }
    # Finish report generation before creating or changing any cached files.
    reports = generate_report_bundle(
        contract_json=contract_json,
        model_xml=model_xml,
        queries=queries,
        result_json=result_json,
        trace_text=trace_text,
        profile=profile or default_profile(),
    )
    artifact_dir.mkdir(parents=True, exist_ok=force)
    files: list[str] = []
    if source_text is not None:
        _write_text(artifact_dir / "source.tex", source_text, files)
    _write_json(artifact_dir / "contract.json", contract_json, files)
    _write_text(artifact_dir / "model.xml", model_xml, files)
    _write_text(artifact_dir / "queries.q", queries, files)
    if result_json is not None:
        _write_json(artifact_dir / "results.json", result_json, files)
    if trace_text is not None:
        _write_text(artifact_dir / "trace.txt", trace_text, files)
    for name in REPORT_FILES:
        _write_text(artifact_dir / name, reports["reports"][name], files)
    if "trace_explanation.md" in reports["reports"]:
        _write_text(artifact_dir / "trace_explanation.md", reports["reports"]["trace_explanation.md"], files)
    _write_json(artifact_dir / "run_metadata.json", metadata, files)
    # Written last: directory existence alone is never proof of a complete run.
    checksums = {Path(item).name: hashlib.sha256(Path(item).read_bytes()).hexdigest() for item in files}
    _write_json(artifact_dir / CHECKSUM_FILE, {"schema_version": 1, "files": checksums}, files)
    return {
        "artifact_dir": str(artifact_dir),
        "run_id": metadata["run_id"],
        "cache_key": metadata["cache_key"],
        "cache_hit": False,
        "files": files,
        "metadata": metadata,
    }


def _run_id(cache_key: str) -> str:
    return f"cache-{cache_key[:24]}"


def _sha_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _sha_json(value: Any) -> str:
    return _sha_text(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")))


def _write_text(path: Path, text: str, files: list[str]) -> None:
    path.write_bytes(text.encode("utf-8"))
    files.append(str(path))


def _write_json(path: Path, data: Any, files: list[str]) -> None:
    _write_text(path, json.dumps(data, ensure_ascii=False, indent=2), files)


def _read_cached_metadata(path: Path, expected: dict, expected_files: set[str]) -> dict:
    try:
        index = json.loads((path / CHECKSUM_FILE).read_text(encoding="utf-8"))
        if (not isinstance(index, dict) or type(index.get("schema_version")) is not int
                or index["schema_version"] != 1 or not isinstance(index.get("files"), dict)
                or set(index["files"]) != expected_files):
            raise ValueError("incomplete or invalid checksum index")
        for name in expected_files:
            actual = hashlib.sha256((path / name).read_bytes()).hexdigest()
            if actual != index["files"][name]:
                raise ValueError(f"checksum mismatch: {name}")
        metadata = json.loads((path / "run_metadata.json").read_text(encoding="utf-8"))
        if (not isinstance(metadata, dict) or not isinstance(metadata.get("created_at"), str)
                or not metadata["created_at"] or {**metadata, "created_at": expected["created_at"]} != expected):
            raise ValueError("stored metadata does not match requested inputs")
        return metadata
    except (OSError, UnicodeError, ValueError) as exc:
        raise ValueError(f"Invalid PHY artifact cache at {path}: {exc}; use force=True to rebuild") from exc
