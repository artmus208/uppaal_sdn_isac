from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass, field

from .defaults import SOURCE, build_default_contract


@dataclass
class ExtractionReport:
    ok: bool
    source_name: str
    source_hash: str
    mode: str = "section-aware-sdn-extractor"
    diagnostics: list[str] = field(default_factory=list)
    sections: list[str] = field(default_factory=list)
    line_markers: dict[str, int] = field(default_factory=dict)
    compositions: dict[str, list[str]] = field(default_factory=dict)
    declarations_found: bool = False
    classes_found: list[str] = field(default_factory=list)
    policies_found: list[str] = field(default_factory=list)
    observers_found: list[str] = field(default_factory=list)
    interfaces_found: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def analyze_latex(tex_text: str, *, source_name: str = SOURCE) -> ExtractionReport:
    sections = re.findall(r"\\(?:section|subsection|subsubsection)\*?\{([^}]+)\}", tex_text)
    section_text = "\n".join(sections)
    markers = _line_markers(tex_text)
    diagnostics: list[str] = []
    required_sections = [
        "Дискретная абстракция SDN/RIC",
        "Композиция автоматов SDN/RIC",
        "Политики SDN/RIC",
        "Operational semantics",
        "UPPAAL-спецификация SDN/RIC",
        "Единая интерфейсная таблица SDN/RIC",
        "Контракт SDN/RIC",
        "Верификационные свойства",
    ]
    for item in required_sections:
        if item not in section_text:
            diagnostics.append(f"Missing or renamed SDN/RIC section: {item}.")
    classes = sorted(set(re.findall(r"\\code\{(TelemetryClass|RiskClass|PolicyClass|RuleClass|RecoveryClass|SliceClass|ServiceImpact|SdnReason)\}", tex_text)))
    for item in ("TelemetryClass", "RiskClass", "PolicyClass", "RuleClass", "RecoveryClass", "SliceClass"):
        if item not in classes:
            diagnostics.append(f"Missing finite class table entry: {item}.")
    policies = sorted(set(re.findall(r"\\code\{(POL_[A-Z_]+)\}", tex_text)))
    for item in ("POL_NORMAL", "POL_SENS_BOOST", "POL_COMM_PRIO", "POL_CONSTRAINED", "POL_REROUTE", "POL_REJECT"):
        if item not in policies:
            diagnostics.append(f"Missing SDN policy: {item}.")
    observers = sorted(set(re.findall(r"template\s+(Obs[A-Za-z0-9_]+)\s*\(", tex_text)))
    for item in ("ObsRuleMiss", "ObsRecovery", "ObsAdmission", "ObsStaleTelemetry"):
        if item not in observers:
            diagnostics.append(f"Missing SDN observer: {item}.")
    interfaces = [name for name, token in {
        "rule_miss": "Rule miss",
        "recovery": "Recovery",
        "sensing_degradation": "Sensing degradation",
        "service_admission": "Service admission",
    }.items() if token in tex_text]
    for item in ("rule_miss", "recovery", "sensing_degradation", "service_admission"):
        if item not in interfaces:
            diagnostics.append(f"Missing interface procedure row: {item}.")
    compositions = {}
    if r"\A{SDN}=\A{MON}" in tex_text:
        compositions["A_SDN"] = ["A_MON", "A_RISK", "A_POLICY", "A_RULE", "A_REC", "A_SDN_AGG"]
    else:
        diagnostics.append("A_SDN composition was not detected.")
    if r"\A{SYS}^{SDN}" in tex_text and r"\A{ENV\_SDN}" in tex_text:
        compositions["A_SYS_SDN"] = ["A_SDN", "A_ENV_SDN"]
    else:
        diagnostics.append("A_SYS_SDN/A_ENV_SDN local environment composition was not detected.")
    declarations_found = "const int D_mon" in tex_text and "broadcast chan mac_report" in tex_text and "TelemetryClass_t" in tex_text
    if not declarations_found:
        diagnostics.append("SDN/RIC declaration verbatim block was not detected.")
    return ExtractionReport(
        ok=not diagnostics,
        source_name=source_name,
        source_hash=hashlib.sha256(tex_text.encode("utf-8")).hexdigest(),
        diagnostics=diagnostics,
        sections=sections,
        line_markers=markers,
        compositions=compositions,
        declarations_found=declarations_found,
        classes_found=classes,
        policies_found=policies,
        observers_found=observers,
        interfaces_found=interfaces,
    )


def extract_contract_model(tex_text: str, *, source_name: str = SOURCE) -> dict:
    contract = build_default_contract().to_dict()
    contract["source_name"] = source_name
    contract["extractor"] = analyze_latex(tex_text, source_name=source_name).to_dict()
    return contract


def _line_markers(tex_text: str) -> dict[str, int]:
    patterns = {
        "alpha_SDN": r"\\alpha_\{SDN\}",
        "A_SDN": r"\\A\{SDN\}=\\A\{MON\}",
        "A_ENV_SDN": r"\\A\{ENV\\_SDN\}",
        "declarations": r"const int D_mon",
        "policy_guards": r"bool gPolConstrained",
        "interface_table": r"I_\{SDN\}",
        "observers": r"template ObsRuleMiss",
        "properties": r"A\[\]\s+not\s+deadlock",
        "limitations": "Ограничения применимости",
    }
    lines = tex_text.splitlines()
    result: dict[str, int] = {}
    for name, pattern in patterns.items():
        for index, line in enumerate(lines, start=1):
            if re.search(pattern, line):
                result[name] = index
                break
    return result
