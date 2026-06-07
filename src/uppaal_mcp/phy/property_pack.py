from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .benchmarks import list_benchmarks
from .defaults import build_default_contract
from .ir import PhyContractModel, PropertySpec
from .validators import validate_generated_model


@dataclass(frozen=True)
class QueryMetadata:
    index: int
    name: str
    query: str
    category: str
    interpretation: str
    source: str | None
    section: str | None
    line: int | None

    def to_dict(self) -> dict:
        return asdict(self)


def generate_property_pack(
    contract: PhyContractModel | None = None,
    *,
    model_xml: str | None = None,
    profile: dict | None = None,
    include_observers: bool = True,
    debug_counters: bool = True,
    include_negative: bool = False,
) -> dict:
    model = contract or build_default_contract()
    properties = _included_properties(
        model,
        include_observers=include_observers,
        debug_counters=debug_counters,
    )
    metadata = [_metadata(index, item) for index, item in enumerate(properties, start=1)]
    queries = "\n".join(item.query for item in properties) + "\n"
    pack = {
        "queries": queries,
        "queries_json": [item.to_dict() for item in metadata],
        "properties": [asdict(item) for item in properties],
        "summary": {
            "query_count": len(properties),
            "categories": _category_counts(properties),
            "include_observers": include_observers,
            "debug_counters": debug_counters,
            "profile": profile,
        },
        "static_checks": [
            {
                "name": "channel_semantics",
                "type": "static",
                "reason": "broadcast/handshake semantics are syntactic/model-structure checks, not UPPAAL formulas",
            },
            {
                "name": "single_sync_per_transition",
                "type": "static",
                "reason": "UPPAAL XML transition labels are checked structurally by validators",
            },
            {
                "name": "no_continuous_guards",
                "type": "static",
                "reason": "continuous PHY symbols must not appear in generated automata guards",
            },
        ],
    }
    if model_xml is not None:
        pack["model_validation"] = validate_generated_model(
            model_xml,
            queries,
            require_observers=include_observers,
        ).to_dict()
    if include_negative:
        pack["negative_property_pack"] = generate_negative_property_pack()
    return pack


def generate_negative_property_pack() -> dict:
    benchmarks = [
        item
        for item in list_benchmarks()
        if item["category"] == "negative-static"
    ]
    return {
        "count": len(benchmarks),
        "items": [
            {
                "name": item["name"],
                "description": item["description"],
                "queries": item["queries"],
                "expected_static_ok": item["expected_static_ok"],
                "expected_validation_error": item["expected_validation_error"],
            }
            for item in benchmarks
        ],
    }


def export_property_pack(
    output_dir: str | Path,
    contract: PhyContractModel | None = None,
    *,
    model_xml: str | None = None,
    profile: dict | None = None,
    include_observers: bool = True,
    debug_counters: bool = True,
    include_negative: bool = False,
) -> dict:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    pack = generate_property_pack(
        contract,
        model_xml=model_xml,
        profile=profile,
        include_observers=include_observers,
        debug_counters=debug_counters,
        include_negative=include_negative,
    )
    files: list[str] = []
    _write_text(output / "queries.q", pack["queries"], files)
    _write_json(output / "queries.json", pack["queries_json"], files)
    _write_json(output / "property_pack.json", _without_large_text(pack), files)
    if include_negative:
        _write_json(output / "negative_property_pack.json", pack["negative_property_pack"], files)
    return {
        "output_dir": str(output),
        "files": files,
        "summary": pack["summary"],
    }


def _included_properties(
    model: PhyContractModel,
    *,
    include_observers: bool,
    debug_counters: bool,
) -> list[PropertySpec]:
    properties: list[PropertySpec] = []
    for item in model.properties:
        if item.name.startswith("Obs") and not include_observers:
            continue
        if item.name in {"ch_determinism", "sq_determinism"} and not debug_counters:
            continue
        properties.append(item)
    return properties


def _metadata(index: int, item: PropertySpec) -> QueryMetadata:
    provenance = item.provenance
    return QueryMetadata(
        index=index,
        name=item.name,
        query=item.query,
        category=item.category,
        interpretation=item.interpretation,
        source=provenance.source if provenance else None,
        section=provenance.section if provenance else None,
        line=provenance.line if provenance else None,
    )


def _category_counts(properties: list[PropertySpec]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in properties:
        counts[item.category] = counts.get(item.category, 0) + 1
    return counts


def _without_large_text(pack: dict) -> dict:
    return {key: value for key, value in pack.items() if key != "queries"}


def _write_text(path: Path, text: str, files: list[str]) -> None:
    path.write_text(text, encoding="utf-8")
    files.append(str(path))


def _write_json(path: Path, data: Any, files: list[str]) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    files.append(str(path))
