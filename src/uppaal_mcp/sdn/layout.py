from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass, field
from typing import Any

from ..layout_core import Point, TransitionGeometry

READABLE_LAYOUT = "readable"
COMPACT_LAYOUT = "compact"


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
    return transition_geometry("", "", "", source, target, pair_index=index).labels[kind]


def nails_for(source: Point, target: Point, source_name: str, target_name: str, index: int = 0) -> list[Point]:
    return transition_geometry("", source_name, target_name, source, target, pair_index=index).nails


def transition_geometry(
    template_name: str,
    source_name: str,
    target_name: str,
    source: Point,
    target: Point,
    *,
    pair_index: int = 0,
    layout: str | None = None,
) -> TransitionGeometry:
    mode = normalize_layout_mode(layout)
    if mode == COMPACT_LAYOUT:
        base = Point((source.x + target.x) // 2 - 70 + pair_index * 22, (source.y + target.y) // 2 + pair_index * 24)
        return TransitionGeometry(labels=_label_points(base), nails=_compact_nails(source, target, source_name, target_name, pair_index))
    if source_name == target_name:
        return _self_loop_geometry(source, pair_index)
    if _is_failure_location(target_name):
        return _failure_geometry(source, target, pair_index)
    if target.x < source.x:
        return _backward_geometry(source, target, pair_index)
    if pair_index:
        return _parallel_forward_geometry(source, target, pair_index)
    return _straight_geometry(source, target)


def wrap_label(text: str, *, max_len: int = 88) -> str:
    if len(text) <= max_len:
        return text
    separators = [" || ", " && ", ", "]
    for separator in separators:
        if separator in text:
            return _wrap_by_separator(text, separator, max_len=max_len)
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if current and len(candidate) > max_len:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return "\n".join(lines)


def validate_generated_layout(model_xml: str) -> LayoutReport:
    errors: list[str] = []
    warnings: list[str] = []
    details: dict[str, Any] = {"templates": {}}
    try:
        root = ET.fromstring(model_xml)
    except ET.ParseError as exc:
        return LayoutReport(ok=False, errors=[f"XML parse error: {exc}"])
    mode = _layout_mode_from_xml(root)
    strict = mode == READABLE_LAYOUT
    for template in root.findall("template"):
        name = template.findtext("name") or "<unnamed>"
        logical_name = name[len("Template_") :] if name.startswith("Template_") else name
        coords = [(loc.attrib.get("x"), loc.attrib.get("y")) for loc in template.findall("location")]
        details["templates"][logical_name] = {
            "location_count": len(coords),
            "distinct_location_coordinates": len(set(coords)),
            "label_count": len(template.findall(".//label")),
        }
        if len(set(coords)) < len(coords):
            errors.append(f"{name} has collapsed location coordinates.")
        if logical_name in {"A_MON", "A_POLICY", "A_RULE", "A_REC", "A_SDN_AGG"}:
            xs = [int(x or 0) for x, _ in coords]
            if xs and max(xs) - min(xs) < 250:
                errors.append(f"{name} readable layout is too narrow.")
            ys = {int(y or 0) for _x, y in coords}
            if strict and len(coords) > 3 and len(ys) == 1:
                errors.append(f"{name} puts all locations on one Y line.")
        if strict:
            _check_initial_on_left(name, template, errors)
            _check_failure_on_right(name, template, errors)
        label_coords = [
            (label.attrib.get("x"), label.attrib.get("y"))
            for label in template.findall(".//label")
            if label.attrib.get("kind") != "comments"
        ]
        duplicate_count = len(label_coords) - len(set(label_coords))
        if strict and duplicate_count:
            errors.append(f"{name} has {duplicate_count} dense/reused label coordinates.")
        elif duplicate_count > 4:
            warnings.append(f"{name} has dense/reused label coordinates.")
        _check_transition_label_separation(name, template, errors)
        if strict:
            _check_self_loops_have_nails(name, template, errors)
    return LayoutReport(ok=not errors, errors=errors, warnings=warnings, details=details)


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


def _label_points(base: Point) -> dict[str, Point]:
    return {
        "guard": Point(base.x, base.y - 64),
        "synchronisation": Point(base.x, base.y - 20),
        "assignment": Point(base.x, base.y + 28),
        "comments": Point(base.x, base.y + 74),
    }


def _compact_nails(source: Point, target: Point, source_name: str, target_name: str, pair_index: int) -> list[Point]:
    if source_name == target_name:
        return [
            Point(source.x - 90 - pair_index * 28, source.y - 90),
            Point(source.x + 90 + pair_index * 28, source.y - 90),
        ]
    if target.x < source.x:
        lane = 170 + pair_index * 44
        return [Point(source.x, source.y + lane), Point(target.x, target.y + lane)]
    return []


def _straight_geometry(source: Point, target: Point) -> TransitionGeometry:
    base = Point((source.x + target.x) // 2 - 70, (source.y + target.y) // 2)
    return TransitionGeometry(labels=_label_points(base))


def _parallel_forward_geometry(source: Point, target: Point, pair_index: int) -> TransitionGeometry:
    lane = _lane_offset(pair_index)
    dx = target.x - source.x
    mid_y = (source.y + target.y) // 2 + lane
    nails = [
        Point(source.x + max(90, dx // 3), mid_y),
        Point(target.x - max(90, dx // 3), mid_y),
    ]
    base = Point((source.x + target.x) // 2 - 70, mid_y)
    return TransitionGeometry(labels=_label_points(base), nails=nails)


def _backward_geometry(source: Point, target: Point, pair_index: int) -> TransitionGeometry:
    lane = pair_index * 76
    arc_y = max(source.y, target.y) + 240 + lane
    nails = [Point(source.x + 90, arc_y), Point(target.x - 90, arc_y)]
    base = Point((source.x + target.x) // 2 - 70, arc_y - 42)
    return TransitionGeometry(labels=_label_points(base), nails=nails)


def _failure_geometry(source: Point, target: Point, pair_index: int) -> TransitionGeometry:
    lane = _lane_offset(pair_index)
    trunk_x = target.x - 140 - pair_index * 36
    mid_y = (source.y + target.y) // 2 + lane
    nails = [Point(trunk_x, source.y), Point(trunk_x, target.y)]
    base = Point(trunk_x - 126, mid_y)
    return TransitionGeometry(labels=_label_points(base), nails=nails)


def _self_loop_geometry(point: Point, pair_index: int) -> TransitionGeometry:
    tier = pair_index // 2
    side = -1 if pair_index % 2 == 0 else 1
    top_y = point.y - 138 - tier * 100
    near_x = point.x + side * (76 + tier * 18)
    far_x = point.x + side * (204 + tier * 36)
    nails = [Point(far_x, top_y), Point(near_x, top_y)]
    base = Point(far_x - 70 if side > 0 else far_x - 150, top_y - 8)
    return TransitionGeometry(labels=_label_points(base), nails=nails)


def _lane_offset(pair_index: int) -> int:
    if pair_index == 0:
        return 0
    sign = -1 if pair_index % 2 else 1
    return sign * ((pair_index + 1) // 2) * 80


def _wrap_by_separator(text: str, separator: str, *, max_len: int) -> str:
    parts = text.split(separator)
    lines: list[str] = []
    current = ""
    for index, part in enumerate(parts):
        token = part.strip()
        if index < len(parts) - 1:
            token = f"{token}{separator.strip()}"
        candidate = f"{current} {token}".strip()
        if current and len(candidate) > max_len:
            lines.append(current)
            current = token
        else:
            current = candidate
    if current:
        lines.append(current)
    return "\n".join(lines)


def _is_failure_location(name: str) -> bool:
    return name == "Violation" or "Violation" in name or name.endswith("Failure") or name.endswith("Failed") or name.endswith("Timeout")


def _layout_mode_from_xml(root: ET.Element) -> str:
    declaration = root.findtext("declaration") or ""
    match = re.search(r"Layout mode:\s*([A-Za-z_]+)", declaration)
    if not match:
        return READABLE_LAYOUT
    return normalize_layout_mode(match.group(1))


def _location_name(location: ET.Element) -> str:
    return location.findtext("name") or ""


def _location_name_by_id(template: ET.Element, ref: str) -> str:
    for location in template.findall("location"):
        if location.attrib.get("id") == ref:
            return _location_name(location)
    return ""


def _location_points(template: ET.Element) -> dict[str, Point]:
    return {
        _location_name(location): Point(int(location.attrib.get("x", "0")), int(location.attrib.get("y", "0")))
        for location in template.findall("location")
    }


def _check_initial_on_left(name: str, template: ET.Element, errors: list[str]) -> None:
    init = template.find("init")
    points = _location_points(template)
    if init is None or not points:
        return
    init_name = _location_name_by_id(template, init.attrib.get("ref", ""))
    if init_name and points[init_name].x > min(point.x for point in points.values()) + 5:
        errors.append(f"{name} initial/base state {init_name} is not on the left.")


def _check_failure_on_right(name: str, template: ET.Element, errors: list[str]) -> None:
    points = _location_points(template)
    if not points:
        return
    nominal_x = min(point.x for point in points.values())
    for loc_name, point in points.items():
        if _is_failure_location(loc_name) and point.x <= nominal_x:
            errors.append(f"{name} failure state {loc_name} is not to the right of nominal/base states.")


def _check_transition_label_separation(name: str, template: ET.Element, errors: list[str]) -> None:
    for transition in template.findall("transition"):
        coords = [
            (label.attrib.get("x"), label.attrib.get("y"))
            for label in transition.findall("label")
            if "x" in label.attrib and "y" in label.attrib
        ]
        if len(coords) != len(set(coords)):
            source = transition.find("source")
            target = transition.find("target")
            src = _location_name_by_id(template, source.attrib.get("ref", "") if source is not None else "")
            dst = _location_name_by_id(template, target.attrib.get("ref", "") if target is not None else "")
            errors.append(f"{name} transition {src}->{dst} has overlapping label coordinates.")


def _check_self_loops_have_nails(name: str, template: ET.Element, errors: list[str]) -> None:
    for transition in template.findall("transition"):
        source = transition.find("source")
        target = transition.find("target")
        if source is None or target is None:
            continue
        if source.attrib.get("ref") == target.attrib.get("ref") and not transition.findall("nail"):
            loc = _location_name_by_id(template, source.attrib.get("ref", ""))
            errors.append(f"{name} self-loop on {loc} has no bend-points/nails.")
