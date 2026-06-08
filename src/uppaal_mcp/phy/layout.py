from __future__ import annotations

import html
import math
import re
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass, field
from typing import Any, Iterable

from .defaults import build_default_contract
from .ir import PhyContractModel


READABLE_LAYOUT = "readable"
COMPACT_LAYOUT = "compact"
LAYOUT_MODES = {READABLE_LAYOUT, COMPACT_LAYOUT}


@dataclass(frozen=True)
class Point:
    x: int
    y: int


@dataclass(frozen=True)
class TransitionGeometry:
    labels: dict[str, Point]
    nails: list[Point] = field(default_factory=list)


@dataclass
class LayoutReport:
    ok: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


TEMPLATE_PURPOSES = {
    "A_CH": "Channel classifier: turns finite alpha_PHY channel classes into ChannelClass and channel reports.",
    "A_SIG": "Signal classifier: models waveform/pilot/PRS/payload sensing configuration and signal reports.",
    "A_BM": "Beam management: search, lock, prediction, recovery, handover assist and failed beam outcomes.",
    "A_SQ": "Sensing QoS classifier: aggregates child reports into finite sensing quality states.",
    "A_PH": "Aggregate PHY state: collects child reports and emits PHY KPI/failure/degradation state.",
    "ENV_CH": "Environment stimulus loop for measurement ticks and finite channel/sensing classes.",
    "ENV_TARGET": "Environment stimulus loop for target detection and blockage classes.",
    "ENV_MAC": "Environment stimulus loop for MAC/SDN configuration commands.",
    "ENV_NET": "Environment stimulus loop for network/controller delivery and freshness expiry.",
}

SEMANTIC_ZONES = {
    "A_CH": {
        "nominal": ["ChannelNominal"],
        "measurement": ["MeasurePending"],
        "channel degraded classes": ["InterferenceLimited", "MobilityLimited", "MultipathLimited", "Blockage"],
        "outage": ["Outage"],
        "contract violation": ["ContractViolation_CH"],
    },
    "A_SIG": {
        "signal nominal": ["SignalNominal", "PilotBasedSensing", "PayloadAssistedSensing"],
        "reconfiguring": ["SignalReconfiguring"],
        "signal limited": ["SignalLimited"],
        "report path": ["signal_report! transitions"],
        "violation": ["ContractViolation_SIG"],
    },
    "A_BM": {
        "beam lock": ["BeamSearch", "BeamSearchSeen", "BeamTrack", "BeamLock", "BeamPredict"],
        "recovery": ["BeamMisalign", "BeamRecoveryStart", "BeamRecover"],
        "restored": ["BeamLock"],
        "handover assist": ["BeamHOAssist"],
        "failed": ["BeamFailed", "ContractViolation_BM"],
    },
    "A_SQ": {
        "sensing nominal": ["Idle", "SensingEvaluating", "SensingQoSOk"],
        "probability/freshness/resolution limited": [
            "ProbabilityLimited",
            "FalseAlarmLimited",
            "AccuracyLimited",
            "FreshnessLimited",
            "CoverageLimited",
            "CapacityLimited",
        ],
        "failure": ["SensingFailure", "ContractViolation_SQ"],
    },
    "A_PH": {
        "aggregate normal": ["PHYNormal"],
        "communication degraded": ["PHYCommunicationDegraded"],
        "sensing degraded": ["PHYSensingDegraded"],
        "joint degraded": ["PHYJointDegraded"],
        "failure": ["PHYFailure", "ContractViolation_PH"],
        "reporting/recovery": ["PHYKpiReporting", "PHYRecovery"],
    },
    "ENV_*": {
        "environment stimulus loops": ["TickWait", "TargetWait", "ConfigWait", "DeliveryWait"],
    },
    "Obs*": {
        "trigger": ["Idle -> Wait"],
        "waiting": ["Wait"],
        "satisfied": ["Wait -> Idle response transitions"],
        "violation": ["Violation"],
    },
}

READABLE_LOCATION_POINTS = {
    "A_CH": {
        "ChannelNominal": Point(0, 0),
        "MeasurePending": Point(300, 180),
        "InterferenceLimited": Point(660, -260),
        "MobilityLimited": Point(660, -80),
        "MultipathLimited": Point(660, 100),
        "Blockage": Point(960, -440),
        "Outage": Point(960, -640),
        "ContractViolation_CH": Point(1280, 0),
    },
    "A_SIG": {
        "SignalNominal": Point(0, 0),
        "SignalReconfiguring": Point(300, 200),
        "PilotBasedSensing": Point(620, 0),
        "PayloadAssistedSensing": Point(900, 0),
        "SignalLimited": Point(1180, -220),
        "ContractViolation_SIG": Point(1480, 0),
    },
    "A_BM": {
        "BeamSearch": Point(0, 0),
        "BeamSearchSeen": Point(280, 0),
        "BeamTrack": Point(560, 0),
        "BeamLock": Point(840, 0),
        "BeamPredict": Point(840, -220),
        "BeamMisalign": Point(560, -260),
        "BeamRecoveryStart": Point(1120, 220),
        "BeamRecover": Point(1400, 220),
        "BeamHOAssist": Point(1680, 200),
        "BeamFailed": Point(1680, -260),
        "ContractViolation_BM": Point(1980, 0),
    },
    "A_SQ": {
        "Idle": Point(0, 0),
        "SensingEvaluating": Point(300, 180),
        "SensingQoSOk": Point(620, 0),
        "ProbabilityLimited": Point(620, -240),
        "FalseAlarmLimited": Point(900, -240),
        "AccuracyLimited": Point(1180, -240),
        "FreshnessLimited": Point(900, -480),
        "CoverageLimited": Point(1180, -480),
        "CapacityLimited": Point(1460, -240),
        "SensingFailure": Point(1460, -480),
        "ContractViolation_SQ": Point(1780, 0),
    },
    "A_PH": {
        "PHYNormal": Point(0, 0),
        "PHYKpiReporting": Point(320, 200),
        "PHYCommunicationDegraded": Point(660, -240),
        "PHYSensingDegraded": Point(660, -40),
        "PHYJointDegraded": Point(940, -420),
        "PHYRecovery": Point(660, 260),
        "PHYFailure": Point(1220, -300),
        "ContractViolation_PH": Point(1520, 0),
    },
    "ENV_CH": {"TickWait": Point(0, 0)},
    "ENV_TARGET": {"TargetWait": Point(0, 0)},
    "ENV_MAC": {"ConfigWait": Point(0, 0)},
    "ENV_NET": {"DeliveryWait": Point(0, 0)},
    "Obs*": {
        "Idle": Point(0, 0),
        "Wait": Point(300, 0),
        "Violation": Point(620, -220),
    },
}

LOCATION_MEANINGS = {
    "ChannelNominal": "nominal channel class; baseline left-side state",
    "MeasurePending": "measurement/report deadline window",
    "InterferenceLimited": "communication degraded by interference",
    "MobilityLimited": "communication degraded by mobility/Doppler",
    "MultipathLimited": "communication degraded by delay spread",
    "Blockage": "blockage class detected",
    "Outage": "channel outage event branch",
    "SignalNominal": "baseline signal configuration",
    "PilotBasedSensing": "pilot-based sensing mode is viable",
    "PayloadAssistedSensing": "payload-assisted sensing mode is viable",
    "SignalReconfiguring": "configuration/report deadline window",
    "SignalLimited": "signal quality is limited",
    "BeamSearch": "beam search baseline",
    "BeamSearchSeen": "target has been detected during search",
    "BeamTrack": "beam tracking path",
    "BeamLock": "locked/restored beam",
    "BeamPredict": "predictive branch before recovery",
    "BeamMisalign": "misalignment alert branch",
    "BeamRecoveryStart": "recovery trigger handoff",
    "BeamRecover": "bounded recovery deadline window",
    "BeamHOAssist": "handover assist outcome",
    "BeamFailed": "beam recovery failed",
    "Idle": "baseline idle state",
    "SensingEvaluating": "child report aggregation deadline window",
    "SensingQoSOk": "sensing QoS nominal",
    "ProbabilityLimited": "detection probability limited",
    "FalseAlarmLimited": "false alarm rate limited",
    "AccuracyLimited": "accuracy/resolution limited",
    "FreshnessLimited": "freshness/AoS limited",
    "CoverageLimited": "coverage limited",
    "CapacityLimited": "capacity/resource limited",
    "SensingFailure": "sensing failure branch",
    "PHYNormal": "aggregate PHY is normal",
    "PHYKpiReporting": "aggregate report deadline window",
    "PHYCommunicationDegraded": "aggregate communication degradation",
    "PHYSensingDegraded": "aggregate sensing degradation",
    "PHYJointDegraded": "joint communication+sensing degradation",
    "PHYRecovery": "aggregate recovery service path",
    "PHYFailure": "aggregate PHY failure branch",
    "TickWait": "environment measurement tick loop",
    "TargetWait": "environment target/blockage stimulus loop",
    "ConfigWait": "environment MAC/SDN command loop",
    "DeliveryWait": "environment delivery/freshness loop",
    "Wait": "observer waiting for bounded response",
    "Violation": "observer deadline violation",
}


def normalize_layout_mode(layout: str | None = None) -> str:
    if layout is None:
        return READABLE_LAYOUT
    normalized = layout.strip().lower()
    if normalized not in LAYOUT_MODES:
        raise ValueError("Unsupported PHY layout. Use readable or compact.")
    return normalized


def logical_template_name(template_name: str) -> str:
    name = template_name.strip()
    if name.startswith("Template_"):
        name = name[len("Template_") :]
    return name


def template_purpose(template_name: str) -> str:
    key = logical_template_name(template_name)
    if key.startswith("Obs"):
        return "Bounded-response observer: trigger, wait, response-satisfied edge, violation edge."
    return TEMPLATE_PURPOSES.get(key, "Generated UPPAAL template.")


def location_positions(
    template_name: str,
    locations: Iterable[str],
    layout: str | None = None,
) -> dict[str, Point]:
    mode = normalize_layout_mode(layout)
    names = list(locations)
    if mode == COMPACT_LAYOUT:
        return {name: Point(index * 180, 0) for index, name in enumerate(names)}

    key = logical_template_name(template_name)
    base = READABLE_LOCATION_POINTS.get(key)
    if base is None and key.startswith("Obs"):
        base = READABLE_LOCATION_POINTS["Obs*"]
    result: dict[str, Point] = {}
    max_x = max((point.x for point in (base or {}).values()), default=-300)
    for index, name in enumerate(names):
        if base and name in base:
            result[name] = base[name]
            continue
        column = index % 4
        row = index // 4
        result[name] = Point(max_x + 300 + column * 260, row * 220)
    return result


def transition_geometry(
    template_name: str,
    source: str,
    target: str,
    source_point: Point,
    target_point: Point,
    *,
    pair_index: int,
    layout: str | None = None,
) -> TransitionGeometry:
    mode = normalize_layout_mode(layout)
    if mode == COMPACT_LAYOUT:
        return TransitionGeometry(
            labels={
                "guard": Point(0, -60),
                "synchronisation": Point(0, -40),
                "assignment": Point(0, -20),
                "comments": Point(0, 0),
            }
        )

    if source == target:
        return _self_loop_geometry(source_point, pair_index)
    if _is_violation_location(target):
        return _violation_geometry(source_point, target_point, pair_index)
    if target_point.x < source_point.x:
        return _backward_geometry(source_point, target_point, pair_index)
    if pair_index:
        return _parallel_forward_geometry(source_point, target_point, pair_index)
    return _straight_geometry(source_point, target_point)


def transition_comment(
    template_name: str,
    source: str,
    target: str,
    *,
    guard: str | None = None,
    sync: str | None = None,
    assignment: str | None = None,
    layout: str | None = None,
) -> str | None:
    if normalize_layout_mode(layout) != READABLE_LAYOUT:
        return None
    sync_text = sync or ""
    if _is_violation_location(target):
        return "deadline or contract failure branch"
    if sync_text.startswith("contract_violation_"):
        return "assumption failure branch"
    if sync_text.endswith("_report!"):
        return "publish report and update finite state"
    if sync_text in {"beam_restored!", "handover_hint!", "beam_failure!"}:
        return "beam recovery outcome"
    if target.endswith("Degraded") or target.endswith("Failure") or target.endswith("Failed"):
        return "degradation or failure branch"
    if source == "Wait" and target == "Idle":
        return "bounded response satisfied"
    return None


def wrap_assignment(text: str, *, max_len: int = 76) -> str:
    if len(text) <= max_len:
        return text
    parts = [part.strip() for part in text.split(",")]
    tokens = [
        part + ("," if index < len(parts) - 1 else "")
        for index, part in enumerate(parts)
        if part
    ]
    lines: list[str] = []
    current = ""
    for token in tokens:
        candidate = f"{current} {token}".strip()
        if current and len(candidate) > max_len:
            lines.append(current)
            current = token
        else:
            current = candidate
    if current:
        lines.append(current)
    return "\n".join(lines)


def generate_layout_maps(
    contract: PhyContractModel | dict | None = None,
    *,
    model_xml: str | None = None,
    layout: str | None = None,
) -> dict[str, str]:
    model = _contract_from_any(contract)
    return {
        "model_map.md": generate_model_map(model, model_xml=model_xml, layout=layout),
        "template_map.md": generate_template_map(model, model_xml=model_xml, layout=layout),
        "channels_map.md": generate_channels_map(model, model_xml=model_xml),
    }


def generate_model_map(
    contract: PhyContractModel | dict | None = None,
    *,
    model_xml: str | None = None,
    layout: str | None = None,
) -> str:
    model = _contract_from_any(contract)
    root = _parse_xml_or_none(model_xml)
    template_io = _template_io(root, model)
    template_names = _template_names(root) or [f"Template_{name}" for name in model.phy_components + model.env_components]
    mode = normalize_layout_mode(layout)
    lines = [
        "# PHY Model Map",
        "",
        f"- layout mode: `{mode}`",
        "- coordinate convention: X left-to-right follows scenario progress.",
        "- coordinate convention: negative Y is degradation/alerts; positive Y is recovery/reporting/service paths.",
        "- coordinate convention: nominal/base states are left; violation/failure states are right.",
        "",
        "## Templates",
        "",
        "| Template | Purpose | Listens | Publishes | Writes | Reads |",
        "|---|---|---|---|---|---|",
    ]
    for template in template_names:
        key = logical_template_name(template)
        io = template_io.get(template, template_io.get(key, {}))
        lines.append(
            "| "
            + " | ".join(
                [
                    _code_cell(key),
                    _cell(template_purpose(template)),
                    _code_list(io.get("listens", [])),
                    _code_list(io.get("publishes", [])),
                    _code_list(io.get("writes", [])),
                    _code_list(io.get("reads", [])),
                ]
            )
            + " |"
        )
    lines.extend(["", "## Semantic Zones", ""])
    for template, zones in SEMANTIC_ZONES.items():
        lines.append(f"### `{template}`")
        lines.append("")
        lines.append("| Zone | Locations / paths |")
        lines.append("|---|---|")
        for zone, locations in zones.items():
            lines.append(f"| {_cell(zone)} | {_code_list(locations)} |")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def generate_template_map(
    contract: PhyContractModel | dict | None = None,
    *,
    model_xml: str | None = None,
    layout: str | None = None,
) -> str:
    model = _contract_from_any(contract)
    root = _parse_xml_or_none(model_xml)
    channel_roles = _channel_roles(root)
    mode = normalize_layout_mode(layout)
    lines = [
        "# PHY Template Map",
        "",
        f"Layout mode: `{mode}`.",
        "",
    ]
    if root is None:
        for auto in model.automata:
            lines.extend(_spec_template_section(auto.name, [loc.name for loc in auto.locations]))
        return "\n".join(lines).rstrip() + "\n"

    for template in root.findall("template"):
        template_name = _template_name(template)
        key = logical_template_name(template_name)
        lines.append(f"## `{key}`")
        lines.append("")
        lines.append(template_purpose(template_name))
        lines.append("")
        lines.append("### Locations")
        lines.append("")
        lines.append("| Location | Meaning | Coordinates |")
        lines.append("|---|---|---|")
        for location in template.findall("location"):
            loc_name = _location_name(location)
            coords = f"{location.attrib.get('x', '?')},{location.attrib.get('y', '?')}"
            lines.append(
                f"| {_code_cell(loc_name)} | {_cell(_location_meaning(key, loc_name))} | `{coords}` |"
            )
        lines.append("")
        lines.append("### Transitions")
        lines.append("")
        lines.append("| Transition | Reason | Guard | Sync | Assignment writes | Sender / listeners |")
        lines.append("|---|---|---|---|---|---|")
        for transition in template.findall("transition"):
            source = _transition_source_name(template, transition)
            target = _transition_target_name(template, transition)
            sync = _transition_sync(transition)
            guard = _transition_guard(transition)
            assignment = _transition_assignment(transition)
            writes = sorted(set(re.findall(r"\b([A-Za-z_]\w*)\s*=", assignment)))
            channel = sync.rstrip("!?")
            role = channel_roles.get(channel, {})
            sender_listener = _sync_role_text(sync, role)
            lines.append(
                "| "
                + " | ".join(
                    [
                        _code_cell(f"{source} -> {target}"),
                        _cell(_transition_reason(key, source, target, sync, guard)),
                        _code_cell(guard or "-"),
                        _code_cell(sync or "-"),
                        _code_list(writes),
                        _cell(sender_listener),
                    ]
                )
                + " |"
            )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def generate_channels_map(
    contract: PhyContractModel | dict | None = None,
    *,
    model_xml: str | None = None,
) -> str:
    model = _contract_from_any(contract)
    root = _parse_xml_or_none(model_xml)
    roles = _channel_roles(root)
    lines = [
        "# PHY Channels Map",
        "",
        "| Channel | Semantics | Declaration | Emits | Listens | Contract role |",
        "|---|---|---|---|---|---|",
    ]
    for channel in sorted(model.channels, key=lambda item: (item.kind, item.name)):
        usage = roles.get(channel.name, {})
        lines.append(
            "| "
            + " | ".join(
                [
                    _code_cell(channel.name),
                    _cell(_channel_semantics(channel.name, channel.kind)),
                    _code_cell(channel.kind),
                    _code_list(usage.get("emitters", [])),
                    _code_list(usage.get("listeners", [])),
                    _cell(channel.role),
                ]
            )
            + " |"
        )
    return "\n".join(lines) + "\n"


def validate_generated_layout(
    model_xml: str,
    *,
    min_location_distance: int = 180,
    max_label_density: int = 3,
    max_locations_on_y: int = 5,
) -> LayoutReport:
    try:
        root = ET.fromstring(model_xml)
    except ET.ParseError as exc:
        return LayoutReport(ok=False, errors=[f"XML parse error: {exc}"])

    errors: list[str] = []
    warnings: list[str] = []
    details: dict[str, Any] = {"templates": {}}
    for template in root.findall("template"):
        name = _template_name(template)
        key = logical_template_name(name)
        locations = template.findall("location")
        points = { _location_name(location): _point_from_element(location) for location in locations }
        details["templates"][key] = {
            "location_count": len(points),
            "distinct_y": len({point.y for point in points.values()}),
        }
        duplicate_locations = _duplicates((point.x, point.y) for point in points.values())
        if duplicate_locations:
            errors.append(f"{key} has overlapping location coordinates: {duplicate_locations}.")
        _check_min_location_distance(key, points, min_location_distance, errors)
        _check_initial_on_left(key, template, points, errors)
        _check_violation_on_right(key, points, errors)
        _check_not_all_on_one_line(key, points, errors)
        _check_y_line_density(key, points, max_locations_on_y, errors)
        _check_label_density(key, template, max_label_density, errors)
        _check_transition_label_separation(key, template, errors)
        _check_self_loops_have_nails(key, template, errors)
    return LayoutReport(ok=not errors, errors=errors, warnings=warnings, details=details)


def generate_diagram_artifacts(model_xml: str) -> dict[str, str]:
    root = ET.fromstring(model_xml)
    return {
        "model.dot": _diagram_dot(root),
        "model.svg": _diagram_svg(root),
    }


def _self_loop_geometry(point: Point, pair_index: int) -> TransitionGeometry:
    direction = -1 if point.y <= 80 else 1
    radius = 110 + pair_index * 46
    nails = [
        Point(point.x - 95, point.y + direction * radius),
        Point(point.x + 95, point.y + direction * radius),
    ]
    base = Point(point.x + 118, point.y + direction * (radius + 8))
    return TransitionGeometry(labels=_label_points(base), nails=nails)


def _violation_geometry(source: Point, target: Point, pair_index: int) -> TransitionGeometry:
    lane = _lane_offset(pair_index)
    trunk_x = max(source.x + 140, target.x - 160)
    nails = [
        Point(trunk_x, source.y + lane),
        Point(trunk_x, target.y + lane),
    ]
    base = Point(trunk_x - 120, (source.y + target.y) // 2 + lane)
    return TransitionGeometry(labels=_label_points(base), nails=nails)


def _backward_geometry(source: Point, target: Point, pair_index: int) -> TransitionGeometry:
    lane = pair_index * 58
    arc_y = max(source.y, target.y) + 220 + lane
    nails = [
        Point(source.x - 80, arc_y),
        Point(target.x + 80, arc_y),
    ]
    base = Point((source.x + target.x) // 2, arc_y - 54)
    return TransitionGeometry(labels=_label_points(base), nails=nails)


def _parallel_forward_geometry(source: Point, target: Point, pair_index: int) -> TransitionGeometry:
    lane = _lane_offset(pair_index)
    mid_y = (source.y + target.y) // 2 + lane
    dx = target.x - source.x
    nails = [
        Point(source.x + max(90, dx // 3), mid_y),
        Point(target.x - max(90, dx // 3), mid_y),
    ]
    base = Point((source.x + target.x) // 2, mid_y)
    return TransitionGeometry(labels=_label_points(base), nails=nails)


def _straight_geometry(source: Point, target: Point) -> TransitionGeometry:
    base = Point((source.x + target.x) // 2, (source.y + target.y) // 2)
    return TransitionGeometry(labels=_label_points(base))


def _label_points(base: Point) -> dict[str, Point]:
    return {
        "guard": Point(base.x, base.y - 58),
        "synchronisation": Point(base.x, base.y - 24),
        "assignment": Point(base.x, base.y + 18),
        "comments": Point(base.x, base.y + 62),
    }


def _lane_offset(pair_index: int) -> int:
    if pair_index == 0:
        return 0
    sign = -1 if pair_index % 2 else 1
    return sign * ((pair_index + 1) // 2) * 58


def _is_violation_location(name: str) -> bool:
    return name == "Violation" or name.startswith("ContractViolation")


def _is_failure_location(name: str) -> bool:
    return _is_violation_location(name) or name.endswith("Failure") or name.endswith("Failed")


def _contract_from_any(contract: PhyContractModel | dict | None) -> PhyContractModel:
    if contract is None:
        return build_default_contract()
    if isinstance(contract, PhyContractModel):
        return contract
    cleaned = dict(contract)
    cleaned.pop("extractor", None)
    return PhyContractModel.from_dict(cleaned)


def _parse_xml_or_none(model_xml: str | None) -> ET.Element | None:
    if not model_xml:
        return None
    try:
        return ET.fromstring(model_xml)
    except ET.ParseError:
        return None


def _template_names(root: ET.Element | None) -> list[str]:
    if root is None:
        return []
    return [_template_name(template) for template in root.findall("template")]


def _template_name(template: ET.Element) -> str:
    element = template.find("name")
    if element is None or element.text is None:
        return ""
    return element.text.strip()


def _location_name(location: ET.Element) -> str:
    element = location.find("name")
    if element is None or element.text is None:
        return ""
    return element.text.strip()


def _point_from_element(element: ET.Element) -> Point:
    return Point(int(element.attrib.get("x", "0")), int(element.attrib.get("y", "0")))


def _transition_source_name(template: ET.Element, transition: ET.Element) -> str:
    source = transition.find("source")
    ref = source.attrib.get("ref") if source is not None else ""
    return _location_name_by_id(template, ref)


def _transition_target_name(template: ET.Element, transition: ET.Element) -> str:
    target = transition.find("target")
    ref = target.attrib.get("ref") if target is not None else ""
    return _location_name_by_id(template, ref)


def _location_name_by_id(template: ET.Element, ref: str) -> str:
    for location in template.findall("location"):
        if location.attrib.get("id") == ref:
            return _location_name(location)
    return ""


def _transition_sync(transition: ET.Element) -> str:
    for label in transition.findall("label"):
        if label.attrib.get("kind") == "synchronisation":
            return _label_text(label)
    return ""


def _transition_guard(transition: ET.Element) -> str:
    return " && ".join(
        _label_text(label)
        for label in transition.findall("label")
        if label.attrib.get("kind") == "guard"
    )


def _transition_assignment(transition: ET.Element) -> str:
    return ", ".join(
        _label_text(label)
        for label in transition.findall("label")
        if label.attrib.get("kind") == "assignment"
    )


def _label_text(label: ET.Element) -> str:
    return "" if label.text is None else label.text.strip()


def _template_io(root: ET.Element | None, contract: PhyContractModel) -> dict[str, dict[str, list[str]]]:
    if root is None:
        return {}
    known_variables = {item.name for item in contract.variables} | {item.name for item in contract.classes}
    data: dict[str, dict[str, set[str]]] = {}
    for template in root.findall("template"):
        name = _template_name(template)
        entry = {
            "listens": set(),
            "publishes": set(),
            "writes": set(),
            "reads": set(),
        }
        for label in template.findall(".//label"):
            text = _label_text(label)
            kind = label.attrib.get("kind")
            if kind == "synchronisation":
                if text.endswith("?"):
                    entry["listens"].add(text[:-1])
                elif text.endswith("!"):
                    entry["publishes"].add(text[:-1])
            if kind == "assignment":
                writes = set(re.findall(r"\b([A-Za-z_]\w*)\s*=", text))
                entry["writes"].update(writes)
                entry["reads"].update(_known_tokens(text, known_variables) - writes)
            if kind == "guard":
                entry["reads"].update(_known_tokens(text, known_variables))
        data[name] = {key: sorted(value) for key, value in entry.items()}
        data[logical_template_name(name)] = data[name]
    return data


def _known_tokens(text: str, known: set[str]) -> set[str]:
    return {token for token in re.findall(r"\b[A-Za-z_]\w*\b", text) if token in known}


def _channel_roles(root: ET.Element | None) -> dict[str, dict[str, list[str]]]:
    roles: dict[str, dict[str, set[str]]] = {}
    if root is None:
        return {}
    for template in root.findall("template"):
        key = logical_template_name(_template_name(template))
        for label in template.findall(".//label"):
            if label.attrib.get("kind") != "synchronisation":
                continue
            sync = _label_text(label)
            if not sync:
                continue
            name = sync.rstrip("!?")
            entry = roles.setdefault(name, {"emitters": set(), "listeners": set()})
            if sync.endswith("!"):
                entry["emitters"].add(key)
            elif sync.endswith("?"):
                entry["listeners"].add(key)
    return {
        name: {field: sorted(values) for field, values in entry.items()}
        for name, entry in roles.items()
    }


def _sync_role_text(sync: str, role: dict[str, list[str]]) -> str:
    if not sync:
        return "-"
    channel = sync.rstrip("!?")
    emitters = ", ".join(role.get("emitters", [])) or "-"
    listeners = ", ".join(role.get("listeners", [])) or "-"
    if sync.endswith("!"):
        return f"{channel}: sender here; listeners {listeners}"
    if sync.endswith("?"):
        return f"{channel}: listener here; senders {emitters}"
    return f"{channel}: emitters {emitters}; listeners {listeners}"


def _channel_semantics(name: str, kind: str) -> str:
    if kind == "handshake":
        return "handshake command"
    if name.endswith("_report"):
        return "broadcast report"
    if any(token in name for token in ("degraded", "alert", "outage", "failure", "violation", "expired")):
        return "broadcast event/alert"
    return "broadcast event"


def _transition_reason(template: str, source: str, target: str, sync: str, guard: str) -> str:
    if _is_violation_location(target):
        return "contract/deadline failure path"
    if sync.endswith("_report!"):
        return "publishes report and commits classifier/aggregate state"
    if sync.endswith("_report?"):
        return "consumes child report"
    if sync.endswith("_cmd?") or sync.endswith("_config?"):
        return "receives MAC/SDN command"
    if sync in {"beam_restored!", "handover_hint!", "beam_failure!"}:
        return "beam recovery outcome"
    if source == target and sync:
        return "event self-loop"
    if guard:
        return "guarded classification branch"
    if sync:
        return "synchronised branch"
    return "internal/environment branch"


def _location_meaning(template: str, location: str) -> str:
    if location.startswith("ContractViolation"):
        return "contract violation sink on the right side"
    return LOCATION_MEANINGS.get(location, "generated state")


def _spec_template_section(name: str, locations: list[str]) -> list[str]:
    lines = [f"## `{name}`", "", template_purpose(name), "", "| Location | Meaning |", "|---|---|"]
    for location in locations:
        lines.append(f"| {_code_cell(location)} | {_cell(_location_meaning(name, location))} |")
    lines.append("")
    return lines


def _check_min_location_distance(
    template: str,
    points: dict[str, Point],
    minimum: int,
    errors: list[str],
) -> None:
    names = list(points)
    for index, first in enumerate(names):
        for second in names[index + 1 :]:
            p1 = points[first]
            p2 = points[second]
            distance = math.hypot(p1.x - p2.x, p1.y - p2.y)
            if distance < minimum:
                errors.append(
                    f"{template} locations {first} and {second} are too close: {distance:.1f}px < {minimum}px."
                )


def _check_initial_on_left(template: str, element: ET.Element, points: dict[str, Point], errors: list[str]) -> None:
    init = element.find("init")
    if init is None or not points:
        return
    init_name = _location_name_by_id(element, init.attrib.get("ref", ""))
    if not init_name or init_name not in points:
        return
    min_x = min(point.x for point in points.values())
    if points[init_name].x > min_x + 5:
        errors.append(f"{template} initial/base state {init_name} is not on the left.")


def _check_violation_on_right(template: str, points: dict[str, Point], errors: list[str]) -> None:
    if not points:
        return
    max_x = max(point.x for point in points.values())
    for name, point in points.items():
        if _is_violation_location(name) and point.x < max_x - 5:
            errors.append(f"{template} violation state {name} is not rightmost.")
    failure_points = {name: point for name, point in points.items() if _is_failure_location(name)}
    nominal_x = min(point.x for point in points.values())
    for name, point in failure_points.items():
        if point.x <= nominal_x:
            errors.append(f"{template} failure state {name} is not to the right of nominal/base states.")


def _check_not_all_on_one_line(template: str, points: dict[str, Point], errors: list[str]) -> None:
    if len(points) <= 3 or template.startswith("ENV"):
        return
    if len({point.y for point in points.values()}) == 1:
        errors.append(f"{template} puts all locations on one Y line.")


def _check_y_line_density(
    template: str,
    points: dict[str, Point],
    maximum: int,
    errors: list[str],
) -> None:
    density: dict[int, list[str]] = {}
    for name, point in points.items():
        density.setdefault(point.y, []).append(name)
    for y, names in density.items():
        if len(names) > maximum:
            errors.append(f"{template} has {len(names)} locations on Y={y}: {names}.")


def _check_label_density(template: str, element: ET.Element, maximum: int, errors: list[str]) -> None:
    density: dict[tuple[int, int], int] = {}
    for label in element.findall(".//label"):
        if "x" not in label.attrib or "y" not in label.attrib:
            errors.append(f"{template} label {_label_text(label)!r} has no coordinates.")
            continue
        key = (int(label.attrib["x"]), int(label.attrib["y"]))
        density[key] = density.get(key, 0) + 1
    for point, count in density.items():
        if count > maximum:
            errors.append(f"{template} has {count} labels at coordinate {point}.")


def _check_transition_label_separation(template: str, element: ET.Element, errors: list[str]) -> None:
    for transition in element.findall("transition"):
        labels = [
            (label.attrib.get("kind", ""), label.attrib.get("x"), label.attrib.get("y"))
            for label in transition.findall("label")
        ]
        coordinates = [(x, y) for _kind, x, y in labels if x is not None and y is not None]
        if len(coordinates) != len(set(coordinates)):
            source = _transition_source_name(element, transition)
            target = _transition_target_name(element, transition)
            errors.append(f"{template} transition {source}->{target} has overlapping label coordinates.")


def _check_self_loops_have_nails(template: str, element: ET.Element, errors: list[str]) -> None:
    for transition in element.findall("transition"):
        source = transition.find("source")
        target = transition.find("target")
        if source is None or target is None:
            continue
        if source.attrib.get("ref") == target.attrib.get("ref") and not transition.findall("nail"):
            loc = _location_name_by_id(element, source.attrib.get("ref", ""))
            errors.append(f"{template} self-loop on {loc} has no bend-points/nails.")


def _duplicates(values: Iterable[tuple[int, int]]) -> list[tuple[int, int]]:
    seen: set[tuple[int, int]] = set()
    duplicates: set[tuple[int, int]] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return sorted(duplicates)


def _diagram_dot(root: ET.Element) -> str:
    lines = ["digraph PHY {", "  rankdir=LR;", "  graph [splines=polyline];", "  node [shape=ellipse];"]
    for template in root.findall("template"):
        name = logical_template_name(_template_name(template))
        lines.append(f'  subgraph "cluster_{name}" {{')
        lines.append(f'    label="{_dot_escape(name)}";')
        for location in template.findall("location"):
            loc = _location_name(location)
            node = f"{name}:{loc}"
            lines.append(f'    "{_dot_escape(node)}" [label="{_dot_escape(loc)}"];')
        for transition in template.findall("transition"):
            source = _transition_source_name(template, transition)
            target = _transition_target_name(template, transition)
            sync = _transition_sync(transition)
            label = sync or _transition_guard(transition) or ""
            lines.append(
                f'    "{_dot_escape(name + ":" + source)}" -> "{_dot_escape(name + ":" + target)}" '
                f'[label="{_dot_escape(label)}"];'
            )
        lines.append("  }")
    lines.append("}")
    return "\n".join(lines) + "\n"


def _diagram_svg(root: ET.Element) -> str:
    templates = root.findall("template")
    prepared = []
    width = 1200
    cursor_y = 40
    for template in templates:
        locations = template.findall("location")
        points = [_point_from_element(location) for location in locations]
        if not points:
            continue
        min_x = min(point.x for point in points)
        max_x = max(point.x for point in points)
        min_y = min(point.y for point in points)
        max_y = max(point.y for point in points)
        shift_x = 100 - min_x
        shift_y = cursor_y + 100 - min_y
        height = max(260, (max_y - min_y) + 240)
        width = max(width, (max_x - min_x) + 260)
        prepared.append((template, shift_x, shift_y, cursor_y, height))
        cursor_y += height + 80
    height_total = max(300, cursor_y)
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height_total}" viewBox="0 0 {width} {height_total}">',
        "<defs>",
        '<marker id="arrow" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto">',
        '<path d="M0,0 L10,4 L0,8 z" fill="#334155" />',
        "</marker>",
        "</defs>",
        '<rect width="100%" height="100%" fill="#ffffff" />',
    ]
    for template, shift_x, shift_y, top_y, block_height in prepared:
        name = logical_template_name(_template_name(template))
        lines.append(f'<text x="32" y="{top_y + 24}" font-family="Arial" font-size="18" font-weight="700">{html.escape(name)}</text>')
        lines.append(f'<rect x="24" y="{top_y + 38}" width="{width - 48}" height="{block_height}" fill="none" stroke="#cbd5e1" />')
        for transition in template.findall("transition"):
            source_ref = transition.find("source").attrib.get("ref", "") if transition.find("source") is not None else ""
            target_ref = transition.find("target").attrib.get("ref", "") if transition.find("target") is not None else ""
            source_loc = _location_element_by_id(template, source_ref)
            target_loc = _location_element_by_id(template, target_ref)
            if source_loc is None or target_loc is None:
                continue
            points = [_svg_point(source_loc, shift_x, shift_y)]
            points.extend(_svg_nail(nail, shift_x, shift_y) for nail in transition.findall("nail"))
            points.append(_svg_point(target_loc, shift_x, shift_y))
            point_text = " ".join(f"{x},{y}" for x, y in points)
            lines.append(f'<polyline points="{point_text}" fill="none" stroke="#334155" stroke-width="1.3" marker-end="url(#arrow)" opacity="0.75" />')
            sync = _transition_sync(transition)
            if sync:
                label_point = _first_label_point(transition, "synchronisation", shift_x, shift_y)
                lines.append(
                    f'<text x="{label_point[0]}" y="{label_point[1]}" font-family="Arial" font-size="12" fill="#0f766e">'
                    f'{html.escape(sync)}</text>'
                )
        for location in template.findall("location"):
            loc = _location_name(location)
            x, y = _svg_point(location, shift_x, shift_y)
            fill = "#fee2e2" if _is_failure_location(loc) else "#e0f2fe" if loc in {"MeasurePending", "SignalReconfiguring", "SensingEvaluating", "PHYKpiReporting", "BeamRecover"} else "#f8fafc"
            lines.append(f'<ellipse cx="{x}" cy="{y}" rx="76" ry="28" fill="{fill}" stroke="#0f172a" />')
            lines.append(f'<text x="{x}" y="{y + 4}" text-anchor="middle" font-family="Arial" font-size="12">{html.escape(loc)}</text>')
    lines.append("</svg>")
    return "\n".join(lines) + "\n"


def _location_element_by_id(template: ET.Element, ref: str) -> ET.Element | None:
    for location in template.findall("location"):
        if location.attrib.get("id") == ref:
            return location
    return None


def _svg_point(element: ET.Element, shift_x: int, shift_y: int) -> tuple[int, int]:
    point = _point_from_element(element)
    return point.x + shift_x, point.y + shift_y


def _svg_nail(element: ET.Element, shift_x: int, shift_y: int) -> tuple[int, int]:
    return int(element.attrib.get("x", "0")) + shift_x, int(element.attrib.get("y", "0")) + shift_y


def _first_label_point(transition: ET.Element, kind: str, shift_x: int, shift_y: int) -> tuple[int, int]:
    for label in transition.findall("label"):
        if label.attrib.get("kind") == kind:
            return int(label.attrib.get("x", "0")) + shift_x, int(label.attrib.get("y", "0")) + shift_y
    return 0 + shift_x, 0 + shift_y


def _dot_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _cell(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ").strip()


def _code_cell(value: Any) -> str:
    return f"`{_cell(value)}`"


def _code_list(values: Iterable[Any]) -> str:
    items = [str(value) for value in values if str(value)]
    if not items:
        return "-"
    return ", ".join(f"`{_cell(item)}`" for item in items)
