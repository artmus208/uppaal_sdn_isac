from __future__ import annotations

import html
import re
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from typing import Iterable

from .alpha import default_profile, generate_uppaal_declarations
from .defaults import build_default_contract
from .ir import PhyContractModel, PropertySpec


@dataclass(frozen=True)
class GeneratedPhyModel:
    model_xml: str
    queries: str
    contract: dict
    profile: dict
    generation_mode: str = "with_observers"
    include_negative_scenarios: bool = False
    system_mode: str = "closed"
    include_extended_observers: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


class UppaalXmlBuilder:
    def __init__(self) -> None:
        self.root = ET.Element("nta")
        self.template_index = 0

    def declaration(self, text: str) -> None:
        ET.SubElement(self.root, "declaration").text = text

    def template(self, name: str, initial: str, locations: list[tuple[str, str | None]]) -> ET.Element:
        template = ET.SubElement(self.root, "template")
        ET.SubElement(template, "name").text = name
        location_ids: dict[str, str] = {}
        x = 0
        for index, (location_name, invariant) in enumerate(locations):
            loc_id = f"{_safe(name)}_{index}"
            location_ids[location_name] = loc_id
            location = ET.SubElement(template, "location", {"id": loc_id, "x": str(x), "y": "0"})
            ET.SubElement(location, "name", {"x": str(x - 20), "y": "-30"}).text = location_name
            if invariant:
                ET.SubElement(location, "label", {"kind": "invariant", "x": str(x - 20), "y": "20"}).text = invariant
            x += 180
        ET.SubElement(template, "init", {"ref": location_ids[initial]})
        template.attrib["_location_ids"] = repr(location_ids)
        return template

    def add_transition(
        self,
        template: ET.Element,
        source: str,
        target: str,
        *,
        guard: str | None = None,
        sync: str | None = None,
        assignment: str | None = None,
    ) -> None:
        location_ids = eval(template.attrib["_location_ids"], {"__builtins__": {}})
        transition = ET.SubElement(template, "transition")
        ET.SubElement(transition, "source", {"ref": location_ids[source]})
        ET.SubElement(transition, "target", {"ref": location_ids[target]})
        y = -60
        if guard:
            ET.SubElement(transition, "label", {"kind": "guard", "x": "0", "y": str(y)}).text = guard
            y += 20
        if sync:
            ET.SubElement(transition, "label", {"kind": "synchronisation", "x": "0", "y": str(y)}).text = sync
            y += 20
        if assignment:
            ET.SubElement(transition, "label", {"kind": "assignment", "x": "0", "y": str(y)}).text = assignment

    def system(self, text: str) -> None:
        ET.SubElement(self.root, "system").text = text

    def to_xml(self) -> str:
        for template in self.root.findall("template"):
            template.attrib.pop("_location_ids", None)
        ET.indent(self.root, space="  ")
        xml_body = ET.tostring(self.root, encoding="unicode")
        return (
            '<?xml version="1.0" encoding="utf-8"?>\n'
            '<!DOCTYPE nta PUBLIC "-//Uppaal Team//DTD Flat System 1.6//EN" '
            '"http://www.it.uu.se/research/group/darts/uppaal/flat-1_6.dtd">\n'
            f"{xml_body}\n"
        )


def generate_uppaal_model(
    contract: PhyContractModel | None = None,
    profile: dict | None = None,
    *,
    include_observers: bool = True,
    debug_counters: bool = True,
    include_negative_scenarios: bool = False,
    mode: str | None = None,
) -> GeneratedPhyModel:
    model = contract or build_default_contract()
    profile = profile or default_profile()
    (
        mode_name,
        include_observers,
        debug_counters,
        include_negative_scenarios,
        include_environment,
        include_extended_observers,
    ) = _normalize_generation_mode(
        mode,
        include_observers=include_observers,
        debug_counters=debug_counters,
        include_negative_scenarios=include_negative_scenarios,
    )
    builder = UppaalXmlBuilder()
    builder.declaration(_declarations(model, profile, debug_counters=debug_counters, mode_name=mode_name, include_negative_scenarios=include_negative_scenarios))
    _add_a_ch(builder)
    _add_a_sig(builder)
    _add_a_bm(builder)
    _add_a_sq(builder)
    _add_a_ph(builder)
    if include_environment:
        _add_env_ch(builder)
        _add_env_target(builder)
        _add_env_mac(builder)
        _add_env_net(builder)
    if include_observers:
        _add_observer(builder, "ObsSenseReport", "sensing_degraded?", ["phy_kpi_report?"], "D_report", "c_obs_sense")
        _add_observer(builder, "ObsFreshness", "aos_ctrl_expired?", ["sensing_report?"], "D_sense", "c_obs_fresh")
        _add_observer(builder, "ObsBeamRecovery", "recovery_start?", ["beam_restored?", "handover_hint?", "beam_failure?"], "D_BM", "c_obs_beam")
    if include_extended_observers:
        _add_pending_flag_observer(builder, "ObsChannelReport", "channel_report_pending", "channel_report?", "D_meas", "c_obs_channel")
        _add_pending_flag_observer(builder, "ObsSignalReport", "signal_report_pending", "signal_report?", "D_sig", "c_obs_signal")
        _add_pending_flag_observer(builder, "ObsSensingReport", "sensing_report_pending", "sensing_report?", "D_sense", "c_obs_sensing")
        _add_pending_flag_observer(builder, "ObsPhyKpiReport", "phy_kpi_report_pending", "phy_kpi_report?", "D_report", "c_obs_phy")
    builder.system(_system_declaration(
        include_observers=include_observers,
        include_environment=include_environment,
        include_extended_observers=include_extended_observers,
    ))
    return GeneratedPhyModel(
        model_xml=builder.to_xml(),
        queries=generate_queries(
            model,
            include_observers=include_observers,
            debug_counters=debug_counters,
            open_system=not include_environment,
            include_extended_observers=include_extended_observers,
        ),
        contract=model.to_dict(),
        profile=profile,
        generation_mode=mode_name,
        include_negative_scenarios=include_negative_scenarios,
        system_mode="closed" if include_environment else "open",
        include_extended_observers=include_extended_observers,
    )


def generate_queries(
    contract: PhyContractModel | None = None,
    *,
    include_observers: bool = True,
    debug_counters: bool = True,
    open_system: bool = False,
    include_extended_observers: bool = False,
) -> str:
    model = contract or build_default_contract()
    queries: list[PropertySpec] = []
    for item in model.properties:
        if item.name.startswith("Obs") and not include_observers:
            continue
        if item.name in {"ch_determinism", "sq_determinism"} and not debug_counters:
            continue
        queries.append(item)
    rendered = [
        _wrap_query_with_env_assumption(item.query) if open_system else item.query
        for item in queries
    ]
    if include_extended_observers:
        rendered.extend(_extended_observer_queries(open_system=open_system))
    return "\n".join(rendered) + "\n"


def _normalize_generation_mode(
    mode: str | None,
    *,
    include_observers: bool,
    debug_counters: bool,
    include_negative_scenarios: bool,
) -> tuple[str, bool, bool, bool, bool, bool]:
    if mode is None:
        if include_negative_scenarios:
            return "with_negative_scenarios", include_observers, debug_counters, True, True, False
        if include_observers and debug_counters:
            return "with_observers", True, True, False, True, False
        if debug_counters:
            return "with_debug_counters", include_observers, True, False, True, False
        if not include_observers:
            return "minimal", False, False, False, True, False
        return "custom", include_observers, debug_counters, include_negative_scenarios, True, False
    normalized = mode.strip().lower()
    if normalized == "minimal":
        return "minimal", False, False, False, True, False
    if normalized == "with_observers":
        return "with_observers", True, debug_counters, include_negative_scenarios, True, False
    if normalized == "with_debug_counters":
        return "with_debug_counters", include_observers, True, include_negative_scenarios, True, False
    if normalized == "with_negative_scenarios":
        return "with_negative_scenarios", include_observers, debug_counters, True, True, False
    if normalized == "with_extended_observers":
        return "with_extended_observers", True, debug_counters, include_negative_scenarios, True, True
    if normalized in {"open_system", "open-system", "open"}:
        return "open_system", include_observers, debug_counters, include_negative_scenarios, False, False
    raise ValueError("Unsupported PHY generation mode. Use minimal, with_observers, with_debug_counters, with_negative_scenarios, with_extended_observers, or open_system.")


def _declarations(
    model: PhyContractModel,
    profile: dict,
    *,
    debug_counters: bool,
    mode_name: str,
    include_negative_scenarios: bool,
) -> str:
    deadlines = profile.get("deadlines", {})
    lines = [
        "// Generated from PHY contract IR. Continuous PHY metrics stay outside timed automata.",
        f"// Generation mode: {mode_name}.",
        "// Negative scenarios are emitted by the benchmark suite, not embedded in the closed A_SYS." if include_negative_scenarios else "// Negative scenarios disabled for this generated model.",
        f"const int D_meas = {int(deadlines.get('D_meas', 5))};",
        f"const int D_sig = {int(deadlines.get('D_sig', 5))};",
        f"const int D_sense = {int(deadlines.get('D_sense', 5))};",
        f"const int D_report = {int(deadlines.get('D_report', 5))};",
        f"const int D_BM = {int(deadlines.get('D_BM', 5))};",
        "const int D_child = 5;",
        "const int D_net = 5;",
        "const int T_meas = 5;",
        "const int J_meas = 1;",
        "const int T_report = 5;",
        "const int J_SSB = 1;",
        "const int tau_SSB = 4;",
        "",
        "const int SCENARIO_NORMAL = 0;",
        "const int SCENARIO_COMM_DEGRADED = 1;",
        "const int SCENARIO_SENSING_DEGRADED = 2;",
        "const int SCENARIO_JOINT_DEGRADED = 3;",
        "int[0,3] env_scenario = SCENARIO_NORMAL;",
        "",
        "clock c_meas, c_sig, c_sense, c_report, c_rec, c_ssb;",
        "clock aos_bs, aos_ctrl, c_env, c_net;",
        "clock c_obs_sense, c_obs_fresh, c_obs_beam;",
        "clock c_obs_channel, c_obs_signal, c_obs_sensing, c_obs_phy;",
        "",
        "typedef int[0,4] WaveformT;",
        "const int W_OFDM = 0;",
        "const int W_OTFS = 1;",
        "const int W_AFDM = 2;",
        "const int W_SC = 3;",
        "const int W_OTHER = 4;",
        "WaveformT W = W_OFDM;",
        "",
        _channel_declarations(model),
        "",
        generate_uppaal_declarations(model),
        _priority_helpers(),
        "bool channel_degraded_flag = false;",
        "bool signal_degraded_flag = false;",
        "bool beam_degraded_flag = false;",
        "bool sensing_degraded_flag = false;",
        "bool sensing_failure_flag = false;",
        "bool degradation_flag = false;",
        "bool child_update = false;",
        "bool input_changed = false;",
        "bool target_seen = false;",
        "bool channel_report_pending = false;",
        "bool signal_report_pending = false;",
        "bool sensing_report_pending = false;",
        "bool phy_kpi_report_pending = false;",
        "bool comm_ok = true;",
        "bool sensing_qos_ok = true;",
        "bool TimingOk = true;",
        "bool ConfigAdmissible = true;",
        "bool BeamCmdAdmissible = true;",
        "bool NetDeliveryOk = true;",
        "bool classes_in_range_ch = true;",
        "bool classes_in_range_sig = true;",
        "bool classes_in_range_bm = true;",
        "bool fresh_child_reports = true;",
        f"int[0,1] ch_enabled_count = {1 if debug_counters else 0};",
        f"int[0,1] sq_enabled_count = {1 if debug_counters else 0};",
        "",
        "bool ass_ch() { return TimingOk && classes_in_range_ch; }",
        "bool gar_ch() { return classes_in_range_ch; }",
        "bool ass_sig() { return ConfigAdmissible && classes_in_range_sig; }",
        "bool gar_sig() { return classes_in_range_sig; }",
        "bool ass_bm() { return BeamCmdAdmissible && classes_in_range_bm; }",
        "bool gar_bm() { return classes_in_range_bm; }",
        "bool ass_sq() { return fresh_child_reports && gar_ch() && gar_sig() && gar_bm(); }",
        "bool gar_sq() { return true; }",
        "bool ass_ph() { return gar_ch() && gar_sig() && gar_bm() && gar_sq(); }",
        "bool gar_ph() { return true; }",
        "bool ass_env() { return TimingOk && ConfigAdmissible && BeamCmdAdmissible && NetDeliveryOk; }",
    ]
    return "\n".join(lines)


def _channel_declarations(model: PhyContractModel) -> str:
    handshake = sorted(item.name for item in model.channels if item.kind == "handshake")
    broadcast = sorted(item.name for item in model.channels if item.kind == "broadcast")
    return "\n".join([
        f"chan {', '.join(handshake)};",
        f"broadcast chan {', '.join(broadcast)};",
    ])


def _priority_helpers() -> str:
    return "\n".join([
        "int highest_priority_CH() {",
        "  if (SINRClass == SINRCLASS_OUTAGE) return CHANNELCLASS_OUTAGE;",
        "  if (PowerClass == POWERCLASS_LOW || PowerClass == POWERCLASS_ABSENT) return CHANNELCLASS_BLOCKAGE;",
        "  if (IClass == ICLASS_HIGH || IClass == ICLASS_CRITICAL) return CHANNELCLASS_INTERFERENCE_LIMITED;",
        "  if (DopplerClass == DOPPLERCLASS_HIGH) return CHANNELCLASS_MOBILITY_LIMITED;",
        "  if (DelaySpreadClass == DELAYSPREADCLASS_HIGH) return CHANNELCLASS_MULTIPATH_LIMITED;",
        "  return CHANNELCLASS_NOMINAL;",
        "}",
        "",
        "int highest_priority_SQ() {",
        "  if (ChannelClass == CHANNELCLASS_OUTAGE || SignalClass == SIGNALCLASS_LIMITED || BeamClass == BEAMCLASS_FAILED || PdClass == PDCLASS_FAILED || RfaClass == RFACLASS_CRITICAL || AccClass == ACCCLASS_FAILED || CRBClass == CRBCLASS_UNUSABLE || AoSClass == AOSCLASS_EXPIRED || CapClass == CAPCLASS_FAILED || CoverageClass == COVERAGECLASS_FAILED) return SENSINGSTATE_SENSINGFAILURE;",
        "  if (ChannelClass == CHANNELCLASS_BLOCKAGE || SignalClass == SIGNALCLASS_RECONFIGURING || BeamClass == BEAMCLASS_MISALIGNED) return SENSINGSTATE_FRESHNESSLIMITED;",
        "  if (AoSClass == AOSCLASS_STALE) return SENSINGSTATE_FRESHNESSLIMITED;",
        "  if (AccClass == ACCCLASS_LIMITED || CRBClass == CRBCLASS_LOOSE) return SENSINGSTATE_ACCURACYLIMITED;",
        "  if (PdClass == PDCLASS_LOW) return SENSINGSTATE_PROBABILITYLIMITED;",
        "  if (RfaClass == RFACLASS_HIGH) return SENSINGSTATE_FALSEALARMLIMITED;",
        "  if (CapClass == CAPCLASS_LIMITED) return SENSINGSTATE_CAPACITYLIMITED;",
        "  if (CoverageClass == COVERAGECLASS_LIMITED) return SENSINGSTATE_COVERAGELIMITED;",
        "  return SENSINGSTATE_SENSINGQOSOK;",
        "}",
        "",
    ])


def _add_a_ch(builder: UppaalXmlBuilder) -> None:
    locations = [
        ("ChannelNominal", None),
        ("MeasurePending", "c_meas <= T_meas + J_meas"),
        ("InterferenceLimited", None),
        ("MobilityLimited", None),
        ("MultipathLimited", None),
        ("Blockage", None),
        ("Outage", None),
        ("ContractViolation_CH", None),
    ]
    template = builder.template("Template_A_CH", "ChannelNominal", locations)
    for source, _ in locations:
        if source != "MeasurePending":
            builder.add_transition(template, source, "MeasurePending", sync="measure_tick?", assignment="c_meas = 0, channel_report_pending = true")
        builder.add_transition(template, source, source, sync="power_cmd?")
    transitions = [
        ("env_scenario == SCENARIO_NORMAL && c_meas <= D_meas", "ChannelNominal", "ChannelClass = highest_priority_CH(), channel_degraded_flag = false, ch_enabled_count = 1, channel_report_pending = false, c_meas = 0"),
        ("env_scenario == SCENARIO_COMM_DEGRADED && c_meas <= D_meas", "InterferenceLimited", "ChannelClass = highest_priority_CH(), channel_degraded_flag = true, ch_enabled_count = 1, channel_report_pending = false, c_meas = 0"),
        ("env_scenario == SCENARIO_SENSING_DEGRADED && c_meas <= D_meas", "MobilityLimited", "ChannelClass = highest_priority_CH(), channel_degraded_flag = true, ch_enabled_count = 1, channel_report_pending = false, c_meas = 0"),
        ("env_scenario == SCENARIO_JOINT_DEGRADED && c_meas <= D_meas", "Outage", "ChannelClass = highest_priority_CH(), channel_degraded_flag = true, ch_enabled_count = 1, channel_report_pending = false, c_meas = 0"),
    ]
    for guard, target, assignment in transitions:
        builder.add_transition(template, "MeasurePending", target, guard=guard, sync="channel_report!", assignment=assignment)
    builder.add_transition(template, "InterferenceLimited", "InterferenceLimited", sync="channel_degraded!")
    builder.add_transition(template, "MobilityLimited", "MobilityLimited", sync="mobility_alert!")
    builder.add_transition(template, "MultipathLimited", "MultipathLimited", sync="multipath_alert!")
    builder.add_transition(template, "Blockage", "Blockage", sync="blockage_detected!")
    builder.add_transition(template, "Outage", "Outage", sync="phy_outage!")
    _add_contract_violation_paths(builder, template, [name for name, _ in locations], "ass_ch()", "contract_violation_ch!", "ContractViolation_CH")


def _add_a_sig(builder: UppaalXmlBuilder) -> None:
    locations = [
        ("SignalNominal", None),
        ("PilotBasedSensing", None),
        ("PayloadAssistedSensing", None),
        ("SignalReconfiguring", "c_sig <= D_sig"),
        ("SignalLimited", None),
        ("ContractViolation_SIG", None),
    ]
    template = builder.template("Template_A_SIG", "SignalNominal", locations)
    for source, _ in locations:
        builder.add_transition(template, source, "SignalReconfiguring", sync="waveform_config?", assignment="c_sig = 0, signal_report_pending = true")
        builder.add_transition(template, source, "SignalReconfiguring", sync="pilot_config?", assignment="c_sig = 0, signal_report_pending = true")
        builder.add_transition(template, source, "SignalReconfiguring", sync="prs_config?", assignment="c_sig = 0, signal_report_pending = true")
        builder.add_transition(template, source, "SignalReconfiguring", sync="payload_sensing_config?", assignment="c_sig = 0, signal_report_pending = true")
        builder.add_transition(template, source, "SignalReconfiguring", sync="sensing_mode_cmd?", assignment="c_sig = 0, signal_report_pending = true")
    builder.add_transition(template, "SignalReconfiguring", "SignalNominal", guard="c_sig <= D_sig", sync="signal_report!", assignment="SignalClass = SIGNALCLASS_RECONFIGURING, signal_report_pending = false, c_sig = 0")
    builder.add_transition(template, "SignalNominal", "PilotBasedSensing", guard="PilotDensityClass == PILOTDENSITYCLASS_OK && BLERClass == BLERCLASS_OK && DRTClass == DRTCLASS_OK", sync="signal_report!", assignment="SignalClass = SIGNALCLASS_PILOT_BASED, signal_report_pending = false, c_sig = 0")
    builder.add_transition(template, "PilotBasedSensing", "PayloadAssistedSensing", guard="PilotDensityClass == PILOTDENSITYCLASS_LOW && PayloadSenseClass != PAYLOADSENSECLASS_FAILED", sync="signal_report!", assignment="SignalClass = SIGNALCLASS_PAYLOAD_ASSISTED, signal_report_pending = false, c_sig = 0")
    builder.add_transition(template, "PayloadAssistedSensing", "SignalLimited", guard="BLERClass != BLERCLASS_OK || DRTClass == DRTCLASS_BAD || PayloadSenseClass == PAYLOADSENSECLASS_FAILED", sync="signal_report!", assignment="SignalClass = SIGNALCLASS_LIMITED, signal_report_pending = false, signal_degraded_flag = true, c_sig = 0")
    builder.add_transition(template, "SignalLimited", "SignalLimited", sync="signal_degraded!")
    builder.add_transition(template, "SignalLimited", "SignalReconfiguring", sync="waveform_config?", assignment="c_sig = 0")
    _add_contract_violation_paths(builder, template, [name for name, _ in locations], "ass_sig()", "contract_violation_sig!", "ContractViolation_SIG")


def _add_a_bm(builder: UppaalXmlBuilder) -> None:
    locations = [
        ("BeamSearch", None),
        ("BeamSearchSeen", None),
        ("BeamTrack", None),
        ("BeamLock", None),
        ("BeamPredict", None),
        ("BeamMisalign", None),
        ("BeamRecoveryStart", None),
        ("BeamRecover", "c_rec <= D_BM"),
        ("BeamHOAssist", None),
        ("BeamFailed", None),
        ("ContractViolation_BM", None),
    ]
    template = builder.template("Template_A_BM", "BeamSearch", locations)
    for source, _ in locations:
        builder.add_transition(template, source, "BeamSearch", sync="beam_cmd?", assignment="BeamClass = BEAMCLASS_SEARCH, c_ssb = 0")
        builder.add_transition(template, source, "BeamSearch", sync="ssb_burst_config?", assignment="BeamClass = BEAMCLASS_SEARCH, c_ssb = 0")
        builder.add_transition(template, source, "BeamRecover", sync="recovery_cmd?", assignment="BeamClass = BEAMCLASS_RECOVERING, c_rec = 0")
        builder.add_transition(template, source, "BeamHOAssist", sync="handover_assist_cmd?", assignment="BeamClass = BEAMCLASS_HO_ASSIST")
    builder.add_transition(template, "BeamSearch", "BeamSearchSeen", sync="target_detected?", assignment="target_seen = true")
    builder.add_transition(template, "BeamSearchSeen", "BeamTrack", guard="PRSClass != PRSCLASS_FAILED", sync="beam_report!", assignment="BeamClass = BEAMCLASS_TRACK")
    builder.add_transition(template, "BeamTrack", "BeamLock", guard="BeamErrorClass == BEAMERRORCLASS_LOCKABLE", sync="beam_report!", assignment="BeamClass = BEAMCLASS_LOCKED")
    builder.add_transition(template, "BeamTrack", "BeamMisalign", guard="AccClass == ACCCLASS_FAILED || BeamErrorClass == BEAMERRORCLASS_CRITICAL", sync="beam_report!", assignment="BeamClass = BEAMCLASS_MISALIGNED, beam_degraded_flag = true")
    builder.add_transition(template, "BeamLock", "BeamLock", guard="MisClass == MISCLASS_OK", sync="beam_report!", assignment="BeamClass = BEAMCLASS_LOCKED")
    builder.add_transition(template, "BeamLock", "BeamPredict", guard="MisClass == MISCLASS_WARN || BlockageClass == BLOCKAGECLASS_SUSPECTED", sync="beam_report!", assignment="BeamClass = BEAMCLASS_PREDICT")
    builder.add_transition(template, "BeamPredict", "BeamRecoveryStart", sync="extra_ssb_cmd?", assignment="c_rec = 0")
    builder.add_transition(template, "BeamRecoveryStart", "BeamRecover", sync="recovery_start!", assignment="BeamClass = BEAMCLASS_RECOVERING")
    builder.add_transition(template, "BeamMisalign", "BeamRecoveryStart", sync="beam_misaligned!", assignment="c_rec = 0")
    builder.add_transition(template, "BeamRecover", "BeamLock", guard="BeamErrorClass == BEAMERRORCLASS_LOCKABLE && c_rec <= D_BM", sync="beam_restored!", assignment="BeamClass = BEAMCLASS_LOCKED")
    builder.add_transition(template, "BeamRecover", "BeamHOAssist", guard="BlockageClass == BLOCKAGECLASS_CONFIRMED && c_rec <= D_BM", sync="handover_hint!", assignment="BeamClass = BEAMCLASS_HO_ASSIST")
    builder.add_transition(template, "BeamRecover", "BeamFailed", guard="c_rec == D_BM && BeamErrorClass != BEAMERRORCLASS_LOCKABLE && BlockageClass != BLOCKAGECLASS_CONFIRMED", sync="beam_failure!", assignment="BeamClass = BEAMCLASS_FAILED")
    builder.add_transition(template, "BeamHOAssist", "BeamTrack", sync="new_beam_confirmed?", assignment="BeamClass = BEAMCLASS_TRACK")
    _add_contract_violation_paths(builder, template, [name for name, _ in locations], "ass_bm()", "contract_violation_bm!", "ContractViolation_BM")


def _add_a_sq(builder: UppaalXmlBuilder) -> None:
    locations = [
        ("Idle", None),
        ("SensingEvaluating", "c_sense <= D_sense"),
        ("SensingQoSOk", None),
        ("ProbabilityLimited", None),
        ("FalseAlarmLimited", None),
        ("AccuracyLimited", None),
        ("FreshnessLimited", None),
        ("CoverageLimited", None),
        ("CapacityLimited", None),
        ("SensingFailure", None),
        ("ContractViolation_SQ", None),
    ]
    template = builder.template("Template_A_SQ", "Idle", locations)
    for sync in ("channel_report?", "signal_report?", "beam_report?"):
        builder.add_transition(template, "Idle", "SensingEvaluating", sync=sync, assignment="input_changed = true, sensing_report_pending = true, c_sense = 0")
    transitions = [
        ("env_scenario == SCENARIO_NORMAL && c_sense <= D_sense", "SensingQoSOk", "SensingState = highest_priority_SQ(), sensing_report_pending = false, sensing_degraded_flag = false, sensing_qos_ok = true, sq_enabled_count = 1, c_sense = 0"),
        ("env_scenario == SCENARIO_COMM_DEGRADED && c_sense <= D_sense", "SensingQoSOk", "SensingState = highest_priority_SQ(), sensing_report_pending = false, sensing_degraded_flag = false, sensing_qos_ok = true, sq_enabled_count = 1, c_sense = 0"),
        ("env_scenario == SCENARIO_SENSING_DEGRADED && c_sense <= D_sense", "FreshnessLimited", "SensingState = highest_priority_SQ(), sensing_report_pending = false, sensing_degraded_flag = true, sensing_qos_ok = false, sq_enabled_count = 1, c_sense = 0"),
        ("env_scenario == SCENARIO_JOINT_DEGRADED && c_sense <= D_sense", "SensingFailure", "SensingState = highest_priority_SQ(), sensing_report_pending = false, sensing_failure_flag = true, sensing_qos_ok = false, sq_enabled_count = 1, c_sense = 0"),
    ]
    for guard, target, assignment in transitions:
        builder.add_transition(template, "SensingEvaluating", target, guard=guard, sync="sensing_report!", assignment=assignment)
    for source in ("ProbabilityLimited", "FalseAlarmLimited", "AccuracyLimited", "FreshnessLimited", "CoverageLimited", "CapacityLimited"):
        builder.add_transition(template, source, source, sync="sensing_degraded!")
    builder.add_transition(template, "SensingFailure", "SensingFailure", sync="sensing_failure!")
    _add_contract_violation_paths(builder, template, [name for name, _ in locations], "ass_sq()", "contract_violation_sq!", "ContractViolation_SQ")


def _add_a_ph(builder: UppaalXmlBuilder) -> None:
    locations = [
        ("PHYNormal", None),
        ("PHYCommunicationDegraded", None),
        ("PHYSensingDegraded", None),
        ("PHYJointDegraded", None),
        ("PHYKpiReporting", "c_report <= D_report"),
        ("PHYRecovery", None),
        ("PHYFailure", None),
        ("ContractViolation_PH", None),
    ]
    template = builder.template("Template_A_PH", "PHYNormal", locations)
    for source, _ in locations:
        for sync in ("channel_report?", "signal_report?", "beam_report?", "sensing_report?"):
            builder.add_transition(template, source, "PHYKpiReporting", sync=sync, assignment="child_update = true, phy_kpi_report_pending = true, c_report = 0")
        for sync in ("mac_report_delivered?", "controller_report_delivered?"):
            builder.add_transition(template, source, source, sync=sync)
        builder.add_transition(template, source, "PHYRecovery", sync="recovery_cmd?", assignment="PHYState = PHYSTATE_PHYRECOVERY")
    transitions = [
        ("env_scenario == SCENARIO_NORMAL && c_report <= D_report", "PHYNormal", "PHYState = PHYSTATE_PHYNORMAL, phy_kpi_report_pending = false, comm_ok = true, sensing_qos_ok = true, degradation_flag = false, c_report = 0"),
        ("env_scenario == SCENARIO_COMM_DEGRADED && c_report <= D_report", "PHYCommunicationDegraded", "PHYState = PHYSTATE_PHYCOMMUNICATIONDEGRADED, phy_kpi_report_pending = false, comm_ok = false, sensing_qos_ok = true, degradation_flag = true, c_report = 0"),
        ("env_scenario == SCENARIO_SENSING_DEGRADED && c_report <= D_report", "PHYSensingDegraded", "PHYState = PHYSTATE_PHYSENSINGDEGRADED, phy_kpi_report_pending = false, comm_ok = true, sensing_qos_ok = false, degradation_flag = true, c_report = 0"),
        ("env_scenario == SCENARIO_JOINT_DEGRADED && c_report <= D_report", "PHYJointDegraded", "PHYState = PHYSTATE_PHYJOINTDEGRADED, phy_kpi_report_pending = false, comm_ok = false, sensing_qos_ok = false, degradation_flag = true, c_report = 0"),
    ]
    for guard, target, assignment in transitions:
        builder.add_transition(template, "PHYKpiReporting", target, guard=guard, sync="phy_kpi_report!", assignment=assignment)
    builder.add_transition(template, "PHYKpiReporting", "PHYFailure", guard="ChannelClass == CHANNELCLASS_OUTAGE || BeamClass == BEAMCLASS_FAILED || SensingState == SENSINGSTATE_SENSINGFAILURE", sync="phy_failure!", assignment="PHYState = PHYSTATE_PHYFAILURE")
    for source in ("PHYCommunicationDegraded", "PHYSensingDegraded", "PHYJointDegraded"):
        builder.add_transition(template, source, source, sync="degradation_event!")
    _add_contract_violation_paths(builder, template, [name for name, _ in locations], "ass_ph()", "contract_violation_ph!", "ContractViolation_PH")


def _add_env_ch(builder: UppaalXmlBuilder) -> None:
    template = builder.template("Template_ENV_CH", "TickWait", [("TickWait", None)])
    assignments = {
        "SCENARIO_NORMAL": "SINRClass = SINRCLASS_OK, IClass = ICLASS_OK, PowerClass = POWERCLASS_OK, AoSClass = AOSCLASS_FRESH, PdClass = PDCLASS_OK, RfaClass = RFACLASS_OK",
        "SCENARIO_COMM_DEGRADED": "SINRClass = SINRCLASS_OK, IClass = ICLASS_CRITICAL, PowerClass = POWERCLASS_OK, AoSClass = AOSCLASS_FRESH, PdClass = PDCLASS_OK, RfaClass = RFACLASS_OK",
        "SCENARIO_SENSING_DEGRADED": "SINRClass = SINRCLASS_OK, IClass = ICLASS_OK, PowerClass = POWERCLASS_OK, AoSClass = AOSCLASS_STALE, PdClass = PDCLASS_OK, RfaClass = RFACLASS_OK",
        "SCENARIO_JOINT_DEGRADED": "SINRClass = SINRCLASS_OUTAGE, IClass = ICLASS_CRITICAL, PowerClass = POWERCLASS_ABSENT, AoSClass = AOSCLASS_EXPIRED, PdClass = PDCLASS_FAILED, RfaClass = RFACLASS_CRITICAL",
    }
    for scenario, assignment in assignments.items():
        builder.add_transition(template, "TickWait", "TickWait", sync="measure_tick!", assignment=f"env_scenario = {scenario}, TimingOk = true, {assignment}, c_env = 0")
    builder.add_transition(template, "TickWait", "TickWait")


def _add_env_target(builder: UppaalXmlBuilder) -> None:
    template = builder.template("Template_ENV_TARGET", "TargetWait", [("TargetWait", None)])
    builder.add_transition(template, "TargetWait", "TargetWait", sync="target_detected!", assignment="PRSClass = PRSCLASS_OK, BeamErrorClass = BEAMERRORCLASS_LOCKABLE, BlockageClass = BLOCKAGECLASS_NONE")
    builder.add_transition(template, "TargetWait", "TargetWait", assignment="BlockageClass = BLOCKAGECLASS_CONFIRMED")


def _add_env_mac(builder: UppaalXmlBuilder) -> None:
    template = builder.template("Template_ENV_MAC", "ConfigWait", [("ConfigWait", None)])
    for sync in (
        "pilot_config!",
        "prs_config!",
        "ssb_burst_config!",
        "waveform_config!",
        "payload_sensing_config!",
        "beam_cmd!",
        "extra_ssb_cmd!",
        "handover_assist_cmd!",
        "power_cmd!",
        "sensing_mode_cmd!",
        "new_beam_confirmed!",
        "recovery_cmd!",
    ):
        builder.add_transition(template, "ConfigWait", "ConfigWait", sync=sync, assignment="ConfigAdmissible = true, BeamCmdAdmissible = true")
    builder.add_transition(template, "ConfigWait", "ConfigWait")


def _add_env_net(builder: UppaalXmlBuilder) -> None:
    template = builder.template("Template_ENV_NET", "DeliveryWait", [("DeliveryWait", None)])
    builder.add_transition(template, "DeliveryWait", "DeliveryWait", sync="mac_report_delivered!", assignment="NetDeliveryOk = true, c_net = 0")
    builder.add_transition(template, "DeliveryWait", "DeliveryWait", sync="controller_report_delivered!", assignment="NetDeliveryOk = true, aos_ctrl = 0, c_net = 0")
    builder.add_transition(template, "DeliveryWait", "DeliveryWait", sync="aos_ctrl_expired!")
    builder.add_transition(template, "DeliveryWait", "DeliveryWait")


def _add_observer(
    builder: UppaalXmlBuilder,
    name: str,
    trigger: str,
    responses: list[str],
    deadline: str,
    clock: str,
) -> None:
    template = builder.template(f"Template_{name}", "Idle", [("Idle", None), ("Wait", None), ("Violation", None)])
    builder.add_transition(template, "Idle", "Wait", sync=trigger, assignment=f"{clock} = 0")
    for response in responses:
        guard = f"{clock} <= {deadline}"
        if name == "ObsFreshness":
            guard = f"{guard} && SensingState == SENSINGSTATE_FRESHNESSLIMITED"
        builder.add_transition(template, "Wait", "Idle", guard=guard, sync=response)
    builder.add_transition(template, "Wait", "Violation", guard=f"{clock} > {deadline}")


def _add_pending_flag_observer(
    builder: UppaalXmlBuilder,
    name: str,
    pending_flag: str,
    response: str,
    deadline: str,
    clock: str,
) -> None:
    template = builder.template(f"Template_{name}", "Idle", [("Idle", None), ("Wait", None), ("Violation", None)])
    builder.add_transition(template, "Idle", "Wait", guard=pending_flag, assignment=f"{clock} = 0")
    builder.add_transition(template, "Wait", "Idle", guard=f"{clock} <= {deadline}", sync=response)
    builder.add_transition(template, "Wait", "Violation", guard=f"{clock} > {deadline}")


def _add_contract_violation_paths(
    builder: UppaalXmlBuilder,
    template: ET.Element,
    locations: Iterable[str],
    assumption: str,
    violation_sync: str,
    violation_location: str,
) -> None:
    for location in locations:
        if location == violation_location:
            continue
        builder.add_transition(
            template,
            location,
            violation_location,
            guard=f"!{assumption}",
            sync=violation_sync,
        )


def _add_self_loops(builder: UppaalXmlBuilder, template: ET.Element, locations: Iterable[str]) -> None:
    for location in locations:
        builder.add_transition(template, location, location)


def _wrap_query_with_env_assumption(query: str) -> str:
    stripped = query.strip()
    if stripped.startswith("A[]"):
        body = stripped[len("A[]") :].strip()
        return f"A[] (ass_env() imply ({body}))"
    if stripped.startswith("E<>"):
        body = stripped[len("E<>") :].strip()
        return f"E<> (ass_env() && ({body}))"
    return stripped


def _extended_observer_queries(*, open_system: bool) -> list[str]:
    queries = [
        "A[] not ObsChannelReport.Violation",
        "A[] not ObsSignalReport.Violation",
        "A[] not ObsSensingReport.Violation",
        "A[] not ObsPhyKpiReport.Violation",
    ]
    if not open_system:
        return queries
    return [_wrap_query_with_env_assumption(query) for query in queries]


def _system_declaration(*, include_observers: bool, include_environment: bool, include_extended_observers: bool) -> str:
    lines = [
        "A_CH = Template_A_CH();",
        "A_SIG = Template_A_SIG();",
        "A_BM = Template_A_BM();",
        "A_SQ = Template_A_SQ();",
        "A_PH = Template_A_PH();",
    ]
    systems = ["A_CH", "A_SIG", "A_BM", "A_SQ", "A_PH"]
    if include_environment:
        lines.extend([
            "ENV_CH = Template_ENV_CH();",
            "ENV_TARGET = Template_ENV_TARGET();",
            "ENV_MAC = Template_ENV_MAC();",
            "ENV_NET = Template_ENV_NET();",
        ])
        systems.extend(["ENV_CH", "ENV_TARGET", "ENV_MAC", "ENV_NET"])
    if include_observers:
        lines.extend([
            "ObsSenseReport = Template_ObsSenseReport();",
            "ObsFreshness = Template_ObsFreshness();",
            "ObsBeamRecovery = Template_ObsBeamRecovery();",
        ])
        systems.extend(["ObsSenseReport", "ObsFreshness", "ObsBeamRecovery"])
    if include_extended_observers:
        lines.extend([
            "ObsChannelReport = Template_ObsChannelReport();",
            "ObsSignalReport = Template_ObsSignalReport();",
            "ObsSensingReport = Template_ObsSensingReport();",
            "ObsPhyKpiReport = Template_ObsPhyKpiReport();",
        ])
        systems.extend(["ObsChannelReport", "ObsSignalReport", "ObsSensingReport", "ObsPhyKpiReport"])
    lines.append(f"system {', '.join(systems)};")
    return "\n".join(lines)


def _safe(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]", "_", value)
