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
    "A_SCH": {
        "Idle": Point(0, 0),
        "CollectKPI": Point(280, 0),
        "SelectMode": Point(560, 0),
        "ApplySchedule": Point(840, 0),
        "WaitPHYAck": Point(1120, 0),
        "ScheduleFailure": Point(1120, -240),
    },
    "A_Q": {
        "QueueNormal": Point(0, 0),
        "QueueWarning": Point(280, -120),
        "QueueCritical": Point(560, -240),
        "QueueDraining": Point(840, 0),
    },
    "A_BUF": {
        "BufferSafe": Point(0, 0),
        "BufferWarning": Point(280, -120),
        "BufferOverflow": Point(560, -240),
    },
    "A_RSRC": {
        "ResourceAvailable": Point(0, 0),
        "ResourceTight": Point(300, -120),
        "ResourceConflict": Point(600, -240),
        "ResourceExhausted": Point(900, -360),
    },
    "A_MAC_AGG": {
        "ReportIdle": Point(0, 0),
        "ReportBuild": Point(320, 0),
        "ReportSent": Point(640, 0),
        "ReportStale": Point(640, -220),
    },
    "A_ENV_MAC": {
        "EnvIdle": Point(0, 0),
    },
    "Obs*": {
        "Idle": Point(0, 0),
        "Wait": Point(300, 0),
        "Violation": Point(620, -220),
    },
}

TEMPLATE_PURPOSES = {
    "A_SCH": "Scheduler: collects KPI, selects finite MAC policy, sends PHY command, waits for ack.",
    "A_Q": "Queue monitor: reacts to critical queue class before D_queue_crit.",
    "A_BUF": "Buffer monitor: reports overflow before D_buf_report.",
    "A_RSRC": "Resource conflict monitor: prevents silent accept under exhausted resource.",
    "A_MAC_AGG": "MAC report aggregator: builds and broadcasts MAC report payload.",
    "A_ENV_MAC": "Closed MAC environment projection: admissible ticks, PHY KPI, SDN policy and PHY ack.",
}


def normalize_layout_mode(layout: str | None = None) -> str:
    if layout is None:
        return READABLE_LAYOUT
    normalized = layout.strip().lower()
    if normalized not in {READABLE_LAYOUT, COMPACT_LAYOUT}:
        raise ValueError("Unsupported MAC layout. Use readable or compact.")
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
    offsets = {
        "guard": -64,
        "synchronisation": -20,
        "assignment": 26,
        "comments": 68,
    }
    return Point(mid_x - 70 + index * 18, mid_y + offsets[kind] + index * 24)


def nails_for(source: Point, target: Point, source_name: str, target_name: str, index: int = 0) -> list[Point]:
    if source_name == target_name:
        return [
            Point(source.x - 80 - index * 20, source.y - 80),
            Point(source.x + 80 + index * 20, source.y - 80),
        ]
    if target.x < source.x:
        return [Point(source.x, source.y + 160 + index * 40), Point(target.x, target.y + 160 + index * 40)]
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
        coords = []
        for location in template.findall("location"):
            coords.append((location.attrib.get("x"), location.attrib.get("y")))
        if len(set(coords)) < len(coords):
            errors.append(f"{name} has collapsed location coordinates.")
        logical_name = name[len("Template_") :] if name.startswith("Template_") else name
        if logical_name in {"A_SCH", "A_Q", "A_BUF", "A_RSRC", "A_MAC_AGG"}:
            xs = [int(x or 0) for x, _ in coords]
            if xs and max(xs) - min(xs) < 250:
                errors.append(f"{name} readable layout is too narrow.")
        label_coords = [
            (label.attrib.get("x"), label.attrib.get("y"))
            for label in template.findall(".//label")
            if label.attrib.get("kind") != "comments"
        ]
        if len(label_coords) - len(set(label_coords)) > 3:
            warnings.append(f"{name} has dense/reused label coordinates.")
    return LayoutReport(ok=not errors, errors=errors, warnings=warnings)


def generate_layout_maps(contract_json: dict, *, model_xml: str | None = None, layout: str | None = None) -> dict[str, str]:
    template_lines = ["# MAC Template Map", ""]
    for item in contract_json.get("automata", []):
        name = item["name"]
        template_lines.extend([f"## {name}", "", TEMPLATE_PURPOSES.get(name, "MAC template."), ""])
        template_lines.append("| Location | Meaning | Invariant |")
        template_lines.append("|---|---|---|")
        for loc in item.get("locations", []):
            template_lines.append(f"| `{loc['name']}` | MAC state | `{loc.get('invariant') or ''}` |")
        template_lines.append("")
    channel_lines = ["# MAC Channels Map", "", "| Channel | Kind | Role |", "|---|---|---|"]
    for item in contract_json.get("channels", []):
        channel_lines.append(f"| `{item['name']}` | `{item['kind']}` | {item['role']} |")
    policy_lines = ["# MAC Policy Map", "", "| Policy | Guard | Mode | Outcome |", "|---|---|---|---|"]
    for item in contract_json.get("policies", []):
        policy_lines.append(f"| `{item['name']}` | `{item['guard']}` | `{item['mode']}` | {item['outcome']} |")
    model_lines = [
        "# MAC Model Map",
        "",
        f"- layer: `{contract_json.get('layer_id', 'mac')}`",
        f"- components: {', '.join(contract_json.get('mac_components', []))}",
        f"- env: {', '.join(contract_json.get('env_components', []))}",
        f"- layout: {normalize_layout_mode(layout)}",
        f"- has model xml: {model_xml is not None}",
        "",
        "MAC is local scheduling logic only. SDN/RIC global recovery and admission control are outside this layer.",
        "",
    ]
    return {
        "model_map.md": "\n".join(model_lines),
        "template_map.md": "\n".join(template_lines),
        "channels_map.md": "\n".join(channel_lines) + "\n",
        "policy_map.md": "\n".join(policy_lines) + "\n",
    }


def generate_diagram_artifacts(model_xml: str) -> dict[str, str]:
    root = ET.fromstring(model_xml)
    lines = ["digraph MAC {", "  rankdir=LR;"]
    for template in root.findall("template"):
        name = template.findtext("name") or "Template"
        lines.append(f'  subgraph "cluster_{name}" {{')
        lines.append(f'    label="{name}";')
        locations = {loc.attrib["id"]: loc.findtext("name") or loc.attrib["id"] for loc in template.findall("location")}
        for loc_name in locations.values():
            lines.append(f'    "{name}.{loc_name}" [label="{loc_name}"];')
        for transition in template.findall("transition"):
            source_el = transition.find("source")
            target_el = transition.find("target")
            source = locations.get(source_el.attrib.get("ref", "") if source_el is not None else "", "?")
            target = locations.get(target_el.attrib.get("ref", "") if target_el is not None else "", "?")
            sync = ""
            for label in transition.findall("label"):
                if label.attrib.get("kind") == "synchronisation":
                    sync = label.text or ""
            lines.append(f'    "{name}.{source}" -> "{name}.{target}" [label="{sync}"];')
        lines.append("  }")
    lines.append("}")
    dot = "\n".join(lines) + "\n"
    svg = "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"900\" height=\"120\"><text x=\"20\" y=\"40\">MAC diagram DOT generated; render model.dot with Graphviz for full diagram.</text></svg>\n"
    return {"model.dot": dot, "model.svg": svg}
