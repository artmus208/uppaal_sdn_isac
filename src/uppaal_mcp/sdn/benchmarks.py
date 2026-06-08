from __future__ import annotations

import xml.etree.ElementTree as ET

from .generator import generate_uppaal_model
from .validators import validate_generated_model

BENCHMARKS = [
    {"name": "nominal_sdn", "category": "positive", "queries": ["A[] not deadlock", "E<> A_POLICY.Evaluate"], "expected_static_ok": True, "expected_validation_error": None},
    {"name": "rule_miss_install", "category": "positive", "queries": ["E<> A_RULE.RuleInstalled"], "expected_static_ok": True, "expected_validation_error": None},
    {"name": "rule_miss_drop", "category": "positive", "queries": ["E<> A_RULE.RuleDropReason"], "expected_static_ok": True, "expected_validation_error": None},
    {"name": "rule_timeout", "category": "positive", "queries": ["E<> A_RULE.RuleTimeout"], "expected_static_ok": True, "expected_validation_error": None},
    {"name": "stale_telemetry_constrained", "category": "positive", "queries": ["A[] (telemetryClass == TEL_STALE imply !optimistic_reconfig)"], "expected_static_ok": True, "expected_validation_error": None},
    {"name": "sensing_degradation_boost", "category": "positive", "queries": ["E<> A_POLICY.SensingBoostMode"], "expected_static_ok": True, "expected_validation_error": None},
    {"name": "sensing_degradation_reject", "category": "positive", "queries": ["E<> A_POLICY.RejectByPolicy"], "expected_static_ok": True, "expected_validation_error": None},
    {"name": "service_admission_accept", "category": "positive", "queries": ["E<> A_POLICY.NormalMode"], "expected_static_ok": True, "expected_validation_error": None},
    {"name": "service_admission_degraded", "category": "positive", "queries": ["E<> A_POLICY.ConstrainedMode"], "expected_static_ok": True, "expected_validation_error": None},
    {"name": "service_admission_reject", "category": "positive", "queries": ["E<> A_POLICY.RejectByPolicy"], "expected_static_ok": True, "expected_validation_error": None},
    {"name": "link_failure_standby", "category": "positive", "queries": ["E<> A_REC.StandbySwitch"], "expected_static_ok": True, "expected_validation_error": None},
    {"name": "node_failure_reembedding", "category": "positive", "queries": ["E<> A_REC.ReactiveReembedding"], "expected_static_ok": True, "expected_validation_error": None},
    {"name": "recovery_rollback", "category": "positive", "queries": ["E<> A_REC.Rollback"], "expected_static_ok": True, "expected_validation_error": None},
    {"name": "recovery_failed", "category": "positive", "queries": ["E<> A_REC.RecoveryFailed"], "expected_static_ok": True, "expected_validation_error": None},
    {"name": "command_ack_timeout", "category": "positive", "queries": ["E<> A_SDN_AGG.CommandTimeout"], "expected_static_ok": True, "expected_validation_error": None},
    {"name": "broken_report_channel_declared_as_chan", "category": "negative-static", "queries": ["A[] not deadlock"], "expected_static_ok": False, "expected_validation_error": "broadcast chan"},
    {"name": "broken_raw_metric_guard", "category": "negative-static", "queries": ["A[] not deadlock"], "expected_static_ok": False, "expected_validation_error": "raw_delay"},
    {"name": "broken_missing_a_env_sdn", "category": "negative-static", "queries": ["A[] not deadlock"], "expected_static_ok": False, "expected_validation_error": "A_ENV_SDN"},
    {"name": "broken_stale_optimistic_reconfig", "category": "negative-static", "queries": ["A[] not deadlock"], "expected_static_ok": False, "expected_validation_error": "stale"},
    {"name": "broken_missing_rule_miss_outcome", "category": "negative-static", "queries": ["A[] not deadlock"], "expected_static_ok": False, "expected_validation_error": "rule miss outcome"},
    {"name": "broken_missing_admission_outcome", "category": "negative-static", "queries": ["A[] not deadlock"], "expected_static_ok": False, "expected_validation_error": "service admission outcome"},
    {"name": "broken_missing_ack_timeout", "category": "negative-static", "queries": ["A[] not deadlock"], "expected_static_ok": False, "expected_validation_error": "command timeout path"},
    {"name": "broken_incomplete_policy_table", "category": "negative-static", "queries": ["A[] not deadlock"], "expected_static_ok": False, "expected_validation_error": "gPolCommPrio"},
    {"name": "broken_sec_forced_into_base", "category": "negative-static", "queries": ["A[] not deadlock"], "expected_static_ok": False, "expected_validation_error": "A_SEC"},
]


def list_benchmarks() -> list[dict]:
    return [dict(item) for item in BENCHMARKS]


def generate_benchmark_model(name: str, profile: dict | None = None) -> dict:
    benchmark = next((item for item in BENCHMARKS if item["name"] == name), None)
    if benchmark is None:
        raise ValueError(f"Unknown SDN benchmark {name!r}.")
    generated = generate_uppaal_model(profile=profile, include_observers=True)
    model_xml = _mutate(generated.model_xml, name)
    queries = "\n".join(benchmark["queries"]) + "\n"
    validation = validate_generated_model(model_xml, queries).to_dict()
    return {**benchmark, "model_xml": model_xml, "queries": queries, "validation": validation}


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
        return model_xml.replace("broadcast chan mac_report, phy_kpi_report, service_request;", "chan mac_report, phy_kpi_report, service_request;", 1)
    if name == "broken_raw_metric_guard":
        return _replace_first_label(model_xml, "telemetryClass == TEL_STALE", "raw_delay > 5")
    if name == "broken_missing_a_env_sdn":
        root = ET.fromstring(model_xml)
        for template in list(root.findall("template")):
            if template.findtext("name") in {"A_ENV_SDN", "Template_A_ENV_SDN"}:
                root.remove(template)
        system = root.find("system")
        if system is not None and system.text:
            system.text = system.text.replace("A_ENV_SDN = Template_A_ENV_SDN();\n", "").replace(", A_ENV_SDN", "")
        ET.indent(root, space="  ")
        return ET.tostring(root, encoding="unicode")
    if name == "broken_stale_optimistic_reconfig":
        return _replace_first_label(model_xml, "telemetryClass = TEL_STALE, optimistic_reconfig = false", "telemetryClass = TEL_STALE, optimistic_reconfig = true")
    if name == "broken_missing_rule_miss_outcome":
        return _replace_first_label(model_xml, "drop_report!", "drop_report_removed!")
    if name == "broken_missing_admission_outcome":
        return _replace_first_label(model_xml, "service_reject!", "service_reject_removed!")
    if name == "broken_missing_ack_timeout":
        return _replace_first_label(model_xml, "c_ctrl_ack == D_ctrl_ack", "c_ctrl_ack < D_ctrl_ack")
    if name == "broken_incomplete_policy_table":
        return model_xml.replace("gPolCommPrio", "removed_gPolCommPrio")
    if name == "broken_sec_forced_into_base":
        return model_xml.replace("system A_MON", "A_SEC = Template_A_SEC();\nsystem A_SEC, A_MON", 1)
    return model_xml


def _replace_first_label(model_xml: str, old: str, new: str) -> str:
    root = ET.fromstring(model_xml)
    for label in root.findall(".//label"):
        if label.text and old in label.text:
            label.text = label.text.replace(old, new, 1)
            ET.indent(root, space="  ")
            return ET.tostring(root, encoding="unicode")
    return model_xml
