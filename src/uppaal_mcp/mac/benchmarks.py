from __future__ import annotations

import xml.etree.ElementTree as ET

from .generator import generate_uppaal_model
from .validators import validate_generated_model

BENCHMARKS = [
    {"name": "nominal_mac", "category": "positive", "queries": ["A[] not deadlock", "E<> A_SCH.SelectMode"], "expected_static_ok": True, "expected_validation_error": None},
    {"name": "queue_critical", "category": "positive", "queries": ["A[] not ObsQueueCritical.Violation"], "expected_static_ok": True, "expected_validation_error": None},
    {"name": "buffer_overflow", "category": "positive", "queries": ["A[] not ObsBufferOverflow.Violation"], "expected_static_ok": True, "expected_validation_error": None},
    {"name": "resource_exhausted", "category": "positive", "queries": ["A[] (resourceClass == RES_EXHAUSTED imply !silent_accept)"], "expected_static_ok": True, "expected_validation_error": None},
    {"name": "stale_phy_kpi", "category": "positive", "queries": ["E<> A_SCH.ApplySchedule"], "expected_static_ok": True, "expected_validation_error": None},
    {"name": "sensing_conflict", "category": "positive", "queries": ["A[] not ObsSensingCritical.Violation"], "expected_static_ok": True, "expected_validation_error": None},
    {"name": "phy_ack_timeout", "category": "positive", "queries": ["A[] not ObsPhyAck.Violation"], "expected_static_ok": True, "expected_validation_error": None},
    {"name": "broken_report_channel_declared_as_chan", "category": "negative-static", "queries": ["A[] not deadlock"], "expected_static_ok": False, "expected_validation_error": "broadcast chan"},
    {"name": "broken_continuous_guard", "category": "negative-static", "queries": ["A[] not deadlock"], "expected_static_ok": False, "expected_validation_error": "queue_length_raw"},
    {"name": "broken_missing_a_env_mac", "category": "negative-static", "queries": ["A[] not deadlock"], "expected_static_ok": False, "expected_validation_error": "A_ENV_MAC"},
    {"name": "broken_silent_accept", "category": "negative-static", "queries": ["A[] not deadlock"], "expected_static_ok": False, "expected_validation_error": "silent_accept=true"},
    {"name": "broken_missing_ack_timeout", "category": "negative-static", "queries": ["A[] not deadlock"], "expected_static_ok": False, "expected_validation_error": "timeout path"},
]


def list_benchmarks() -> list[dict]:
    return [dict(item) for item in BENCHMARKS]


def generate_benchmark_model(name: str, profile: dict | None = None) -> dict:
    benchmark = next((item for item in BENCHMARKS if item["name"] == name), None)
    if benchmark is None:
        raise ValueError(f"Unknown MAC benchmark {name!r}.")
    generated = generate_uppaal_model(profile=profile, include_observers=True)
    model_xml = _mutate(generated.model_xml, name)
    queries = "\n".join(benchmark["queries"]) + "\n"
    validation = validate_generated_model(model_xml, queries).to_dict()
    return {
        **benchmark,
        "model_xml": model_xml,
        "queries": queries,
        "validation": validation,
    }


def validate_all_benchmarks(profile: dict | None = None) -> dict:
    results = []
    for item in BENCHMARKS:
        generated = generate_benchmark_model(item["name"], profile=profile)
        ok = generated["validation"]["ok"] == item["expected_static_ok"]
        expected = item["expected_validation_error"]
        if expected:
            ok = ok and any(expected in error for error in generated["validation"]["errors"])
        results.append({"name": item["name"], "ok": ok, "validation": generated["validation"], "expected_static_ok": item["expected_static_ok"]})
    return {"ok": all(item["ok"] for item in results), "count": len(results), "results": results}


def _mutate(model_xml: str, name: str) -> str:
    if name == "broken_report_channel_declared_as_chan":
        return model_xml.replace("broadcast chan phy_kpi_report, mac_report;", "chan phy_kpi_report, mac_report;", 1)
    if name == "broken_continuous_guard":
        return model_xml.replace("queueClass == Q_CRIT", "queue_length_raw > 100", 1)
    if name == "broken_missing_a_env_mac":
        root = ET.fromstring(model_xml)
        for template in list(root.findall("template")):
            if template.findtext("name") in {"A_ENV_MAC", "Template_A_ENV_MAC"}:
                root.remove(template)
        system = root.find("system")
        if system is not None and system.text:
            system.text = system.text.replace("A_ENV_MAC = Template_A_ENV_MAC();\n", "").replace(", A_ENV_MAC", "")
        ET.indent(root, space="  ")
        return ET.tostring(root, encoding="unicode")
    if name == "broken_silent_accept":
        return model_xml.replace("silent_accept = false", "silent_accept = true", 1)
    if name == "broken_missing_ack_timeout":
        return model_xml.replace("c_phy_ack == D_phy_ack", "c_phy_ack &lt; D_phy_ack", 1)
    return model_xml
