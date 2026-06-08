from __future__ import annotations

from .generator import generate_uppaal_model

SCENARIOS = [
    {"name": "sdn_nominal", "description": "Nominal SDN/RIC service request reaches policy evaluation.", "expected_status": "satisfied", "query": "E<> A_POLICY.Evaluate"},
    {"name": "sdn_rule_miss", "description": "Rule miss has bounded explicit outcome observer.", "expected_status": "satisfied", "query": "A[] not ObsRuleMiss.Violation"},
    {"name": "sdn_recovery", "description": "Link/node failure recovery observer stays safe.", "expected_status": "satisfied", "query": "A[] not ObsRecovery.Violation"},
    {"name": "sdn_admission", "description": "Service admission observer stays safe.", "expected_status": "satisfied", "query": "A[] not ObsAdmission.Violation"},
    {"name": "sdn_stale_telemetry", "description": "Stale telemetry never enables optimistic reconfiguration.", "expected_status": "satisfied", "query": "A[] not ObsStaleTelemetry.Violation"},
    {"name": "sdn_command_timeout", "description": "Command timeout path is reachable.", "expected_status": "satisfied", "query": "E<> A_SDN_AGG.CommandTimeout"},
]


def list_scenarios() -> list[dict]:
    return [dict(item) for item in SCENARIOS]


def generate_scenario_model(name: str, profile: dict | None = None) -> dict:
    scenario = next((item for item in SCENARIOS if item["name"] == name), None)
    if scenario is None:
        raise ValueError(f"Unknown SDN scenario {name!r}.")
    generated = generate_uppaal_model(profile=profile, include_observers=True)
    return {
        "name": name,
        "description": scenario["description"],
        "expected_status": scenario["expected_status"],
        "model_xml": generated.model_xml,
        "queries": scenario["query"] + "\n",
        "timeout_sec": 10.0,
    }
