from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass, field
from typing import Any

READABLE_LAYOUT = "readable"
COMPACT_LAYOUT = "compact"


@dataclass(frozen=True)
class Point:
    x: int
    y: int


@dataclass
class LayoutReport:
    ok: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


POINTS = {
    "A_MON": {
        "MonitorIdle": Point(0, 0),
        "CollectReports": Point(300, 0),
        "TelemetryFresh": Point(620, -180),
        "TelemetryStale": Point(620, 0),
        "TelemetryMissing": Point(620, 180),
    },
    "A_RISK": {
        "RiskLow": Point(0, 0),
        "RiskMedium": Point(300, -120),
        "RiskHigh": Point(600, -240),
        "RiskCritical": Point(900, -360),
    },
    "A_POLICY": {
        "PolicyIdle": Point(0, 0),
        "Evaluate": Point(300, 0),
        "NormalMode": Point(650, -300),
        "SensingBoostMode": Point(650, -150),
        "CommPriorityMode": Point(650, 0),
        "ConstrainedMode": Point(650, 150),
        "RejectByPolicy": Point(650, 300),
    },
    "A_RULE": {
        "RuleStable": Point(0, 0),
        "RuleMiss": Point(260, 0),
        "RuleInstallPending": Point(560, -140),
        "RuleInstalled": Point(860, -140),
        "RuleAcked": Point(1160, -140),
        "RuleTimeout": Point(860, 80),
        "RuleDropReason": Point(560, 160),
    },
    "A_REC": {
        "StableConfig": Point(0, 0),
        "FailureDetected": Point(300, 0),
        "StandbySwitch": Point(620, -180),
        "ReactiveReembedding": Point(620, 20),
        "Rollback": Point(920, 0),
        "RecoveryFailed": Point(1220, 120),
    },
    "A_SDN_AGG": {
        "CommandBuild": Point(0, 0),
        "CommandSent": Point(300, 0),
        "AwaitAck": Point(600, 0),
        "Acked": Point(900, -160),
        "CommandTimeout": Point(900, 160),
    },
    "A_ENV_SDN": {"EnvIdle": Point(0, 0)},
    "A_SEC": {
        "SecIdle": Point(0, 0),
        "ThreatObserved": Point(300, 0),
        "SecurityReport": Point(600, -120),
        "SecurityFailure": Point(600, 120),
    },
    "Obs*": {
        "Idle": Point(0, 0),
        "Wait": Point(300, 0),
        "Violation": Point(620, -220),
        "Safe": Point(0, 0),
    },
}

TEMPLATE_PURPOSES = {
    "A_MON": "Telemetry monitor: classifies fresh/stale/missing MAC/PHY reports.",
    "A_RISK": "Risk classifier over finite telemetry, rule, recovery and slice classes.",
    "A_POLICY": "Finite SDN/RIC policy selector with stale telemetry protection.",
    "A_RULE": "Rule-miss handling: install, ack, explicit drop or timeout.",
    "A_REC": "Bounded link/node failure recovery with rollback/failure outcomes.",
    "A_SDN_AGG": "Command aggregation and lower-plane acknowledgement timeout.",
    "A_ENV_SDN": "Closed local SDN/RIC environment projection.",
    "A_SEC": "Optional security alert extension outside base A_SDN.",
}


def normalize_layout_mode(layout: str | None = None) -> str:
    if layout is None:
        return READABLE_LAYOUT
    normalized = layout.strip().lower()
    if normalized not in {READABLE_LAYOUT, COMPACT_LAYOUT}:
        raise ValueError("Unsupported SDN layout. Use readable or compact.")
    return normalized


def location_positions(template_name: str, locations: list[str], layout: str | None = None) -> dict[str, Point]:
    mode = normalize_layout_mode(layout)
    if mode == COMPACT_LAYOUT:
        return {name: Point(index * 180, 0) for index, name in enumerate(locations)}
    logical_name = template_name[len("Template_") :] if template_name.startswith("Template_") else template_name
    base = POINTS.get(logical_name) or (POINTS["Obs*"] if logical_name.startswith("Obs") else {})
    return {name: base.get(name, Point(index * 260, 180)) for index, name in enumerate(locations)}


def label_point(source: Point, target: Point, kind: str, index: int = 0) -> Point:
    mid_x = (source.x + target.x) // 2
    mid_y = (source.y + target.y) // 2
    offsets = {"guard": -64, "synchronisation": -20, "assignment": 26, "comments": 68}
    return Point(mid_x - 70 + index * 22, mid_y + offsets[kind] + index * 24)


def nails_for(source: Point, target: Point, source_name: str, target_name: str, index: int = 0) -> list[Point]:
    if source_name == target_name:
        return [Point(source.x - 90 - index * 28, source.y - 90), Point(source.x + 90 + index * 28, source.y - 90)]
    if target.x < source.x:
        return [Point(source.x, source.y + 170 + index * 44), Point(target.x, target.y + 170 + index * 44)]
    return []


def validate_generated_layout(model_xml: str) -> LayoutReport:
    errors: list[str] = []
    warnings: list[str] = []
    try:
        root = ET.fromstring(model_xml)
    except ET.ParseError as exc:
        return LayoutReport(ok=False, errors=[f"XML parse error: {exc}"])
    for template in root.findall("template"):
        name = template.findtext("name") or "<unnamed>"
        coords = [(loc.attrib.get("x"), loc.attrib.get("y")) for loc in template.findall("location")]
        if len(set(coords)) < len(coords):
            errors.append(f"{name} has collapsed location coordinates.")
        logical_name = name[len("Template_") :] if name.startswith("Template_") else name
        if logical_name in {"A_MON", "A_POLICY", "A_RULE", "A_REC", "A_SDN_AGG"}:
            xs = [int(x or 0) for x, _ in coords]
            if xs and max(xs) - min(xs) < 250:
                errors.append(f"{name} readable layout is too narrow.")
        label_coords = [
            (label.attrib.get("x"), label.attrib.get("y"))
            for label in template.findall(".//label")
            if label.attrib.get("kind") != "comments"
        ]
        if len(label_coords) - len(set(label_coords)) > 4:
            warnings.append(f"{name} has dense/reused label coordinates.")
    return LayoutReport(ok=not errors, errors=errors, warnings=warnings)


def generate_layout_maps(contract_json: dict, *, model_xml: str | None = None, layout: str | None = None) -> dict[str, str]:
    template_lines = ["# SDN/RIC Template Map", ""]
    for item in contract_json.get("automata", []):
        name = item["name"]
        template_lines.extend([f"## {name}", "", TEMPLATE_PURPOSES.get(name, "SDN/RIC template."), ""])
        template_lines.append("| Location | Invariant |")
        template_lines.append("|---|---|")
        for loc in item.get("locations", []):
            template_lines.append(f"| `{loc['name']}` | `{loc.get('invariant') or ''}` |")
        template_lines.append("")
    channel_lines = ["# SDN/RIC Channels Map", "", "| Channel | Kind | Role |", "|---|---|---|"]
    for item in contract_json.get("channels", []):
        channel_lines.append(f"| `{item['name']}` | `{item['kind']}` | {item['role']} |")
    policy_lines = ["# SDN/RIC Policy Map", "", "| Policy | Guard | Mode | Outcome |", "|---|---|---|---|"]
    for item in contract_json.get("policies", []):
        policy_lines.append(f"| `{item['name']}` | `{item['guard']}` | `{item['mode']}` | {item['outcome']} |")
    interface_lines = ["# SDN/RIC Interface Map", "", "| Procedure | Trigger | Deadline | Outcomes |", "|---|---|---|---|"]
    for item in contract_json.get("interfaces", []):
        interface_lines.append(f"| `{item['name']}` | `{item['trigger']}` | `{item['deadline']}` | {', '.join(item.get('outcomes', []))} |")
    model_lines = [
        "# SDN/RIC Model Map",
        "",
        f"- layer: `{contract_json.get('layer_id', 'sdn')}`",
        f"- components: {', '.join(contract_json.get('sdn_components', []))}",
        f"- env: {', '.join(contract_json.get('env_components', []))}",
        f"- layout: {normalize_layout_mode(layout)}",
        f"- has model xml: {model_xml is not None}",
        "",
        "SDN/RIC selects finite control policies; it does not learn, optimize, or compute PHY metrics inside timed automata.",
        "",
    ]
    return {
        "model_map.md": "\n".join(model_lines),
        "template_map.md": "\n".join(template_lines),
        "channels_map.md": "\n".join(channel_lines),
        "policy_map.md": "\n".join(policy_lines),
        "interface_map.md": "\n".join(interface_lines),
    }


def generate_diagram_artifacts(model_xml: str) -> dict[str, str]:
    root = ET.fromstring(model_xml)
    lines = ["digraph SDN_RIC {", "  rankdir=LR;", "  node [shape=box,fontname=\"DejaVu Sans\"];"]
    for template in root.findall("template"):
        template_name = template.findtext("name") or "template"
        loc_names = {loc.attrib.get("id", ""): (loc.findtext("name") or loc.attrib.get("id", "")) for loc in template.findall("location")}
        for loc in loc_names.values():
            lines.append(f'  "{template_name}.{loc}" [label="{template_name}\\n{loc}"];')
        for transition in template.findall("transition"):
            source_el = transition.find("source")
            target_el = transition.find("target")
            src = loc_names.get(source_el.attrib.get("ref", "") if source_el is not None else "", "")
            dst = loc_names.get(target_el.attrib.get("ref", "") if target_el is not None else "", "")
            labels = []
            for label in transition.findall("label"):
                if label.attrib.get("kind") in {"guard", "synchronisation"} and label.text:
                    labels.append(label.text.replace('"', "'"))
            if src and dst:
                lines.append(f'  "{template_name}.{src}" -> "{template_name}.{dst}" [label="{_dot_label(labels)}"];')
    lines.append("}")
    dot = "\n".join(lines)
    svg = _simple_svg(root)
    return {"model.dot": dot, "model.svg": svg}


def _dot_label(labels: list[str]) -> str:
    return "\\n".join(labels)[:180]


def _simple_svg(root: ET.Element) -> str:
    templates = [template.findtext("name") or "template" for template in root.findall("template")]
    rows = "\n".join(
        f'<text x="24" y="{36 + index * 24}" font-family="DejaVu Sans" font-size="14">{_escape_xml(name)}</text>'
        for index, name in enumerate(templates)
    )
    height = max(80, 52 + len(templates) * 24)
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="720" height="{height}"><rect width="100%" height="100%" fill="white"/>{rows}</svg>'


def _escape_xml(text: str) -> str:
    return re.sub(r"[&<>]", lambda m: {"&": "&amp;", "<": "&lt;", ">": "&gt;"}[m.group(0)], text)
