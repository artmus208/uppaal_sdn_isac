from __future__ import annotations

import json
from pathlib import Path

from .defaults import build_default_contract
from .generator import generate_queries
from .ir import SdnContractModel
from .validators import validate_generated_model


def generate_property_pack(contract: SdnContractModel | None = None, *, model_xml: str | None = None, include_observers: bool = True, debug_counters: bool = True, include_negative: bool = False) -> dict:
    model = contract or build_default_contract()
    queries = generate_queries(model, include_observers=include_observers, debug_counters=debug_counters)
    items = [
        {
            "name": prop.name,
            "query": prop.query,
            "category": prop.category,
            "interpretation": prop.interpretation,
            "source": prop.provenance.section if prop.provenance else "unknown",
        }
        for prop in model.properties
        if include_observers or not prop.name.startswith("Obs")
    ]
    if debug_counters:
        items.append({"name": "policy_totality", "query": "A[] policy_enabled_count >= 1", "category": "debug", "interpretation": "policy/fallback totality", "source": "generated"})
    pack = {
        "queries": queries,
        "queries_json": items,
        "summary": {
            "property_count": len(items),
            "include_observers": include_observers,
            "debug_counters": debug_counters,
        },
        "static_checks": {
            "channel_semantics": "reports/service outcomes broadcast; commands/acks/failure paths handshake",
            "no_continuous_guards": "raw SDN/PHY/MAC samples, probabilities and optimization scores forbidden in guards",
            "single_sync": "one sync label per edge",
            "stale_telemetry": "TEL_STALE/TEL_MISSING imply !optimistic_reconfig",
            "explicit_outcomes": "rule miss, admission and recovery expose bounded explicit outcomes",
        },
    }
    if model_xml is not None:
        pack["model_validation"] = validate_generated_model(model_xml, queries).to_dict()
    if include_negative:
        pack["negative_property_pack"] = {
            "mutations": [
                "report/outcome channel declared as chan",
                "raw continuous guard",
                "missing A_ENV_SDN",
                "stale optimistic reconfiguration",
                "missing rule miss outcome",
                "missing admission outcome",
                "missing ack timeout path",
            ]
        }
    return pack


def export_property_pack(output_dir: str | Path, contract: SdnContractModel | None = None, *, model_xml: str | None = None, include_observers: bool = True, debug_counters: bool = True, include_negative: bool = False) -> dict:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    pack = generate_property_pack(contract, model_xml=model_xml, include_observers=include_observers, debug_counters=debug_counters, include_negative=include_negative)
    files = []
    (output / "queries.q").write_text(pack["queries"], encoding="utf-8")
    files.append(str(output / "queries.q"))
    (output / "queries.json").write_text(json.dumps(pack["queries_json"], ensure_ascii=False, indent=2), encoding="utf-8")
    files.append(str(output / "queries.json"))
    (output / "property_pack.json").write_text(json.dumps(pack, ensure_ascii=False, indent=2), encoding="utf-8")
    files.append(str(output / "property_pack.json"))
    return {"output_dir": str(output), "files": files, "summary": pack["summary"]}
