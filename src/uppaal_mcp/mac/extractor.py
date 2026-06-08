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
    mode: str = "section-aware-mac-extractor"
    diagnostics: list[str] = field(default_factory=list)
    sections: list[str] = field(default_factory=list)
    line_markers: dict[str, int] = field(default_factory=dict)
    compositions: dict[str, list[str]] = field(default_factory=dict)
    declarations_found: bool = False
    policies_found: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def analyze_latex(tex_text: str, *, source_name: str = SOURCE) -> ExtractionReport:
    sections = re.findall(r"\\(?:section|subsection)\{([^}]+)\}", tex_text)
    markers = _line_markers(tex_text)
    diagnostics: list[str] = []
    required = [
        "Композиция автоматов MAC",
        "Declarations уровня MAC",
        "UPPAAL templates MAC",
        "Observer-автоматы MAC",
        "Контракт MAC",
        "Верификационные свойства",
    ]
    for item in required:
        if item not in "\n".join(sections):
            diagnostics.append(f"Missing or renamed MAC section: {item}.")
    policies = sorted(set(re.findall(r"\\code\{(P[0-7])\}", tex_text)))
    if len(policies) < 8:
        diagnostics.append("MAC policy table P0..P7 was not fully detected.")
    compositions = {}
    if "A{MAC}" in tex_text:
        compositions["A_MAC"] = ["A_SCH", "A_Q", "A_BUF", "A_RSRC", "A_MAC_AGG"]
    if "A{SYS}^{MAC}" in tex_text or "A{SYS" in tex_text:
        compositions["A_SYS_MAC"] = ["A_MAC", "A_ENV_MAC"]
    declarations_found = "const int D_collect" in tex_text and "broadcast chan phy_kpi_report" in tex_text
    if not declarations_found:
        diagnostics.append("MAC declaration verbatim block was not detected.")
    return ExtractionReport(
        ok=not diagnostics,
        source_name=source_name,
        source_hash=hashlib.sha256(tex_text.encode("utf-8")).hexdigest(),
        diagnostics=diagnostics,
        sections=sections,
        line_markers=markers,
        compositions=compositions,
        declarations_found=declarations_found,
        policies_found=policies,
    )


def extract_contract_model(tex_text: str, *, source_name: str = SOURCE) -> dict:
    contract = build_default_contract().to_dict()
    contract["source_name"] = source_name
    contract["extractor"] = analyze_latex(tex_text, source_name=source_name).to_dict()
    return contract


def _line_markers(tex_text: str) -> dict[str, int]:
    patterns = {
        "alpha_MAC": r"\\alpha_\{MAC\}",
        "mu_PHY_to_MAC": r"\\mu_\{PHY\\rightarrow MAC\}",
        "A_MAC": r"\\A\{MAC\}=\\A\{SCH\}",
        "A_ENV_MAC": r"\\A\{ENV\\_MAC\}",
        "observers": r"ObsPhyAck",
        "properties": r"A\[\]\s*not\s*deadlock",
    }
    lines = tex_text.splitlines()
    result: dict[str, int] = {}
    for name, pattern in patterns.items():
        for index, line in enumerate(lines, start=1):
            if re.search(pattern, line):
                result[name] = index
                break
    return result

