from __future__ import annotations


def explain_counterexample(result_json: dict, trace_text: str | None = None, contract_json: dict | None = None) -> dict:
    status = result_json.get("status", "unknown")
    failed = [item for item in result_json.get("query_results", []) if item.get("status") != "satisfied"]
    if status in {"satisfied", "validated"} and not failed:
        return {"status": status, "summary": "All executed MAC properties were satisfied or statically validated.", "failed_queries": [], "counterexample_classification": None}
    reasons = []
    formulas = "\n".join(item.get("formula", "") for item in failed)
    text = (trace_text or "") + "\n" + formulas
    lower = text.lower()
    classification = "unknown"
    if "obsphyack" in lower or "phy_ack" in lower or "waitphyack" in lower:
        reasons.append("PHY command was not acknowledged before D_phy_ack or timeout path is malformed.")
        classification = "possible_mac_timing_violation"
    if "obsqueuecritical" in lower or "q_crit" in lower or "queuecritical" in lower:
        reasons.append("Critical queue did not drain, reject or report before D_queue_crit.")
        classification = "possible_mac_timing_violation"
    if "obsbufferoverflow" in lower or "b_overflow" in lower:
        reasons.append("Buffer overflow did not produce bounded MAC report.")
        classification = "possible_mac_timing_violation"
    if "silent_accept" in lower or "res_exhausted" in lower:
        reasons.append("Resource exhaustion may have been silently accepted.")
        classification = "modeling_error" if status == "static_error" else "environment_or_policy_violation"
    if "deadlock" in lower:
        reasons.append("Closed MAC composition deadlocked; check handshake pairing and ENV_MAC assumptions.")
        classification = "modeling_error"
    return {"status": status, "summary": "At least one MAC property failed or was not classified as satisfied.", "failed_queries": failed, "reasons": reasons, "counterexample_classification": classification, "artifact_dir": result_json.get("artifact_dir")}

