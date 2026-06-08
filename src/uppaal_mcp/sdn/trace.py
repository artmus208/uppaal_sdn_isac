from __future__ import annotations


def explain_counterexample(result_json: dict, trace_text: str | None = None, contract_json: dict | None = None) -> dict:
    status = result_json.get("status", "unknown")
    failed = [item for item in result_json.get("query_results", []) if item.get("status") != "satisfied"]
    if status in {"satisfied", "validated"} and not failed:
        return {
            "status": status,
            "summary": "All executed SDN/RIC properties were satisfied or statically validated.",
            "failed_queries": [],
            "counterexample_classification": None,
        }
    formulas = "\n".join(item.get("formula", "") for item in failed)
    text = (trace_text or "") + "\n" + formulas + "\n" + " ".join(result_json.get("validation", {}).get("errors", []))
    lower = text.lower()
    reasons = []
    classification = "unknown"
    if "optimistic_reconfig" in lower or "obsstaletelemetry" in lower or "stale" in lower:
        reasons.append("Stale/missing telemetry may have allowed optimistic reconfiguration.")
        classification = "policy_semantics_violation"
    if "obsrulemiss" in lower or "rule_miss" in lower or "ruletimeout" in lower:
        reasons.append("Rule miss did not reach flow install, drop reason or timeout report by D_rule_install.")
        classification = "possible_sdn_timing_violation"
    if "obsadmission" in lower or "service_request" in lower:
        reasons.append("Service admission did not reach accept, degraded or reject outcome by D_admission.")
        classification = "possible_sdn_timing_violation"
    if "obsrecovery" in lower or "recoveryfailed" in lower or "rollback" in lower:
        reasons.append("Recovery path did not reach stable configuration or explicit failure in time.")
        classification = "possible_sdn_timing_violation"
    if "obscommandack" in lower or "commandtimeout" in lower or "ack" in lower:
        reasons.append("Lower-plane command acknowledgement path is late or malformed.")
        classification = "blocked_handshake_or_timeout"
    if "broadcast" in lower or "handshake" in lower or "chan" in lower:
        reasons.append("Channel declaration or sync direction is inconsistent with the SDN/RIC contract.")
        classification = "modeling_error"
    if "deadlock" in lower:
        reasons.append("Closed SDN/RIC composition deadlocked; check handshake pairing and A_ENV_SDN assumptions.")
        classification = "modeling_error"
    if not reasons:
        reasons.append("No SDN/RIC-specific root cause matched the result.")
    return {
        "status": status,
        "summary": "At least one SDN/RIC property failed or was not classified as satisfied.",
        "failed_queries": failed,
        "reasons": reasons,
        "counterexample_classification": classification,
        "artifact_dir": result_json.get("artifact_dir"),
    }
