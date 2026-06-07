from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field

from .defaults import build_default_contract
from .ir import PhyContractModel

CONTINUOUS_GUARD_TOKENS = {
    "SINR_c",
    "SINR_s",
    "Pd",
    "Rfa",
    "CRB_R",
    "CRB_v",
    "CRB_theta",
    "Acc_r",
    "Acc_v",
    "p_mis",
    "Omega_BM",
    "Pi_PHY",
    "C_s",
}

SAFETY_CRITICAL_CLASSES = {
    "SINRClass": {"OUTAGE", "LOW"},
    "PowerClass": {"LOW", "ABSENT"},
    "PdClass": {"LOW", "FAILED"},
    "RfaClass": {"HIGH", "CRITICAL"},
    "AccClass": {"LIMITED", "FAILED"},
    "CRBClass": {"LOOSE", "UNUSABLE"},
    "AoSClass": {"STALE", "EXPIRED"},
    "BeamErrorClass": {"UNSTABLE", "CRITICAL"},
    "BlockageClass": {"SUSPECTED", "CONFIRMED"},
    "BeamClass": {"MISALIGNED", "FAILED"},
    "SensingState": {"ProbabilityLimited", "FalseAlarmLimited", "AccuracyLimited", "FreshnessLimited", "SensingFailure"},
}


@dataclass
class AlphaCheckReport:
    ok: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    classes: dict[str, list[str]] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


def list_classes(contract: PhyContractModel | None = None) -> dict[str, list[str]]:
    model = contract or build_default_contract()
    return {item.name: list(item.values) for item in model.classes}


def generate_uppaal_declarations(contract: PhyContractModel | None = None) -> str:
    model = contract or build_default_contract()
    lines: list[str] = []
    for item in model.classes:
        upper = item.name.upper()
        max_value = len(item.values) - 1
        lines.append(f"typedef int[0,{max_value}] {item.name}T;")
        for index, value in enumerate(item.values):
            lines.append(f"const int {upper}_{_const_name(value)} = {index};")
        default_value = _default_value(item.name, item.values)
        lines.append(f"{item.name}T {item.name} = {upper}_{_const_name(default_value)};")
        lines.append("")
    return "\n".join(lines)


def check_no_continuous_guards(model_text: str) -> AlphaCheckReport:
    errors: list[str] = []
    for token in sorted(CONTINUOUS_GUARD_TOKENS):
        if re.search(rf"\b{re.escape(token)}\b", model_text):
            errors.append(f"Continuous PHY value {token} appears in generated automata text.")
    return AlphaCheckReport(ok=not errors, errors=errors, classes=list_classes())


def validate_threshold_policy(profile: dict | None = None) -> AlphaCheckReport:
    profile = profile or default_profile()
    errors: list[str] = []
    warnings: list[str] = []
    boundary_report = check_boundary_policy(profile)
    errors.extend(boundary_report.errors)
    warnings.extend(boundary_report.warnings)
    if profile.get("parameter_synthesis"):
        errors.append("parameter_synthesis is out of scope for this base TA MCP layer.")
    for name in ("D_meas", "D_sig", "D_sense", "D_report", "D_BM"):
        value = profile.get("deadlines", {}).get(name)
        if not isinstance(value, int) or value <= 0:
            errors.append(f"Deadline {name} must be a positive integer.")
    if not profile.get("source"):
        warnings.append("Profile has no source metadata.")
    return AlphaCheckReport(ok=not errors, errors=errors, warnings=warnings, classes=list_classes())


def check_boundary_policy(profile: dict | None = None) -> AlphaCheckReport:
    profile = profile or default_profile()
    errors: list[str] = []
    warnings: list[str] = []
    if profile.get("boundary_policy") != "worse_class":
        errors.append("boundary_policy must be 'worse_class'.")
    overrides = profile.get("boundary_policy_overrides") or {}
    for name, policy in sorted(overrides.items()):
        if name in SAFETY_CRITICAL_CLASSES and policy != "worse_class":
            errors.append(f"Safety-critical class {name} must use worse_class boundary policy.")
    classes = list_classes()
    for name, bad_values in sorted(SAFETY_CRITICAL_CLASSES.items()):
        values = set(classes.get(name, []))
        missing = sorted(bad_values - values)
        if missing:
            errors.append(f"Safety-critical class {name} is missing conservative value(s): {', '.join(missing)}.")
    if not profile.get("boundary_policy_evidence"):
        warnings.append("Profile has no boundary_policy_evidence metadata.")
    return AlphaCheckReport(ok=not errors, errors=errors, warnings=warnings, classes=classes)


def default_profile(name: str = "default") -> dict:
    if name == "conservative_safety":
        deadlines = {"D_meas": 4, "D_sig": 4, "D_sense": 4, "D_report": 4, "D_BM": 4}
    elif name == "stress":
        deadlines = {"D_meas": 2, "D_sig": 2, "D_sense": 2, "D_report": 2, "D_BM": 2}
    else:
        deadlines = {"D_meas": 5, "D_sig": 5, "D_sense": 5, "D_report": 5, "D_BM": 5}
    return {
        "name": name,
        "source": "built-in",
        "boundary_policy": "worse_class",
        "parameter_synthesis": False,
        "deadlines": deadlines,
    }


def classify_sample(meas: dict, cfg: dict | None = None, profile: dict | None = None) -> dict:
    """Small deterministic classifier for examples and MCP smoke tests.

    This is not a radio estimator. It only demonstrates the alpha_PHY contract:
    continuous values are converted outside UPPAAL into finite classes.
    """
    profile = profile or default_profile()
    cfg = cfg or {}
    sinr = float(meas.get("SINR_c", 20.0))
    pd = float(meas.get("Pd", 0.99))
    rfa = float(meas.get("Rfa", 0.01))
    aos = float(meas.get("AoS_CTRL", 0.0))
    blockage = bool(meas.get("blockage", False))
    result = {
        "profile": profile["name"],
        "SINRClass": "OUTAGE" if sinr < 0 else "LOW" if sinr < 10 else "OK" if sinr < 25 else "HIGH",
        "PdClass": "FAILED" if pd < 0.5 else "LOW" if pd < 0.9 else "OK",
        "RfaClass": "CRITICAL" if rfa > 0.2 else "HIGH" if rfa > 0.05 else "OK",
        "AoSClass": "EXPIRED" if aos > float(cfg.get("AoS_max", 10)) else "FRESH",
        "BlockageClass": "CONFIRMED" if blockage else "NONE",
        "boundary_policy": profile["boundary_policy"],
    }
    return result


def _const_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]", "_", value).upper()


def _default_value(class_name: str, values: list[str]) -> str:
    preferred = {
        "SINRClass": "OK",
        "BLERClass": "OK",
        "CQIClass": "GOOD",
        "IClass": "OK",
        "DopplerClass": "OK",
        "DelaySpreadClass": "OK",
        "PowerClass": "OK",
        "DRTClass": "OK",
        "PilotDensityClass": "OK",
        "PayloadSenseClass": "OK",
        "PRSClass": "OK",
        "BeamErrorClass": "LOCKABLE",
        "BlockageClass": "NONE",
        "PdClass": "OK",
        "RfaClass": "OK",
        "AccClass": "OK",
        "CRBClass": "OK",
        "AoSClass": "FRESH",
        "CapClass": "OK",
        "CoverageClass": "OK",
        "ResourceShareClass": "OK",
        "MisClass": "OK",
        "BMOverheadClass": "OK",
        "ChannelClass": "NOMINAL",
        "SignalClass": "NOMINAL",
        "BeamClass": "SEARCH",
        "SensingState": "SensingQoSOk",
        "PHYState": "PHYNormal",
    }.get(class_name)
    if preferred in values:
        return preferred
    return values[0]
