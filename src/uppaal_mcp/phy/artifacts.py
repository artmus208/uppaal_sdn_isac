from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .alpha import default_profile
from .reports import generate_report_bundle


GENERATOR_VERSION = "phy-generator-v0.5"


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
            "source_hash": source_hash,
            "profile_hash": profile_hash,
            "generator_version": GENERATOR_VERSION,
            "verifyta_version": verifyta_version or "unknown",
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
    )
    root = Path(output_root)
    artifact_dir = root / "artifacts" / metadata["run_id"]
    cached = artifact_dir.exists() and not force
    if cached:
        cached_metadata = _read_cached_metadata(artifact_dir) or metadata
        return {
            "artifact_dir": str(artifact_dir),
            "run_id": cached_metadata["run_id"],
            "cache_key": cached_metadata["cache_key"],
            "cache_hit": True,
            "files": _existing_files(artifact_dir),
            "metadata": cached_metadata,
        }
    artifact_dir.mkdir(parents=True, exist_ok=True)
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
    reports = generate_report_bundle(
        contract_json=contract_json,
        model_xml=model_xml,
        queries=queries,
        result_json=result_json,
        trace_text=trace_text,
        profile=profile or default_profile(),
    )
    _write_text(artifact_dir / "report.md", reports["reports"]["report.md"], files)
    _write_text(artifact_dir / "traceability_matrix.md", reports["reports"]["traceability_matrix.md"], files)
    _write_text(artifact_dir / "model_summary.md", reports["reports"]["model_summary.md"], files)
    if "trace_explanation.md" in reports["reports"]:
        _write_text(artifact_dir / "trace_explanation.md", reports["reports"]["trace_explanation.md"], files)
    _write_json(artifact_dir / "run_metadata.json", metadata, files)
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
    path.write_text(text, encoding="utf-8")
    files.append(str(path))


def _write_json(path: Path, data: Any, files: list[str]) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    files.append(str(path))


def _existing_files(path: Path) -> list[str]:
    return [str(item) for item in sorted(path.iterdir()) if item.is_file()]


def _read_cached_metadata(path: Path) -> dict | None:
    metadata_path = path / "run_metadata.json"
    if not metadata_path.exists():
        return None
    try:
        return json.loads(metadata_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
