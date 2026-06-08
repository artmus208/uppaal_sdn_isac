from __future__ import annotations

from .generator import generate_uppaal_model

SCENARIOS = [
    {"name": "mac_nominal", "description": "nominal scheduling path reaches SelectMode", "expected_status": "satisfied", "query": "E<> A_SCH.SelectMode"},
    {"name": "mac_queue_critical", "description": "queue critical observer scenario", "expected_status": "satisfied", "query": "A[] not ObsQueueCritical.Violation"},
    {"name": "mac_phy_ack_timeout", "description": "PHY ack observer scenario", "expected_status": "satisfied", "query": "A[] not ObsPhyAck.Violation"},
]


def list_scenarios() -> list[dict]:
    return [dict(item) for item in SCENARIOS]


def generate_scenario_model(name: str, profile: dict | None = None) -> dict:
    scenario = next((item for item in SCENARIOS if item["name"] == name), None)
    if scenario is None:
        raise ValueError(f"Unknown MAC scenario {name!r}.")
    generated = generate_uppaal_model(profile=profile, include_observers=True)
    return {
        "name": name,
        "description": scenario["description"],
        "expected_status": scenario["expected_status"],
        "model_xml": generated.model_xml,
        "queries": scenario["query"] + "\n",
        "timeout_sec": 10.0,
    }

