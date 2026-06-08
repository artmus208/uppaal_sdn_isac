from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field

from .defaults import build_default_contract
from .ir import MacContractModel

CONTINUOUS_GUARD_TOKENS = [
    "queue_length_raw",
    "buffer_occupancy_raw",
    "packet_loss_rate",
    "scheduling_delay_sample",
    "radio_resource_utilization",
    "harq_nack_count",
    "harq_nack_rate",
    "throughput_avg",
    "mean_delay",
]


@dataclass
class AlphaReport:
    ok: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    details: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


def default_profile(name: str = "default") -> dict:
    profiles = {
        "default": {"D_collect": 2, "D_sched": 5, "D_phy_ack": 3, "D_queue_crit": 10, "D_buf_report": 4, "D_mac_report": 5, "D_phy_report": 10},
        "conservative_safety": {"D_collect": 1, "D_sched": 4, "D_phy_ack": 2, "D_queue_crit": 8, "D_buf_report": 3, "D_mac_report": 4, "D_phy_report": 8},
        "stress": {"D_collect": 1, "D_sched": 2, "D_phy_ack": 1, "D_queue_crit": 4, "D_buf_report": 2, "D_mac_report": 2, "D_phy_report": 4},
    }
    if name not in profiles:
        raise ValueError("Unsupported MAC profile. Use default, conservative_safety, or stress.")
    return {
        "name": name,
        "source": "built-in",
        "boundary_policy": "worse_class",
        "parameter_synthesis": False,
        "deadlines": profiles[name],
    }


def list_classes(contract: MacContractModel | None = None) -> dict[str, list[str]]:
    model = contract or build_default_contract()
    return {item.name: list(item.values) for item in model.classes}


def validate_threshold_policy(profile_json: dict | None = None) -> AlphaReport:
    profile = profile_json or default_profile()
    errors: list[str] = []
    deadlines = profile.get("deadlines", {})
    for name in ("D_collect", "D_sched", "D_phy_ack", "D_queue_crit", "D_buf_report", "D_mac_report", "D_phy_report"):
        value = deadlines.get(name)
        if not isinstance(value, int) or value <= 0:
            errors.append(f"{name} must be a positive integer deadline.")
    if profile.get("boundary_policy") != "worse_class":
        errors.append("boundary_policy must be worse_class for MAC safety-critical classes.")
    if profile.get("parameter_synthesis"):
        errors.append("parameter_synthesis is not supported in MAC base layer.")
    return AlphaReport(ok=not errors, errors=errors, details={"profile": profile})


def check_no_continuous_guards(model_text: str) -> AlphaReport:
    errors = []
    for token in CONTINUOUS_GUARD_TOKENS:
        if re.search(rf"\b{re.escape(token)}\b", model_text):
            errors.append(f"Continuous/counter MAC value {token} must not appear in generated UPPAAL guards.")
    return AlphaReport(ok=not errors, errors=errors, details={"forbidden_tokens": CONTINUOUS_GUARD_TOKENS})

