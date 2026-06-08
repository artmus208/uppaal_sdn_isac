from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass

from .alpha import default_profile
from .defaults import build_default_contract
from .ir import MacContractModel, PropertySpec
from .layout import (
    Point,
    TransitionGeometry,
    location_positions,
    normalize_layout_mode,
    transition_geometry,
    validate_generated_layout,
    generate_layout_maps,
    wrap_label,
)


@dataclass(frozen=True)
class GeneratedMacModel:
    model_xml: str
    queries: str
    contract: dict
    profile: dict
    layout: str
    model_map: str
    template_map: str
    channels_map: str
    policy_map: str
    layout_validation: dict
    generation_mode: str = "with_observers"
    include_negative_scenarios: bool = False
    system_mode: str = "closed"

    def to_dict(self) -> dict:
        return asdict(self)


class UppaalXmlBuilder:
    def __init__(self, *, layout: str | None = None) -> None:
        self.root = ET.Element("nta")
        self.layout = normalize_layout_mode(layout)
        self.location_ids: dict[int, dict[str, str]] = {}
        self.points: dict[int, dict[str, object]] = {}
        self.edge_counts: dict[tuple[int, str, str], int] = {}
        self.label_points: dict[int, set[tuple[int, int]]] = {}

    def declaration(self, text: str) -> None:
        ET.SubElement(self.root, "declaration").text = text

    def template(self, name: str, initial: str, locations: list[tuple[str, str | None]]) -> ET.Element:
        template = ET.SubElement(self.root, "template")
        ET.SubElement(template, "name").text = name
        names = [item[0] for item in locations]
        points = location_positions(name, names, self.layout)
        ids = {}
        for index, (loc_name, invariant) in enumerate(locations):
            loc_id = f"{_safe(name)}_{index}"
            ids[loc_name] = loc_id
            point = points[loc_name]
            loc = ET.SubElement(template, "location", {"id": loc_id, "x": str(point.x), "y": str(point.y)})
            ET.SubElement(loc, "name", {"x": str(point.x - 55), "y": str(point.y - 35)}).text = loc_name
            if invariant:
                ET.SubElement(loc, "label", {"kind": "invariant", "x": str(point.x - 70), "y": str(point.y + 35)}).text = invariant
        ET.SubElement(template, "init", {"ref": ids[initial]})
        self.location_ids[id(template)] = ids
        self.points[id(template)] = points
        self.label_points[id(template)] = set()
        return template

    def add_transition(self, template: ET.Element, source: str, target: str, *, guard: str | None = None, sync: str | None = None, assignment: str | None = None, comment: str | None = None) -> None:
        ids = self.location_ids[id(template)]
        points = self.points[id(template)]
        count_key = (id(template), source, target)
        index = self.edge_counts.get(count_key, 0)
        self.edge_counts[count_key] = index + 1
        src = points[source]
        dst = points[target]
        geometry = transition_geometry(
            template.findtext("name") or "",
            source,
            target,
            src,
            dst,
            pair_index=index,
            layout=self.layout,
        )
        label_kinds = [
            kind
            for kind, present in (
                ("guard", bool(guard)),
                ("synchronisation", bool(sync)),
                ("assignment", bool(assignment)),
                ("comments", bool(comment)),
            )
            if present
        ]
        geometry = _avoid_label_collisions(geometry, label_kinds, self.label_points[id(template)])
        transition = ET.SubElement(template, "transition")
        ET.SubElement(transition, "source", {"ref": ids[source]})
        ET.SubElement(transition, "target", {"ref": ids[target]})
        if guard:
            pt = geometry.labels["guard"]
            ET.SubElement(transition, "label", {"kind": "guard", "x": str(pt.x), "y": str(pt.y)}).text = wrap_label(guard)
        if sync:
            pt = geometry.labels["synchronisation"]
            ET.SubElement(transition, "label", {"kind": "synchronisation", "x": str(pt.x), "y": str(pt.y)}).text = sync
        if assignment:
            pt = geometry.labels["assignment"]
            ET.SubElement(transition, "label", {"kind": "assignment", "x": str(pt.x), "y": str(pt.y)}).text = wrap_label(assignment)
        if comment:
            pt = geometry.labels["comments"]
            ET.SubElement(transition, "label", {"kind": "comments", "x": str(pt.x), "y": str(pt.y)}).text = wrap_label(comment)
        for nail in geometry.nails:
            ET.SubElement(transition, "nail", {"x": str(nail.x), "y": str(nail.y)})
        for kind in label_kinds:
            pt = geometry.labels[kind]
            self.label_points[id(template)].add((pt.x, pt.y))

    def system(self, text: str) -> None:
        ET.SubElement(self.root, "system").text = text

    def to_xml(self) -> str:
        ET.indent(self.root, space="  ")
        body = ET.tostring(self.root, encoding="unicode")
        return (
            '<?xml version="1.0" encoding="utf-8"?>\n'
            '<!DOCTYPE nta PUBLIC "-//Uppaal Team//DTD Flat System 1.6//EN" '
            '"http://www.it.uu.se/research/group/darts/uppaal/flat-1_6.dtd">\n'
            f"{body}\n"
        )


def generate_uppaal_model(
    contract: MacContractModel | None = None,
    profile: dict | None = None,
    *,
    include_observers: bool = True,
    debug_counters: bool = True,
    include_negative_scenarios: bool = False,
    mode: str | None = None,
    layout: str | None = None,
) -> GeneratedMacModel:
    model = contract or build_default_contract()
    profile = profile or default_profile()
    layout_mode = normalize_layout_mode(layout)
    mode_name, include_observers, debug_counters, include_negative_scenarios = _normalize_generation_mode(
        mode,
        include_observers=include_observers,
        debug_counters=debug_counters,
        include_negative_scenarios=include_negative_scenarios,
    )
    builder = UppaalXmlBuilder(layout=layout_mode)
    builder.declaration(_declarations(profile, mode_name=mode_name, layout_mode=layout_mode, debug_counters=debug_counters, include_negative_scenarios=include_negative_scenarios))
    _add_a_sch(builder)
    _add_a_q(builder)
    _add_a_buf(builder)
    _add_a_rsrc(builder)
    _add_a_mac_agg(builder)
    _add_a_env_mac(builder)
    if include_observers:
        _add_obs_phy_ack(builder)
        _add_obs_queue_critical(builder)
        _add_obs_sensing_critical(builder)
        _add_obs_buffer_overflow(builder)
        _add_obs_mac_report_freshness(builder)
    builder.system(_system_declaration(include_observers=include_observers))
    model_xml = builder.to_xml()
    maps = generate_layout_maps(model.to_dict(), model_xml=model_xml, layout=layout_mode)
    return GeneratedMacModel(
        model_xml=model_xml,
        queries=generate_queries(model, include_observers=include_observers, debug_counters=debug_counters),
        contract=model.to_dict(),
        profile=profile,
        layout=layout_mode,
        model_map=maps["model_map.md"],
        template_map=maps["template_map.md"],
        channels_map=maps["channels_map.md"],
        policy_map=maps["policy_map.md"],
        layout_validation=validate_generated_layout(model_xml).to_dict(),
        generation_mode=mode_name,
        include_negative_scenarios=include_negative_scenarios,
    )


def generate_queries(contract: MacContractModel | None = None, *, include_observers: bool = True, debug_counters: bool = True) -> str:
    model = contract or build_default_contract()
    queries: list[PropertySpec] = []
    for item in model.properties:
        if item.name.startswith("Obs") and not include_observers:
            continue
        queries.append(item)
    if debug_counters:
        queries.append(PropertySpec("policy_totality", "A[] policy_enabled_count >= 1", "debug", "at least one policy/fallback is enabled"))
    return "\n".join(item.query for item in queries) + "\n"


def _normalize_generation_mode(mode: str | None, *, include_observers: bool, debug_counters: bool, include_negative_scenarios: bool) -> tuple[str, bool, bool, bool]:
    if mode is None:
        if include_negative_scenarios:
            return "with_negative_scenarios", include_observers, debug_counters, True
        if include_observers and debug_counters:
            return "with_observers", True, True, False
        if debug_counters:
            return "with_debug_counters", include_observers, True, False
        if not include_observers:
            return "minimal", False, False, False
        return "custom", include_observers, debug_counters, include_negative_scenarios
    normalized = mode.strip().lower()
    if normalized == "minimal":
        return "minimal", False, False, False
    if normalized == "with_observers":
        return "with_observers", True, debug_counters, include_negative_scenarios
    if normalized == "with_debug_counters":
        return "with_debug_counters", include_observers, True, include_negative_scenarios
    if normalized == "with_negative_scenarios":
        return "with_negative_scenarios", include_observers, debug_counters, True
    raise ValueError("Unsupported MAC generation mode. Use minimal, with_observers, with_debug_counters, or with_negative_scenarios.")


def _declarations(profile: dict, *, mode_name: str, layout_mode: str, debug_counters: bool, include_negative_scenarios: bool) -> str:
    d = profile.get("deadlines", {})
    lines = [
        "// Generated from MAC contract IR. Raw queue/delay/loss/utilization samples stay outside timed automata.",
        f"// Generation mode: {mode_name}.",
        f"// Layout mode: {layout_mode}.",
        "// Negative scenarios are emitted by benchmark mutations." if include_negative_scenarios else "// Negative scenarios disabled for this generated model.",
        f"const int D_collect = {int(d.get('D_collect', 2))};",
        f"const int D_sched = {int(d.get('D_sched', 5))};",
        f"const int D_phy_ack = {int(d.get('D_phy_ack', 3))};",
        f"const int D_queue_crit = {int(d.get('D_queue_crit', 10))};",
        f"const int D_buf_report = {int(d.get('D_buf_report', 4))};",
        f"const int D_mac_report = {int(d.get('D_mac_report', 5))};",
        f"const int D_phy_report = {int(d.get('D_phy_report', 10))};",
        "",
        "clock c_sched, c_phy_ack, c_queue, c_buf, c_report;",
        "clock c_obs_ack, c_obs_queue, c_obs_sensing, c_obs_buf, c_obs_report;",
        "",
        "broadcast chan phy_kpi_report, mac_report;",
        "chan mac_tick, sdn_policy_cmd, service_priority, phy_ack;",
        "chan mac_schedule_cmd, beam_update_cmd, sensing_boost_cmd, constrained_mode_cmd, resource_reject;",
        "",
        "typedef int[0,4] QueueClass_t;",
        "const QueueClass_t Q_EMPTY=0, Q_LOW=1, Q_MED=2, Q_HIGH=3, Q_CRIT=4;",
        "typedef int[0,2] BufferClass_t;",
        "const BufferClass_t B_SAFE=0, B_WARN=1, B_OVERFLOW=2;",
        "typedef int[0,3] DelayClass_t;",
        "const DelayClass_t D_OK=0, D_WARN=1, D_DEADLINE_RISK=2, D_VIOLATED=3;",
        "typedef int[0,2] DropClass_t;",
        "const DropClass_t DROP_NONE=0, DROP_LOW=1, DROP_HIGH=2;",
        "typedef int[0,3] ResourceClass_t;",
        "const ResourceClass_t RES_FREE=0, RES_BALANCED=1, RES_TIGHT=2, RES_EXHAUSTED=3;",
        "typedef int[0,2] SensingDemand_t;",
        "const SensingDemand_t SENS_NOMINAL=0, SENS_BOOST_REQ=1, SENS_CRITICAL=2;",
        "typedef int[0,2] CommDemand_t;",
        "const CommDemand_t COMM_NOMINAL=0, COMM_HIGH=1, COMM_CRITICAL=2;",
        "typedef int[0,2] KPIFreshnessClass_t;",
        "const KPIFreshnessClass_t KPI_FRESH=0, KPI_STALE=1, KPI_MISSING=2;",
        "typedef int[0,4] ScheduleMode_t;",
        "const ScheduleMode_t SCH_IDLE=0, SCH_COMM=1, SCH_SENS=2, SCH_JOINT=3, SCH_CONSTRAINED=4;",
        "typedef int[0,6] MacReason_t;",
        "const MacReason_t REASON_NONE=0, REASON_RESOURCE_EXHAUSTED=1, REASON_PHY_ACK_TIMEOUT=2, REASON_QUEUE_CRITICAL=3, REASON_SENS_COMM_CONFLICT=4, REASON_STALE_PHY_KPI=5, REASON_BUFFER_OVERFLOW=6;",
        "",
        "QueueClass_t queueClass = Q_EMPTY;",
        "BufferClass_t bufferClass = B_SAFE;",
        "DelayClass_t delayClass = D_OK;",
        "DropClass_t dropClass = DROP_NONE;",
        "ResourceClass_t resourceClass = RES_FREE;",
        "ResourceClass_t mappedResourceClass = RES_FREE;",
        "SensingDemand_t sensingDemand = SENS_NOMINAL;",
        "CommDemand_t commDemand = COMM_NOMINAL;",
        "KPIFreshnessClass_t kpiFreshnessClass = KPI_FRESH;",
        "ScheduleMode_t scheduleMode = SCH_IDLE;",
        "MacReason_t macReason = REASON_NONE;",
        "bool mac_report_pending = false;",
        "bool mac_report_sent = false;",
        "bool silent_accept = false;",
        "bool phy_ack_timeout = false;",
        "bool phy_command_pending = false;",
        "bool sdn_sensing_priority_allowed = false;",
        "bool sdn_comm_priority_allowed = false;",
        "int[0,8] policy_enabled_count = 1;",
        "",
        "bool gP0() { return resourceClass == RES_EXHAUSTED || mappedResourceClass == RES_EXHAUSTED; }",
        "bool gP1() { return bufferClass == B_OVERFLOW || delayClass == D_VIOLATED; }",
        "bool gP2() { return queueClass == Q_CRIT && commDemand == COMM_CRITICAL; }",
        "bool gP3() { return sensingDemand == SENS_CRITICAL && sdn_sensing_priority_allowed; }",
        "bool gP4() { return resourceClass == RES_TIGHT && sensingDemand != SENS_NOMINAL && commDemand != COMM_NOMINAL; }",
        "bool gP5() { return kpiFreshnessClass == KPI_STALE || kpiFreshnessClass == KPI_MISSING; }",
        "bool gP6() { return resourceClass == RES_FREE || resourceClass == RES_BALANCED; }",
        "bool gP7() { return true; }",
        "void update_policy_counter() { policy_enabled_count = 0; if (gP0()) policy_enabled_count++; if (gP1()) policy_enabled_count++; if (gP2()) policy_enabled_count++; if (gP3()) policy_enabled_count++; if (gP4()) policy_enabled_count++; if (gP5()) policy_enabled_count++; if (gP6()) policy_enabled_count++; if (gP7()) policy_enabled_count++; }",
        "void select_mac_policy() { update_policy_counter(); silent_accept = false; if (gP0()) { scheduleMode = SCH_CONSTRAINED; macReason = REASON_RESOURCE_EXHAUSTED; mac_report_pending = true; } else if (gP1()) { scheduleMode = SCH_COMM; } else if (gP2()) { scheduleMode = SCH_COMM; } else if (gP3()) { scheduleMode = SCH_SENS; } else if (gP4()) { scheduleMode = SCH_JOINT; macReason = REASON_SENS_COMM_CONFLICT; } else if (gP5()) { scheduleMode = SCH_CONSTRAINED; macReason = REASON_STALE_PHY_KPI; } else if (gP6()) { scheduleMode = SCH_JOINT; } else { scheduleMode = SCH_CONSTRAINED; } }",
    ]
    if not debug_counters:
        lines.append("// Debug counter query disabled by generation mode.")
    return "\n".join(lines)


def _add_a_sch(builder: UppaalXmlBuilder) -> None:
    t = builder.template("Template_A_SCH", "Idle", [("Idle", None), ("CollectKPI", "c_sched <= D_collect"), ("SelectMode", "c_sched <= D_sched"), ("ApplySchedule", None), ("WaitPHYAck", "c_phy_ack <= D_phy_ack"), ("ScheduleFailure", None)])
    builder.add_transition(t, "Idle", "CollectKPI", sync="mac_tick?", assignment="c_sched = 0, mac_report_sent = false", comment="start scheduling window")
    builder.add_transition(t, "CollectKPI", "SelectMode", guard="c_sched <= D_collect", sync="phy_kpi_report?", assignment="c_sched = 0", comment="fresh KPI collected")
    builder.add_transition(t, "CollectKPI", "ApplySchedule", guard="kpiFreshnessClass != KPI_FRESH || c_sched == D_collect", assignment="scheduleMode = SCH_CONSTRAINED, macReason = REASON_STALE_PHY_KPI, c_phy_ack = 0", comment="stale KPI fallback")
    builder.add_transition(t, "SelectMode", "ScheduleFailure", guard="gP0()", assignment="scheduleMode = SCH_CONSTRAINED, macReason = REASON_RESOURCE_EXHAUSTED, mac_report_pending = true, silent_accept = false", comment="explicit exhausted-resource path")
    builder.add_transition(t, "SelectMode", "ApplySchedule", guard="!gP0()", assignment="select_mac_policy(), c_phy_ack = 0, phy_command_pending = true", comment="apply selected finite policy")
    builder.add_transition(t, "ApplySchedule", "WaitPHYAck", sync="mac_schedule_cmd!", assignment="phy_command_pending = true", comment="send PHY command")
    builder.add_transition(t, "WaitPHYAck", "Idle", guard="c_phy_ack <= D_phy_ack", sync="phy_ack?", assignment="phy_command_pending = false, phy_ack_timeout = false", comment="PHY acknowledged")
    builder.add_transition(t, "WaitPHYAck", "ScheduleFailure", guard="c_phy_ack == D_phy_ack", assignment="phy_ack_timeout = true, macReason = REASON_PHY_ACK_TIMEOUT, mac_report_pending = true, phy_command_pending = false", comment="ack timeout")
    builder.add_transition(t, "ScheduleFailure", "Idle", sync="mac_report!", assignment="mac_report_sent = true, mac_report_pending = false, silent_accept = false", comment="report local failure")


def _add_a_q(builder: UppaalXmlBuilder) -> None:
    t = builder.template("Template_A_Q", "QueueNormal", [("QueueNormal", None), ("QueueWarning", None), ("QueueCritical", "c_queue <= D_queue_crit"), ("QueueDraining", None)])
    builder.add_transition(t, "QueueNormal", "QueueWarning", guard="queueClass == Q_HIGH")
    builder.add_transition(t, "QueueNormal", "QueueCritical", guard="queueClass == Q_CRIT", assignment="c_queue = 0, mac_report_pending = true, macReason = REASON_QUEUE_CRITICAL")
    builder.add_transition(t, "QueueWarning", "QueueCritical", guard="queueClass == Q_CRIT", assignment="c_queue = 0, mac_report_pending = true, macReason = REASON_QUEUE_CRITICAL")
    builder.add_transition(t, "QueueCritical", "QueueDraining", guard="c_queue <= D_queue_crit && (scheduleMode == SCH_COMM || scheduleMode == SCH_CONSTRAINED || mac_report_sent)")
    builder.add_transition(t, "QueueCritical", "QueueDraining", guard="c_queue == D_queue_crit", sync="resource_reject!", assignment="mac_report_pending = true, macReason = REASON_QUEUE_CRITICAL")
    builder.add_transition(t, "QueueDraining", "QueueNormal", guard="queueClass != Q_CRIT")
    builder.add_transition(t, "QueueWarning", "QueueNormal", guard="queueClass < Q_HIGH")


def _add_a_buf(builder: UppaalXmlBuilder) -> None:
    t = builder.template("Template_A_BUF", "BufferSafe", [("BufferSafe", None), ("BufferWarning", None), ("BufferOverflow", "c_buf <= D_buf_report")])
    builder.add_transition(t, "BufferSafe", "BufferWarning", guard="bufferClass == B_WARN")
    builder.add_transition(t, "BufferSafe", "BufferOverflow", guard="bufferClass == B_OVERFLOW", assignment="c_buf = 0, mac_report_pending = true, macReason = REASON_BUFFER_OVERFLOW")
    builder.add_transition(t, "BufferWarning", "BufferOverflow", guard="bufferClass == B_OVERFLOW", assignment="c_buf = 0, mac_report_pending = true, macReason = REASON_BUFFER_OVERFLOW")
    builder.add_transition(t, "BufferOverflow", "BufferSafe", guard="bufferClass != B_OVERFLOW")
    builder.add_transition(t, "BufferOverflow", "BufferSafe", guard="c_buf == D_buf_report", sync="mac_report!", assignment="mac_report_sent = true, mac_report_pending = false")
    builder.add_transition(t, "BufferWarning", "BufferSafe", guard="bufferClass == B_SAFE")


def _add_a_rsrc(builder: UppaalXmlBuilder) -> None:
    t = builder.template("Template_A_RSRC", "ResourceAvailable", [("ResourceAvailable", None), ("ResourceTight", None), ("ResourceConflict", None), ("ResourceExhausted", None)])
    builder.add_transition(t, "ResourceAvailable", "ResourceTight", guard="resourceClass == RES_TIGHT")
    builder.add_transition(t, "ResourceAvailable", "ResourceExhausted", guard="resourceClass == RES_EXHAUSTED || mappedResourceClass == RES_EXHAUSTED", assignment="silent_accept = false, mac_report_pending = true, macReason = REASON_RESOURCE_EXHAUSTED")
    builder.add_transition(t, "ResourceTight", "ResourceConflict", guard="sensingDemand != SENS_NOMINAL && commDemand != COMM_NOMINAL", assignment="macReason = REASON_SENS_COMM_CONFLICT")
    builder.add_transition(t, "ResourceConflict", "ResourceExhausted", guard="resourceClass == RES_EXHAUSTED", assignment="silent_accept = false, mac_report_pending = true")
    builder.add_transition(t, "ResourceExhausted", "ResourceAvailable", sync="resource_reject!", assignment="silent_accept = false, mac_report_pending = true")
    builder.add_transition(t, "ResourceTight", "ResourceAvailable", guard="resourceClass == RES_FREE || resourceClass == RES_BALANCED")
    builder.add_transition(t, "ResourceConflict", "ResourceAvailable", guard="resourceClass == RES_FREE || resourceClass == RES_BALANCED")


def _add_a_mac_agg(builder: UppaalXmlBuilder) -> None:
    t = builder.template("Template_A_MAC_AGG", "ReportIdle", [("ReportIdle", None), ("ReportBuild", "c_report <= D_mac_report"), ("ReportSent", None), ("ReportStale", None)])
    builder.add_transition(t, "ReportIdle", "ReportBuild", guard="mac_report_pending", assignment="c_report = 0")
    builder.add_transition(t, "ReportBuild", "ReportSent", guard="c_report <= D_mac_report", sync="mac_report!", assignment="mac_report_sent = true, mac_report_pending = false")
    builder.add_transition(t, "ReportBuild", "ReportStale", guard="c_report == D_mac_report", assignment="macReason = REASON_STALE_PHY_KPI")
    builder.add_transition(t, "ReportStale", "ReportSent", sync="mac_report!", assignment="mac_report_sent = true, mac_report_pending = false")
    builder.add_transition(t, "ReportSent", "ReportIdle", assignment="mac_report_sent = false")


def _add_a_env_mac(builder: UppaalXmlBuilder) -> None:
    t = builder.template("Template_A_ENV_MAC", "EnvIdle", [("EnvIdle", None)])
    builder.add_transition(t, "EnvIdle", "EnvIdle", sync="mac_tick!")
    builder.add_transition(t, "EnvIdle", "EnvIdle", sync="phy_kpi_report!")
    builder.add_transition(t, "EnvIdle", "EnvIdle", sync="sdn_policy_cmd!", assignment="sdn_sensing_priority_allowed = true, sdn_comm_priority_allowed = true")
    builder.add_transition(t, "EnvIdle", "EnvIdle", sync="service_priority!", assignment="commDemand = COMM_CRITICAL")
    builder.add_transition(t, "EnvIdle", "EnvIdle", sync="phy_ack!")
    builder.add_transition(t, "EnvIdle", "EnvIdle", sync="mac_schedule_cmd?")
    builder.add_transition(t, "EnvIdle", "EnvIdle", sync="beam_update_cmd?")
    builder.add_transition(t, "EnvIdle", "EnvIdle", sync="sensing_boost_cmd?")
    builder.add_transition(t, "EnvIdle", "EnvIdle", sync="constrained_mode_cmd?")
    builder.add_transition(t, "EnvIdle", "EnvIdle", sync="resource_reject?")
    builder.add_transition(t, "EnvIdle", "EnvIdle", assignment="queueClass = Q_CRIT, bufferClass = B_SAFE, resourceClass = RES_BALANCED")
    builder.add_transition(t, "EnvIdle", "EnvIdle", assignment="bufferClass = B_OVERFLOW, queueClass = Q_LOW")
    builder.add_transition(t, "EnvIdle", "EnvIdle", assignment="resourceClass = RES_EXHAUSTED, mappedResourceClass = RES_EXHAUSTED")
    builder.add_transition(t, "EnvIdle", "EnvIdle", assignment="sensingDemand = SENS_CRITICAL, resourceClass = RES_TIGHT")
    builder.add_transition(t, "EnvIdle", "EnvIdle", assignment="kpiFreshnessClass = KPI_STALE")
    builder.add_transition(t, "EnvIdle", "EnvIdle", assignment="queueClass = Q_EMPTY, bufferClass = B_SAFE, resourceClass = RES_FREE, mappedResourceClass = RES_FREE, sensingDemand = SENS_NOMINAL, commDemand = COMM_NOMINAL, kpiFreshnessClass = KPI_FRESH")


def _add_obs_phy_ack(builder: UppaalXmlBuilder) -> None:
    _add_observer(builder, "ObsPhyAck", "phy_command_pending", "!phy_command_pending", "D_phy_ack", "c_obs_ack")


def _add_obs_queue_critical(builder: UppaalXmlBuilder) -> None:
    _add_observer(builder, "ObsQueueCritical", "queueClass == Q_CRIT", "queueClass != Q_CRIT || mac_report_sent || scheduleMode == SCH_COMM || scheduleMode == SCH_CONSTRAINED", "D_queue_crit", "c_obs_queue")


def _add_obs_sensing_critical(builder: UppaalXmlBuilder) -> None:
    _add_observer(builder, "ObsSensingCritical", "sensingDemand == SENS_CRITICAL", "scheduleMode == SCH_SENS || scheduleMode == SCH_JOINT || scheduleMode == SCH_CONSTRAINED || mac_report_sent", "D_sched", "c_obs_sensing")


def _add_obs_buffer_overflow(builder: UppaalXmlBuilder) -> None:
    _add_observer(builder, "ObsBufferOverflow", "bufferClass == B_OVERFLOW", "mac_report_sent || bufferClass != B_OVERFLOW", "D_buf_report", "c_obs_buf")


def _add_obs_mac_report_freshness(builder: UppaalXmlBuilder) -> None:
    _add_observer(builder, "ObsMacReportFreshness", "mac_report_pending", "mac_report_sent || !mac_report_pending", "D_mac_report", "c_obs_report")


def _add_observer(builder: UppaalXmlBuilder, name: str, trigger: str, response: str, deadline: str, clock: str) -> None:
    t = builder.template(f"Template_{name}", "Idle", [("Idle", None), ("Wait", None), ("Violation", None)])
    builder.add_transition(t, "Idle", "Wait", guard=trigger, assignment=f"{clock} = 0")
    builder.add_transition(t, "Wait", "Idle", guard=f"({response}) && {clock} <= {deadline}")
    builder.add_transition(t, "Wait", "Violation", guard=f"{clock} > {deadline}")


def _system_declaration(*, include_observers: bool) -> str:
    instances = ["A_SCH", "A_Q", "A_BUF", "A_RSRC", "A_MAC_AGG", "A_ENV_MAC"]
    if include_observers:
        instances.extend(["ObsPhyAck", "ObsQueueCritical", "ObsSensingCritical", "ObsBufferOverflow", "ObsMacReportFreshness"])
    declarations = [f"{name} = Template_{name}();" for name in instances]
    return "\n".join(declarations) + "\n\nsystem " + ", ".join(instances) + ";\n"


def _safe(name: str) -> str:
    return re.sub(r"\W+", "_", name)


def _avoid_label_collisions(
    geometry: TransitionGeometry,
    label_kinds: list[str],
    occupied: set[tuple[int, int]],
) -> TransitionGeometry:
    if not label_kinds:
        return geometry
    labels = dict(geometry.labels)
    shift = 0
    while any((labels[kind].x, labels[kind].y) in occupied for kind in label_kinds):
        shift += 1
        dx = 34 * shift
        dy = 96 * shift
        labels = {
            kind: Point(point.x + dx, point.y + dy)
            for kind, point in geometry.labels.items()
        }
    return TransitionGeometry(labels=labels, nails=geometry.nails)


def _wrap_assignment(text: str) -> str:
    return wrap_label(text)
