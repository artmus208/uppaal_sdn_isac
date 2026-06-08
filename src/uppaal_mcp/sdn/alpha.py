from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field

from .defaults import build_default_contract
from .ir import SdnContractModel

CONTINUOUS_GUARD_TOKENS = [
    "queue_length_raw",
    "raw_queue_length",
    "raw_delay",
    "delay_sample",
    "packet_rate",
    "packet_loss_rate",
    "throughput_avg",
    "mean_delay",
    "SINR",
    "SINR_c",
    "SINR_s",
    "CRB",
    "CRB_R",
    "CRB_v",
    "CRB_theta",
    "Pd",
    "Rfa",
    "recovery_probability",
    "expected_recovery_cost",
    "optimization_score",
    "Pi_SDN",
]

REQUIRED_DEADLINES = (
    "D_mon",
    "D_decision",
    "D_rule_install",
    "D_rule_ack",
    "D_ctrl_ack",
    "D_recovery",
    "D_rollback",
    "D_admission",
    "D_sec_ack",
)


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
        "default": {
            "D_mon": 5,
            "D_decision": 5,
            "D_rule_install": 8,
            "D_rule_ack": 5,
            "D_ctrl_ack": 5,
            "D_recovery": 20,
            "D_rollback": 10,
            "D_admission": 15,
            "D_sec_ack": 10,
        },
        "conservative_safety": {
            "D_mon": 4,
            "D_decision": 4,
            "D_rule_install": 6,
            "D_rule_ack": 4,
            "D_ctrl_ack": 4,
            "D_recovery": 16,
            "D_rollback": 8,
            "D_admission": 12,
            "D_sec_ack": 8,
        },
        "stress": {
            "D_mon": 2,
            "D_decision": 2,
            "D_rule_install": 4,
            "D_rule_ack": 2,
            "D_ctrl_ack": 2,
            "D_recovery": 8,
            "D_rollback": 4,
            "D_admission": 6,
            "D_sec_ack": 4,
        },
    }
    if name not in profiles:
        raise ValueError("Unsupported SDN profile. Use default, conservative_safety, or stress.")
    return {
        "name": name,
        "source": "built-in",
        "boundary_policy": "worse_class",
        "stale_policy": "constrained_or_reject",
        "parameter_synthesis": False,
        "deadlines": profiles[name],
    }


def list_classes(contract: SdnContractModel | None = None) -> dict[str, list[str]]:
    model = contract or build_default_contract()
    return {item.name: list(item.values) for item in model.classes}


def validate_threshold_policy(profile_json: dict | None = None) -> AlphaReport:
    profile = profile_json or default_profile()
    errors: list[str] = []
    deadlines = profile.get("deadlines", {})
    for name in REQUIRED_DEADLINES:
        value = deadlines.get(name)
        if not isinstance(value, int) or value <= 0:
            errors.append(f"{name} must be a positive integer deadline.")
    if deadlines.get("D_rule_ack", 1) > deadlines.get("D_rule_install", 0):
        errors.append("D_rule_ack must not exceed D_rule_install.")
    if profile.get("boundary_policy") != "worse_class":
        errors.append("boundary_policy must be worse_class for SDN safety-critical classes.")
    if profile.get("stale_policy") != "constrained_or_reject":
        errors.append("stale_policy must be constrained_or_reject.")
    if profile.get("parameter_synthesis"):
        errors.append("parameter_synthesis is not supported in SDN base layer.")
    return AlphaReport(ok=not errors, errors=errors, details={"profile": profile})


def check_no_continuous_guards(model_text: str) -> AlphaReport:
    guard_text = _guards_only(model_text)
    errors = []
    for token in CONTINUOUS_GUARD_TOKENS:
        if re.search(rf"\b{re.escape(token)}\b", guard_text):
            errors.append(f"Raw/continuous SDN value {token} must not appear in UPPAAL guards.")
    return AlphaReport(ok=not errors, errors=errors, details={"forbidden_tokens": CONTINUOUS_GUARD_TOKENS})


def _guards_only(model_text: str) -> str:
    labels = re.findall(r'<label[^>]*kind="guard"[^>]*>(.*?)</label>', model_text, flags=re.DOTALL)
    if labels:
        return "\n".join(labels)
    return model_text
