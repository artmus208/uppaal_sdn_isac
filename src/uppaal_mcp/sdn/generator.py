from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass

from .alpha import default_profile
from .defaults import build_default_contract
from .ir import PropertySpec, SdnContractModel
from .layout import generate_layout_maps, label_point, location_positions, nails_for, normalize_layout_mode, validate_generated_layout


@dataclass(frozen=True)
class GeneratedSdnModel:
    model_xml: str
    queries: str
    contract: dict
    profile: dict
    layout: str
    model_map: str
    template_map: str
    channels_map: str
    policy_map: str
    interface_map: str
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

    def declaration(self, text: str) -> None:
        ET.SubElement(self.root, "declaration").text = text

    def template(self, name: str, initial: str, locations: list[tuple[str, str | None]]) -> ET.Element:
        template = ET.SubElement(self.root, "template")
        ET.SubElement(template, "name").text = name
        points = location_positions(name, [item[0] for item in locations], self.layout)
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
        return template

    def add_transition(self, template: ET.Element, source: str, target: str, *, guard: str | None = None, sync: str | None = None, assignment: str | None = None, comment: str | None = None) -> None:
        ids = self.location_ids[id(template)]
        points = self.points[id(template)]
        count_key = (id(template), source, target)
        index = self.edge_counts.get(count_key, 0)
        self.edge_counts[count_key] = index + 1
        src = points[source]
        dst = points[target]
        transition = ET.SubElement(template, "transition")
        ET.SubElement(transition, "source", {"ref": ids[source]})
        ET.SubElement(transition, "target", {"ref": ids[target]})
        if guard:
            pt = label_point(src, dst, "guard", index)
            ET.SubElement(transition, "label", {"kind": "guard", "x": str(pt.x), "y": str(pt.y)}).text = guard
        if sync:
            pt = label_point(src, dst, "synchronisation", index)
            ET.SubElement(transition, "label", {"kind": "synchronisation", "x": str(pt.x), "y": str(pt.y)}).text = sync
        if assignment:
            pt = label_point(src, dst, "assignment", index)
            ET.SubElement(transition, "label", {"kind": "assignment", "x": str(pt.x), "y": str(pt.y)}).text = _wrap_assignment(assignment)
        if comment:
            pt = label_point(src, dst, "comments", index)
            ET.SubElement(transition, "label", {"kind": "comments", "x": str(pt.x), "y": str(pt.y)}).text = comment
        for nail in nails_for(src, dst, source, target, index):
            ET.SubElement(transition, "nail", {"x": str(nail.x), "y": str(nail.y)})

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
    contract: SdnContractModel | None = None,
    profile: dict | None = None,
    *,
    include_observers: bool = True,
    debug_counters: bool = True,
    include_negative_scenarios: bool = False,
    mode: str | None = None,
    layout: str | None = None,
) -> GeneratedSdnModel:
    model = contract or build_default_contract()
    profile = profile or default_profile()
    layout_mode = normalize_layout_mode(layout)
    mode_name, include_observers, debug_counters, include_negative_scenarios, include_sec, open_system = _normalize_generation_mode(
        mode,
        include_observers=include_observers,
        debug_counters=debug_counters,
        include_negative_scenarios=include_negative_scenarios,
    )
    builder = UppaalXmlBuilder(layout=layout_mode)
    builder.declaration(_declarations(profile, mode_name=mode_name, layout_mode=layout_mode, include_negative_scenarios=include_negative_scenarios))
    _add_a_mon(builder)
    _add_a_risk(builder)
    _add_a_policy(builder)
    _add_a_rule(builder)
    _add_a_rec(builder)
    _add_a_sdn_agg(builder)
    if not open_system:
        _add_a_env_sdn(builder)
    if include_sec:
        _add_a_sec(builder)
    if include_observers:
        _add_obs_rule_miss(builder)
        _add_obs_recovery(builder)
        _add_obs_admission(builder)
        _add_obs_stale_telemetry(builder)
        _add_obs_command_ack(builder)
        _add_obs_sensing_decision(builder)
    builder.system(_system_declaration(include_observers=include_observers, include_sec=include_sec, open_system=open_system))
    model_xml = builder.to_xml()
    maps = generate_layout_maps(model.to_dict(), model_xml=model_xml, layout=layout_mode)
    return GeneratedSdnModel(
        model_xml=model_xml,
        queries=generate_queries(model, include_observers=include_observers, debug_counters=debug_counters, open_system=open_system),
        contract=model.to_dict(),
        profile=profile,
        layout=layout_mode,
        model_map=maps["model_map.md"],
        template_map=maps["template_map.md"],
        channels_map=maps["channels_map.md"],
        policy_map=maps["policy_map.md"],
        interface_map=maps["interface_map.md"],
        layout_validation=validate_generated_layout(model_xml).to_dict(),
        generation_mode=mode_name,
        include_negative_scenarios=include_negative_scenarios,
        system_mode="open" if open_system else "closed",
    )


def generate_queries(contract: SdnContractModel | None = None, *, include_observers: bool = True, debug_counters: bool = True, open_system: bool = False) -> str:
    model = contract or build_default_contract()
    queries: list[PropertySpec] = []
    for item in model.properties:
        if item.name.startswith("Obs") and not include_observers:
            continue
        if open_system and item.query == "A[] not deadlock":
            continue
        queries.append(item)
    if debug_counters:
        queries.append(PropertySpec("policy_totality", "A[] policy_enabled_count >= 1", "debug", "at least one SDN policy/fallback is enabled"))
    return "\n".join(item.query for item in queries) + "\n"


def _normalize_generation_mode(mode: str | None, *, include_observers: bool, debug_counters: bool, include_negative_scenarios: bool) -> tuple[str, bool, bool, bool, bool, bool]:
    include_sec = False
    open_system = False
    if mode is None:
        if include_negative_scenarios:
            return "with_negative_scenarios", include_observers, debug_counters, True, False, False
        if include_observers and debug_counters:
            return "with_observers", True, True, False, False, False
        if debug_counters:
            return "with_debug_counters", include_observers, True, False, False, False
        if not include_observers:
            return "minimal", False, False, False, False, False
        return "custom", include_observers, debug_counters, include_negative_scenarios, False, False
    normalized = mode.strip().lower()
    if normalized == "minimal":
        return "minimal", False, False, False, False, False
    if normalized == "with_observers":
        return "with_observers", True, debug_counters, include_negative_scenarios, False, False
    if normalized == "with_debug_counters":
        return "with_debug_counters", include_observers, True, include_negative_scenarios, False, False
    if normalized == "with_negative_scenarios":
        return "with_negative_scenarios", include_observers, debug_counters, True, False, False
    if normalized == "with_optional_sec":
        return "with_optional_sec", include_observers, debug_counters, include_negative_scenarios, True, False
    if normalized == "open_system":
        return "open_system", include_observers, debug_counters, include_negative_scenarios, False, True
    raise ValueError("Unsupported SDN mode. Use minimal, with_observers, with_debug_counters, with_negative_scenarios, with_optional_sec, or open_system.")


def _declarations(profile: dict, *, mode_name: str, layout_mode: str, include_negative_scenarios: bool) -> str:
    d = profile.get("deadlines", {})
    lines = [
        "// Generated from SDN/RIC contract IR. Raw metrics, probabilities and optimization scores stay outside timed automata.",
        f"// Generation mode: {mode_name}.",
        f"// Layout mode: {layout_mode}.",
        "// Negative scenarios are emitted by benchmark mutations." if include_negative_scenarios else "// Negative scenarios disabled for this generated model.",
        f"const int D_mon = {int(d.get('D_mon', 5))};",
        f"const int D_decision = {int(d.get('D_decision', 5))};",
        f"const int D_rule_install = {int(d.get('D_rule_install', 8))};",
        f"const int D_rule_ack = {int(d.get('D_rule_ack', 5))};",
        f"const int D_ctrl_ack = {int(d.get('D_ctrl_ack', 5))};",
        f"const int D_recovery = {int(d.get('D_recovery', 20))};",
        f"const int D_rollback = {int(d.get('D_rollback', 10))};",
        f"const int D_admission = {int(d.get('D_admission', 15))};",
        f"const int D_sec_ack = {int(d.get('D_sec_ack', 10))};",
        "",
        "clock c_mon, c_dec, c_rule, c_ctrl_ack, c_rec, c_rollback, c_admission, c_sec_ack;",
        "clock c_obs_rule, c_obs_rec, c_obs_admission, c_obs_cmd, c_obs_sensing;",
        "",
        "broadcast chan mac_report, phy_kpi_report, service_request;",
        "broadcast chan service_accept, service_degraded, service_reject;",
        "chan rule_miss, link_failure, node_failure, ack;",
        "chan sdn_policy_cmd, flow_mod, forward_cmd, drop_report;",
        "chan failure_report, timeout_report, rollback_cmd;",
        "",
        "typedef int[0,2] TelemetryClass_t;",
        "const TelemetryClass_t TEL_FRESH=0, TEL_STALE=1, TEL_MISSING=2;",
        "typedef int[0,3] RiskClass_t;",
        "const RiskClass_t RISK_LOW=0, RISK_MED=1, RISK_HIGH=2, RISK_CRIT=3;",
        "typedef int[0,5] PolicyClass_t;",
        "const PolicyClass_t POL_NORMAL=0, POL_SENS_BOOST=1, POL_COMM_PRIO=2, POL_CONSTRAINED=3, POL_REROUTE=4, POL_REJECT=5;",
        "typedef int[0,5] RuleClass_t;",
        "const RuleClass_t RULE_OK=0, RULE_MISS=1, RULE_PENDING=2, RULE_ACKED=3, RULE_TIMEOUT=4, RULE_DROP=5;",
        "typedef int[0,4] RecoveryClass_t;",
        "const RecoveryClass_t REC_STABLE=0, REC_STANDBY=1, REC_REEMBED=2, REC_ROLLBACK=3, REC_FAILED=4;",
        "typedef int[0,2] SliceClass_t;",
        "const SliceClass_t SLICE_OK=0, SLICE_WARN=1, SLICE_VIOLATED=2;",
        "typedef int[0,3] ServiceImpact_t;",
        "const ServiceImpact_t IMPACT_NONE=0, IMPACT_DEGRADED=1, IMPACT_REJECTED=2, IMPACT_FAILED=3;",
        "typedef int[0,6] SdnReason_t;",
        "const SdnReason_t SDN_NONE=0, SDN_STALE_TELEMETRY=1, SDN_RULE_TIMEOUT=2, SDN_RECOVERY_FAILED=3, SDN_RESOURCE_LIMITED=4, SDN_SENSING_FAILURE=5, SDN_POLICY_REJECT=6;",
        "",
        "TelemetryClass_t telemetryClass = TEL_FRESH;",
        "RiskClass_t riskClass = RISK_LOW;",
        "PolicyClass_t policyClass = POL_NORMAL;",
        "RuleClass_t ruleClass = RULE_OK;",
        "RecoveryClass_t recoveryClass = REC_STABLE;",
        "SliceClass_t sliceClass = SLICE_OK;",
        "ServiceImpact_t serviceImpact = IMPACT_NONE;",
        "SdnReason_t sdnReason = SDN_NONE;",
        "bool rule_miss_pending = false;",
        "bool link_failure_pending = false;",
        "bool node_failure_pending = false;",
        "bool sensing_degradation_pending = false;",
        "bool service_request_pending = false;",
        "bool command_pending = false;",
        "bool optimistic_reconfig = false;",
        "bool standby_available = false;",
        "bool alternative_config_exists = false;",
        "bool lower_ack_received = false;",
        "bool failure_report_sent = false;",
        "int[0,6] policy_enabled_count = 1;",
        "",
        "bool telemetry_bad() { return telemetryClass == TEL_STALE || telemetryClass == TEL_MISSING; }",
        "bool gPolReject() { return riskClass == RISK_CRIT || sliceClass == SLICE_VIOLATED || recoveryClass == REC_FAILED; }",
        "bool gPolConstrained() { return telemetry_bad() || riskClass == RISK_HIGH || sliceClass == SLICE_WARN; }",
        "bool gPolReroute() { return (ruleClass == RULE_MISS || link_failure_pending || node_failure_pending) && (standby_available || alternative_config_exists) && !telemetry_bad(); }",
        "bool gPolSensingBoost() { return sensing_degradation_pending && !telemetry_bad() && riskClass != RISK_CRIT; }",
        "bool gPolCommPrio() { return service_request_pending && sliceClass != SLICE_VIOLATED && !telemetry_bad(); }",
        "bool reconfig_allowed() { return telemetryClass == TEL_FRESH && policyClass != POL_CONSTRAINED && policyClass != POL_REJECT; }",
        "void update_policy_counter() { policy_enabled_count = (gPolReject()?1:0) + (gPolConstrained()?1:0) + (gPolReroute()?1:0) + (gPolSensingBoost()?1:0) + (gPolCommPrio()?1:0) + 1; }",
        "void classify_risk() { if (recoveryClass == REC_FAILED || sliceClass == SLICE_VIOLATED || telemetryClass == TEL_MISSING) riskClass = RISK_CRIT; else if (ruleClass == RULE_TIMEOUT || sensing_degradation_pending) riskClass = RISK_HIGH; else if (telemetryClass == TEL_STALE || sliceClass == SLICE_WARN) riskClass = RISK_MED; else riskClass = RISK_LOW; }",
        "void select_sdn_policy() { update_policy_counter(); optimistic_reconfig = false; if (gPolReject()) { policyClass = POL_REJECT; serviceImpact = IMPACT_REJECTED; sdnReason = SDN_POLICY_REJECT; } else if (telemetry_bad()) { policyClass = POL_CONSTRAINED; serviceImpact = IMPACT_DEGRADED; sdnReason = SDN_STALE_TELEMETRY; } else if (gPolReroute()) { policyClass = POL_REROUTE; serviceImpact = IMPACT_NONE; sdnReason = SDN_NONE; } else if (gPolSensingBoost()) { policyClass = POL_SENS_BOOST; serviceImpact = IMPACT_DEGRADED; sdnReason = SDN_SENSING_FAILURE; } else if (gPolCommPrio()) { policyClass = POL_COMM_PRIO; serviceImpact = IMPACT_NONE; sdnReason = SDN_NONE; } else { policyClass = POL_NORMAL; serviceImpact = IMPACT_NONE; sdnReason = SDN_NONE; } }",
    ]
    return "\n".join(lines)


def _add_a_mon(builder: UppaalXmlBuilder) -> None:
    t = builder.template("Template_A_MON", "MonitorIdle", [("MonitorIdle", None), ("CollectReports", "c_mon <= D_mon"), ("TelemetryFresh", None), ("TelemetryStale", None), ("TelemetryMissing", None)])
    builder.add_transition(t, "MonitorIdle", "CollectReports", sync="mac_report?", assignment="c_mon = 0, telemetryClass = TEL_FRESH", comment="MAC report observed")
    builder.add_transition(t, "MonitorIdle", "CollectReports", sync="phy_kpi_report?", assignment="c_mon = 0, telemetryClass = TEL_FRESH", comment="PHY report observed")
    builder.add_transition(t, "CollectReports", "TelemetryFresh", guard="c_mon <= D_mon && telemetryClass == TEL_FRESH")
    builder.add_transition(t, "CollectReports", "TelemetryStale", guard="telemetryClass == TEL_STALE || c_mon == D_mon", assignment="telemetryClass = TEL_STALE, optimistic_reconfig = false")
    builder.add_transition(t, "CollectReports", "TelemetryMissing", guard="telemetryClass == TEL_MISSING", assignment="optimistic_reconfig = false")
    builder.add_transition(t, "TelemetryFresh", "MonitorIdle")
    builder.add_transition(t, "TelemetryStale", "MonitorIdle")
    builder.add_transition(t, "TelemetryMissing", "MonitorIdle")


def _add_a_risk(builder: UppaalXmlBuilder) -> None:
    t = builder.template("Template_A_RISK", "RiskLow", [("RiskLow", None), ("RiskMedium", None), ("RiskHigh", None), ("RiskCritical", None)])
    for source in ("RiskLow", "RiskMedium", "RiskHigh", "RiskCritical"):
        builder.add_transition(t, source, "RiskCritical", guard="recoveryClass == REC_FAILED || sliceClass == SLICE_VIOLATED || telemetryClass == TEL_MISSING", assignment="classify_risk()")
        builder.add_transition(t, source, "RiskHigh", guard="ruleClass == RULE_TIMEOUT || sensing_degradation_pending", assignment="classify_risk()")
        builder.add_transition(t, source, "RiskMedium", guard="telemetryClass == TEL_STALE || sliceClass == SLICE_WARN", assignment="classify_risk()")
        builder.add_transition(t, source, "RiskLow", guard="telemetryClass == TEL_FRESH && sliceClass == SLICE_OK && recoveryClass != REC_FAILED && ruleClass != RULE_TIMEOUT && !sensing_degradation_pending", assignment="classify_risk()")


def _add_a_policy(builder: UppaalXmlBuilder) -> None:
    t = builder.template("Template_A_POLICY", "PolicyIdle", [("PolicyIdle", None), ("Evaluate", "c_dec <= D_decision"), ("NormalMode", None), ("SensingBoostMode", None), ("CommPriorityMode", None), ("ConstrainedMode", None), ("RejectByPolicy", None)])
    builder.add_transition(t, "PolicyIdle", "Evaluate", sync="service_request?", assignment="service_request_pending = true, c_admission = 0, c_dec = 0", comment="service admission")
    builder.add_transition(t, "PolicyIdle", "Evaluate", sync="mac_report?", assignment="sensing_degradation_pending = true, c_dec = 0", comment="MAC/ISAC degradation")
    builder.add_transition(t, "PolicyIdle", "Evaluate", sync="phy_kpi_report?", assignment="c_dec = 0", comment="PHY KPI update")
    builder.add_transition(t, "Evaluate", "RejectByPolicy", guard="gPolReject()", sync="service_reject!", assignment="select_sdn_policy(), service_request_pending = false, optimistic_reconfig = false")
    builder.add_transition(t, "Evaluate", "ConstrainedMode", guard="!gPolReject() && gPolConstrained()", sync="service_degraded!", assignment="select_sdn_policy(), service_request_pending = false, optimistic_reconfig = false")
    builder.add_transition(t, "Evaluate", "SensingBoostMode", guard="!gPolReject() && !gPolConstrained() && gPolSensingBoost()", sync="service_degraded!", assignment="select_sdn_policy(), command_pending = true")
    builder.add_transition(t, "Evaluate", "CommPriorityMode", guard="!gPolReject() && !gPolConstrained() && !gPolSensingBoost() && gPolCommPrio()", sync="service_accept!", assignment="select_sdn_policy(), service_request_pending = false, command_pending = true")
    builder.add_transition(t, "Evaluate", "NormalMode", guard="!gPolReject() && !gPolConstrained() && !gPolSensingBoost() && !gPolCommPrio()", sync="service_accept!", assignment="select_sdn_policy(), service_request_pending = false")
    for loc in ("NormalMode", "SensingBoostMode", "CommPriorityMode", "ConstrainedMode", "RejectByPolicy"):
        builder.add_transition(t, loc, "PolicyIdle")


def _add_a_rule(builder: UppaalXmlBuilder) -> None:
    t = builder.template("Template_A_RULE", "RuleStable", [("RuleStable", None), ("RuleMiss", None), ("RuleInstallPending", "c_rule <= D_rule_install"), ("RuleInstalled", None), ("RuleAcked", None), ("RuleTimeout", None), ("RuleDropReason", None)])
    builder.add_transition(t, "RuleStable", "RuleMiss", sync="rule_miss?", assignment="ruleClass = RULE_MISS, rule_miss_pending = true, c_rule = 0")
    builder.add_transition(t, "RuleMiss", "RuleInstallPending", guard="gPolReroute()", sync="flow_mod!", assignment="ruleClass = RULE_PENDING, optimistic_reconfig = true")
    builder.add_transition(t, "RuleMiss", "RuleDropReason", guard="gPolReject() || !reconfig_allowed()", sync="drop_report!", assignment="ruleClass = RULE_DROP, rule_miss_pending = false, optimistic_reconfig = false")
    builder.add_transition(t, "RuleInstallPending", "RuleInstalled", guard="c_rule <= D_rule_install", sync="forward_cmd!")
    builder.add_transition(t, "RuleInstalled", "RuleAcked", guard="c_rule <= D_rule_ack", sync="ack?", assignment="ruleClass = RULE_ACKED, rule_miss_pending = false, optimistic_reconfig = false")
    builder.add_transition(t, "RuleInstallPending", "RuleTimeout", guard="c_rule == D_rule_install", sync="timeout_report!", assignment="ruleClass = RULE_TIMEOUT, sdnReason = SDN_RULE_TIMEOUT, serviceImpact = IMPACT_DEGRADED, rule_miss_pending = false, optimistic_reconfig = false")
    builder.add_transition(t, "RuleInstalled", "RuleTimeout", guard="c_rule == D_rule_install", sync="timeout_report!", assignment="ruleClass = RULE_TIMEOUT, sdnReason = SDN_RULE_TIMEOUT, serviceImpact = IMPACT_DEGRADED, rule_miss_pending = false, optimistic_reconfig = false")
    builder.add_transition(t, "RuleAcked", "RuleStable", guard="ruleClass == RULE_ACKED")
    builder.add_transition(t, "RuleTimeout", "RuleStable")
    builder.add_transition(t, "RuleDropReason", "RuleStable")


def _add_a_rec(builder: UppaalXmlBuilder) -> None:
    t = builder.template("Template_A_REC", "StableConfig", [("StableConfig", None), ("FailureDetected", None), ("StandbySwitch", "c_rec <= D_recovery"), ("ReactiveReembedding", "c_rec <= D_recovery"), ("Rollback", "c_rollback <= D_rollback"), ("RecoveryFailed", None)])
    builder.add_transition(t, "StableConfig", "FailureDetected", sync="link_failure?", assignment="link_failure_pending = true, recoveryClass = REC_STANDBY, c_rec = 0")
    builder.add_transition(t, "StableConfig", "FailureDetected", sync="node_failure?", assignment="node_failure_pending = true, recoveryClass = REC_REEMBED, c_rec = 0")
    builder.add_transition(t, "FailureDetected", "StandbySwitch", guard="standby_available && reconfig_allowed()", sync="sdn_policy_cmd!", assignment="command_pending = true, optimistic_reconfig = true")
    builder.add_transition(t, "FailureDetected", "ReactiveReembedding", guard="alternative_config_exists && reconfig_allowed()", sync="flow_mod!", assignment="command_pending = true, optimistic_reconfig = true")
    builder.add_transition(t, "FailureDetected", "Rollback", guard="!standby_available && !alternative_config_exists || !reconfig_allowed()", sync="rollback_cmd!", assignment="recoveryClass = REC_ROLLBACK, c_rollback = 0, optimistic_reconfig = false")
    builder.add_transition(t, "StandbySwitch", "StableConfig", guard="c_rec <= D_recovery", sync="ack?", assignment="recoveryClass = REC_STABLE, link_failure_pending = false, node_failure_pending = false, optimistic_reconfig = false")
    builder.add_transition(t, "ReactiveReembedding", "StableConfig", guard="c_rec <= D_recovery", sync="ack?", assignment="recoveryClass = REC_STABLE, link_failure_pending = false, node_failure_pending = false, optimistic_reconfig = false")
    builder.add_transition(t, "StandbySwitch", "Rollback", guard="c_rec == D_recovery", sync="rollback_cmd!", assignment="recoveryClass = REC_ROLLBACK, c_rollback = 0, optimistic_reconfig = false")
    builder.add_transition(t, "ReactiveReembedding", "Rollback", guard="c_rec == D_recovery", sync="rollback_cmd!", assignment="recoveryClass = REC_ROLLBACK, c_rollback = 0, optimistic_reconfig = false")
    builder.add_transition(t, "Rollback", "StableConfig", guard="c_rollback <= D_rollback", sync="ack?", assignment="recoveryClass = REC_STABLE, link_failure_pending = false, node_failure_pending = false")
    builder.add_transition(t, "Rollback", "RecoveryFailed", guard="c_rollback == D_rollback", sync="failure_report!", assignment="recoveryClass = REC_FAILED, sdnReason = SDN_RECOVERY_FAILED, serviceImpact = IMPACT_FAILED, failure_report_sent = true, link_failure_pending = false, node_failure_pending = false")


def _add_a_sdn_agg(builder: UppaalXmlBuilder) -> None:
    t = builder.template("Template_A_SDN_AGG", "CommandBuild", [("CommandBuild", None), ("CommandSent", None), ("AwaitAck", "c_ctrl_ack <= D_ctrl_ack"), ("Acked", None), ("CommandTimeout", None)])
    builder.add_transition(t, "CommandBuild", "CommandSent", guard="command_pending", sync="sdn_policy_cmd!", assignment="c_ctrl_ack = 0")
    builder.add_transition(t, "CommandSent", "AwaitAck")
    builder.add_transition(t, "AwaitAck", "Acked", guard="c_ctrl_ack <= D_ctrl_ack", sync="ack?", assignment="command_pending = false, lower_ack_received = true")
    builder.add_transition(t, "AwaitAck", "CommandTimeout", guard="c_ctrl_ack == D_ctrl_ack", sync="timeout_report!", assignment="command_pending = false, lower_ack_received = false, sdnReason = SDN_RULE_TIMEOUT")
    builder.add_transition(t, "Acked", "CommandBuild")
    builder.add_transition(t, "CommandTimeout", "CommandBuild")


def _add_a_env_sdn(builder: UppaalXmlBuilder) -> None:
    t = builder.template("Template_A_ENV_SDN", "EnvIdle", [("EnvIdle", None)])
    builder.add_transition(t, "EnvIdle", "EnvIdle", sync="mac_report!", assignment="telemetryClass = TEL_FRESH")
    builder.add_transition(t, "EnvIdle", "EnvIdle", sync="phy_kpi_report!", assignment="telemetryClass = TEL_FRESH")
    builder.add_transition(t, "EnvIdle", "EnvIdle", sync="service_request!", assignment="service_request_pending = true")
    builder.add_transition(t, "EnvIdle", "EnvIdle", sync="rule_miss!")
    builder.add_transition(t, "EnvIdle", "EnvIdle", sync="link_failure!", assignment="standby_available = true")
    builder.add_transition(t, "EnvIdle", "EnvIdle", sync="node_failure!", assignment="alternative_config_exists = true")
    builder.add_transition(t, "EnvIdle", "EnvIdle", sync="ack!")
    for ch in ("sdn_policy_cmd", "flow_mod", "forward_cmd", "drop_report", "failure_report", "timeout_report", "rollback_cmd"):
        builder.add_transition(t, "EnvIdle", "EnvIdle", sync=f"{ch}?")
    builder.add_transition(t, "EnvIdle", "EnvIdle", assignment="telemetryClass = TEL_STALE, optimistic_reconfig = false")
    builder.add_transition(t, "EnvIdle", "EnvIdle", assignment="telemetryClass = TEL_MISSING, optimistic_reconfig = false")
    builder.add_transition(t, "EnvIdle", "EnvIdle", assignment="sliceClass = SLICE_VIOLATED")
    builder.add_transition(t, "EnvIdle", "EnvIdle", assignment="sensing_degradation_pending = true")
    builder.add_transition(t, "EnvIdle", "EnvIdle", assignment="standby_available = true, alternative_config_exists = false")
    builder.add_transition(t, "EnvIdle", "EnvIdle", assignment="standby_available = false, alternative_config_exists = true")


def _add_a_sec(builder: UppaalXmlBuilder) -> None:
    t = builder.template("Template_A_SEC", "SecIdle", [("SecIdle", None), ("ThreatObserved", "c_sec_ack <= D_sec_ack"), ("SecurityReport", None), ("SecurityFailure", None)])
    builder.add_transition(t, "SecIdle", "ThreatObserved", assignment="c_sec_ack = 0")
    builder.add_transition(t, "ThreatObserved", "SecurityReport", guard="c_sec_ack <= D_sec_ack", sync="failure_report!")
    builder.add_transition(t, "ThreatObserved", "SecurityFailure", guard="c_sec_ack == D_sec_ack")
    builder.add_transition(t, "SecurityReport", "SecIdle")
    builder.add_transition(t, "SecurityFailure", "SecIdle")


def _add_obs_rule_miss(builder: UppaalXmlBuilder) -> None:
    _add_observer(builder, "ObsRuleMiss", "rule_miss_pending", "ruleClass == RULE_ACKED || ruleClass == RULE_DROP || ruleClass == RULE_TIMEOUT", "D_rule_install", "c_obs_rule")


def _add_obs_recovery(builder: UppaalXmlBuilder) -> None:
    _add_observer(builder, "ObsRecovery", "link_failure_pending || node_failure_pending", "recoveryClass == REC_STABLE || recoveryClass == REC_FAILED", "D_recovery + D_rollback", "c_obs_rec")


def _add_obs_admission(builder: UppaalXmlBuilder) -> None:
    _add_observer(builder, "ObsAdmission", "service_request_pending", "serviceImpact == IMPACT_NONE || serviceImpact == IMPACT_DEGRADED || serviceImpact == IMPACT_REJECTED", "D_admission", "c_obs_admission")


def _add_obs_stale_telemetry(builder: UppaalXmlBuilder) -> None:
    t = builder.template("Template_ObsStaleTelemetry", "Safe", [("Safe", None), ("Violation", None)])
    builder.add_transition(t, "Safe", "Violation", guard="(telemetryClass == TEL_STALE || telemetryClass == TEL_MISSING) && optimistic_reconfig")


def _add_obs_command_ack(builder: UppaalXmlBuilder) -> None:
    _add_observer(builder, "ObsCommandAck", "command_pending", "!command_pending", "D_ctrl_ack", "c_obs_cmd")


def _add_obs_sensing_decision(builder: UppaalXmlBuilder) -> None:
    _add_observer(builder, "ObsSensingDecision", "sensing_degradation_pending", "policyClass == POL_SENS_BOOST || policyClass == POL_CONSTRAINED || policyClass == POL_REJECT", "D_decision", "c_obs_sensing")


def _add_observer(builder: UppaalXmlBuilder, name: str, trigger: str, response: str, deadline: str, clock: str) -> None:
    t = builder.template(f"Template_{name}", "Idle", [("Idle", None), ("Wait", None), ("Violation", None)])
    builder.add_transition(t, "Idle", "Wait", guard=trigger, assignment=f"{clock} = 0")
    builder.add_transition(t, "Wait", "Idle", guard=response)
    builder.add_transition(t, "Wait", "Violation", guard=f"{clock} > {deadline}")


def _system_declaration(*, include_observers: bool, include_sec: bool, open_system: bool) -> str:
    instances = ["A_MON", "A_RISK", "A_POLICY", "A_RULE", "A_REC", "A_SDN_AGG"]
    if not open_system:
        instances.append("A_ENV_SDN")
    if include_sec:
        instances.append("A_SEC")
    if include_observers:
        instances.extend(["ObsRuleMiss", "ObsRecovery", "ObsAdmission", "ObsStaleTelemetry", "ObsCommandAck", "ObsSensingDecision"])
    lines = [f"{name} = Template_{name}();" for name in instances]
    lines.append(f"system {', '.join(instances)};")
    return "\n".join(lines)


def _wrap_assignment(text: str, width: int = 96) -> str:
    if len(text) <= width:
        return text
    parts = [part.strip() for part in text.split(",")]
    lines = []
    current = ""
    for part in parts:
        candidate = part if not current else f"{current}, {part}"
        if len(candidate) > width:
            if current:
                lines.append(current + ",")
            current = part
        else:
            current = candidate
    if current:
        lines.append(current)
    return "\n".join(lines)


def _safe(name: str) -> str:
    return name.replace("Template_", "").replace(" ", "_")
