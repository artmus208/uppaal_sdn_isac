from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass, field

from .alpha import CONTINUOUS_GUARD_TOKENS, check_no_continuous_guards
from .defaults import build_default_contract
from .ir import PhyContractModel

REQUIRED_PHY = ["A_CH", "A_SIG", "A_BM", "A_SQ", "A_PH"]
REQUIRED_ENV = ["ENV_CH", "ENV_TARGET", "ENV_MAC", "ENV_NET"]
REQUIRED_OBSERVERS = ["ObsSenseReport", "ObsFreshness", "ObsBeamRecovery"]
REQUIRED_BROADCAST_REPORTS = ["channel_report", "signal_report", "beam_report", "sensing_report", "phy_kpi_report"]
REQUIRED_BROADCAST_EVENTS = [
    "channel_degraded",
    "signal_degraded",
    "beam_misaligned",
    "beam_failure",
    "sensing_degraded",
    "phy_outage",
    "degradation_event",
    "recovery_event",
    "mobility_alert",
    "multipath_alert",
    "blockage_detected",
    "beam_locked",
    "beam_restored",
    "handover_hint",
    "sensing_failure",
    "phy_failure",
    "sensing_success",
    "aos_ctrl_expired",
    "recovery_start",
    "target_detected",
    "contract_violation_ch",
    "contract_violation_sig",
    "contract_violation_bm",
    "contract_violation_sq",
    "contract_violation_ph",
]
REQUIRED_HANDSHAKES = [
    "measure_tick",
    "pilot_config",
    "prs_config",
    "ssb_burst_config",
    "waveform_config",
    "payload_sensing_config",
    "beam_cmd",
    "extra_ssb_cmd",
    "handover_assist_cmd",
    "power_cmd",
    "sensing_mode_cmd",
    "recovery_cmd",
    "new_beam_confirmed",
    "mac_report_delivered",
    "controller_report_delivered",
]


@dataclass
class SemanticReport:
    ok: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    details: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


def validate_contract_ir(contract: PhyContractModel | None = None) -> SemanticReport:
    model = contract or build_default_contract()
    errors: list[str] = []
    warnings: list[str] = []
    automata = {item.name for item in model.automata}
    env_specs = {item.name for item in model.env}
    classes = {item.name for item in model.classes}
    variables = {item.name for item in model.variables}
    channels = {item.name: item.kind for item in model.channels}
    for name in REQUIRED_PHY:
        if name not in model.phy_components:
            errors.append(f"Missing PHY component in composition: {name}.")
        if name not in automata:
            errors.append(f"Missing automaton spec: {name}.")
    for name in REQUIRED_ENV:
        if name not in model.env_components:
            errors.append(f"Missing ENV component in composition: {name}.")
        if model.env and name not in env_specs:
            errors.append(f"Missing ENV spec: {name}.")
    for name in ("ChannelClass", "SignalClass", "BeamClass", "SensingState", "PHYState"):
        if name not in classes:
            errors.append(f"Missing class spec: {name}.")
        if model.variables and name not in variables:
            errors.append(f"Missing variable spec: {name}.")
    for name in REQUIRED_BROADCAST_REPORTS + REQUIRED_BROADCAST_EVENTS:
        if channels.get(name) != "broadcast":
            errors.append(f"Report/event channel {name} must be broadcast.")
    for name in REQUIRED_HANDSHAKES:
        if channels.get(name) != "handshake":
            errors.append(f"Command channel {name} must be handshake.")
    observer_names = {item.name for item in model.observers}
    for name in REQUIRED_OBSERVERS:
        if name not in observer_names:
            errors.append(f"Missing observer: {name}.")
    if any("OFDM" == loc.name for auto in model.automata for loc in auto.locations):
        errors.append("OFDM must be a waveform variable value, not a location.")
    return SemanticReport(
        ok=not errors,
        errors=errors,
        warnings=warnings,
        details={
            "phy_components": list(model.phy_components),
            "env_components": list(model.env_components),
            "class_count": len(model.classes),
            "variable_count": len(model.variables),
            "channel_count": len(model.channels),
            "env_spec_count": len(model.env),
        },
    )


def validate_generated_model(
    model_xml: str,
    queries: str | None = None,
    *,
    require_observers: bool = True,
    require_environment: bool = True,
) -> SemanticReport:
    errors: list[str] = []
    warnings: list[str] = []
    try:
        root = ET.fromstring(model_xml)
    except ET.ParseError as exc:
        return SemanticReport(ok=False, errors=[f"XML parse error: {exc}"])

    declarations = root.findtext("declaration") or ""
    system = root.findtext("system") or ""
    template_names = [_text(template.find("name")) for template in root.findall("template")]
    all_names = set(template_names) | set(_system_instances(system))

    required_instances = list(REQUIRED_PHY)
    if require_environment:
        required_instances.extend(REQUIRED_ENV)
    if require_observers:
        required_instances.extend(REQUIRED_OBSERVERS)
    for name in required_instances:
        if name not in all_names:
            errors.append(f"Generated model does not contain required template/instance: {name}.")
    for name in REQUIRED_BROADCAST_REPORTS + REQUIRED_BROADCAST_EVENTS:
        if not _declares_broadcast(declarations, name):
            errors.append(f"{name} must be declared as broadcast chan.")
    for name in REQUIRED_HANDSHAKES:
        if not _declares_handshake(declarations, name):
            errors.append(f"{name} must be declared as handshake chan.")
    alpha_report = check_no_continuous_guards(_model_body_without_comments(model_xml))
    errors.extend(alpha_report.errors)
    errors.extend(_check_single_sync_per_transition(root))
    errors.extend(_check_waveform_not_location(root))
    errors.extend(_check_report_variable_single_writer(root))
    errors.extend(_check_priority_helpers(root, declarations))
    errors.extend(_check_bm_deadline_semantics(root))
    errors.extend(_check_observer_deadlines(root))
    errors.extend(_check_observer_non_interference(root, declarations))
    errors.extend(_check_required_inputs(root))
    errors.extend(_check_class_ranges(declarations))
    errors.extend(_check_sync_declarations(root, declarations))
    errors.extend(_check_no_estimator_values_in_transition_guards(root))
    errors.extend(_check_report_event_payload_policy(root))
    errors.extend(_check_channel_report_guarantee(root))
    errors.extend(_check_signal_report_guarantee(root))
    errors.extend(_check_bm_outcome_and_misalignment_guarantee(root))
    errors.extend(_check_a_sq_dependency(declarations))
    errors.extend(_check_sensing_report_guarantee(root))
    errors.extend(_check_phy_kpi_report_guarantee(root))
    errors.extend(_check_contract_violation_paths(root))
    if require_environment:
        dangling_errors, dangling_warnings = _check_dangling_channels(root, declarations, require_observers=require_observers)
        errors.extend(dangling_errors)
        warnings.extend(dangling_warnings)
    if queries is not None:
        errors.extend(_check_deadlock_query_scope(queries, require_environment=require_environment))
        errors.extend(_check_no_unbounded_leads_to_for_deadlines(queries))
        errors.extend(_check_query_references(root, system, queries))
    return SemanticReport(
        ok=not errors,
        errors=errors,
        warnings=warnings,
        details={"templates": template_names, "instances": _system_instances(system)},
    )


def _declares_broadcast(declarations: str, name: str) -> bool:
    return bool(re.search(rf"\bbroadcast\s+chan\b[^;]*\b{name}\b", declarations))


def _declares_handshake(declarations: str, name: str) -> bool:
    return bool(re.search(rf"(?<!broadcast\s)\bchan\b[^;]*\b{name}\b", declarations))


def _text(element: ET.Element | None) -> str:
    return "" if element is None or element.text is None else element.text.strip()


def _system_instances(system: str) -> list[str]:
    return re.findall(r"^\s*([A-Za-z_]\w*)\s*=", system, flags=re.MULTILINE)


def _model_body_without_comments(model_xml: str) -> str:
    return re.sub(r"//.*", "", model_xml)


def _check_single_sync_per_transition(root: ET.Element) -> list[str]:
    errors: list[str] = []
    for template in root.findall("template"):
        name = _text(template.find("name"))
        for transition in template.findall("transition"):
            syncs = [label for label in transition.findall("label") if label.attrib.get("kind") == "synchronisation"]
            if len(syncs) > 1:
                errors.append(f"{name} has a transition with more than one sync label.")
    return errors


def _check_waveform_not_location(root: ET.Element) -> list[str]:
    forbidden = {"OFDM", "OTFS", "AFDM", "SC", "OTHER"}
    errors: list[str] = []
    for template in root.findall("template"):
        template_name = _text(template.find("name"))
        if template_name not in {"A_SIG", "Template_A_SIG"}:
            continue
        for location in template.findall("location"):
            loc_name = _text(location.find("name"))
            if loc_name in forbidden:
                errors.append(f"A_SIG uses waveform {loc_name} as a location.")
    return errors


def _check_report_variable_single_writer(root: ET.Element) -> list[str]:
    allowed_writers = {
        "ChannelClass": {"A_CH", "Template_A_CH"},
        "SignalClass": {"A_SIG", "Template_A_SIG"},
        "BeamClass": {"A_BM", "Template_A_BM"},
        "SensingState": {"A_SQ", "Template_A_SQ"},
        "PHYState": {"A_PH", "Template_A_PH"},
    }
    errors: list[str] = []
    for template in root.findall("template"):
        name = _text(template.find("name"))
        for label in template.findall(".//label"):
            if label.attrib.get("kind") != "assignment":
                continue
            assignment = _text(label)
            for variable, allowed in allowed_writers.items():
                if re.search(rf"\b{variable}\s*=", assignment) and name not in allowed:
                    owner = sorted(allowed)[0].replace("Template_", "")
                    errors.append(f"{name} writes {variable}; only {owner} may write it.")
    return errors


def _check_bm_deadline_semantics(root: ET.Element) -> list[str]:
    errors: list[str] = []
    for template in root.findall("template"):
        name = _text(template.find("name"))
        if name not in {"A_BM", "Template_A_BM"}:
            continue
        outcome_syncs: set[str] = set()
        for transition in template.findall("transition"):
            source_ref = transition.find("source").attrib.get("ref") if transition.find("source") is not None else ""
            source_name = _location_name_by_id(template, source_ref)
            labels = "\n".join(_text(label) for label in transition.findall("label"))
            if source_name == "BeamRecover" and re.search(r"\bc_rec\s*>\s*D_BM\b", labels):
                errors.append("BeamRecover transition uses unreachable guard c_rec > D_BM.")
            if source_name != "BeamRecover":
                continue
            sync = _transition_sync(transition)
            guard = _transition_guard(transition)
            if sync in {"beam_restored!", "handover_hint!", "beam_failure!"}:
                outcome_syncs.add(sync)
            if sync == "beam_failure!" and not re.search(r"\bc_rec\s*==\s*D_BM\b", guard):
                errors.append("BeamRecover beam_failure! transition must use timeout guard c_rec == D_BM.")
        missing = {"beam_restored!", "handover_hint!", "beam_failure!"} - outcome_syncs
        if missing:
            errors.append(f"BeamRecover is missing recovery outcome transition(s): {', '.join(sorted(missing))}.")
    return errors


def _check_priority_helpers(root: ET.Element, declarations: str) -> list[str]:
    errors: list[str] = []
    for name in ("highest_priority_CH", "highest_priority_SQ"):
        if not re.search(rf"\b{name}\s*\(", declarations):
            errors.append(f"Missing generated priority helper function: {name}.")
    assignment_text = "\n".join(
        _text(label)
        for label in root.findall(".//label")
        if label.attrib.get("kind") == "assignment"
    )
    if "ChannelClass = highest_priority_CH()" not in assignment_text:
        errors.append("Generated model does not reference highest_priority_CH().")
    if "SensingState = highest_priority_SQ()" not in assignment_text:
        errors.append("Generated model does not reference highest_priority_SQ().")
    return errors


def _check_observer_deadlines(root: ET.Element) -> list[str]:
    errors: list[str] = []
    for template in root.findall("template"):
        name = _text(template.find("name"))
        if not name.startswith("Obs"):
            continue
        for location in template.findall("location"):
            loc_name = _text(location.find("name"))
            invariant = "\n".join(_text(label) for label in location.findall("label") if label.attrib.get("kind") == "invariant")
            if loc_name.startswith("Wait") and "<=" in invariant:
                errors.append(f"{name}.{loc_name} has an invariant; observer wait locations must allow c>D violation.")
    return errors


def _check_observer_non_interference(root: ET.Element, declarations: str) -> list[str]:
    errors: list[str] = []
    broadcast = _broadcast_declared_names(declarations)
    for template in root.findall("template"):
        name = _text(template.find("name"))
        if not name.startswith("Template_Obs") and not name.startswith("Obs"):
            continue
        for transition in template.findall("transition"):
            sync = _transition_sync(transition)
            if not sync:
                continue
            if not sync.endswith("?"):
                errors.append(f"{name} observer transition must listen passively, found sync {sync}.")
                continue
            channel = sync[:-1]
            if channel not in broadcast:
                errors.append(f"{name} observer listens to non-broadcast channel {channel}.")
    return errors


def _check_required_inputs(root: ET.Element) -> list[str]:
    errors: list[str] = []
    sq = _template_by_name(root, "Template_A_SQ")
    if sq is None:
        sq = _template_by_name(root, "A_SQ")
    ph = _template_by_name(root, "Template_A_PH")
    if ph is None:
        ph = _template_by_name(root, "A_PH")
    if sq is not None:
        syncs = _template_syncs(sq)
        for item in ("channel_report?", "signal_report?", "beam_report?"):
            if item not in syncs:
                errors.append(f"A_SQ does not listen to {item}.")
    if ph is not None:
        syncs = _template_syncs(ph)
        for item in ("channel_report?", "signal_report?", "beam_report?", "sensing_report?"):
            if item not in syncs:
                errors.append(f"A_PH does not listen to {item}.")
    return errors


def _check_class_ranges(declarations: str) -> list[str]:
    errors: list[str] = []
    model = build_default_contract()
    for item in model.classes:
        expected_max = len(item.values) - 1
        if not re.search(rf"\btypedef\s+int\[0,{expected_max}\]\s+{item.name}T\s*;", declarations):
            errors.append(f"Class {item.name} must be declared as bounded int[0,{expected_max}].")
        if not re.search(rf"\b{item.name}T\s+{item.name}\s*=", declarations):
            errors.append(f"Class variable {item.name} must use bounded type {item.name}T.")
    return errors


def _check_dangling_channels(
    root: ET.Element,
    declarations: str,
    *,
    require_observers: bool,
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    handshake = _handshake_declared_names(declarations)
    broadcast = _broadcast_declared_names(declarations)
    sends, receives = _channel_usage(root)
    for name in sorted(handshake):
        if name not in sends:
            errors.append(f"Handshake channel {name} has no sender.")
        if name not in receives:
            errors.append(f"Handshake channel {name} has no receiver.")
    required_broadcast = {"channel_report", "signal_report", "beam_report", "sensing_report", "target_detected"}
    if require_observers:
        required_broadcast.update({
            "phy_kpi_report",
            "sensing_degraded",
            "aos_ctrl_expired",
            "recovery_start",
            "beam_restored",
            "handover_hint",
            "beam_failure",
        })
    for name in sorted(broadcast):
        if name not in sends:
            message = f"Broadcast channel {name} has no sender."
            if name in required_broadcast:
                errors.append(message)
            else:
                warnings.append(message)
        if name not in receives:
            message = f"Broadcast channel {name} has no listener."
            if name in required_broadcast:
                errors.append(message)
            else:
                warnings.append(message)
    return errors, warnings


def _check_sync_declarations(root: ET.Element, declarations: str) -> list[str]:
    errors: list[str] = []
    declared = _handshake_declared_names(declarations) | _broadcast_declared_names(declarations)
    sends, receives = _channel_usage(root)
    for name in sorted(sends | receives):
        if name not in declared:
            errors.append(f"Transition uses undeclared channel {name}.")
    return errors


def _check_no_estimator_values_in_transition_guards(root: ET.Element) -> list[str]:
    errors: list[str] = []
    token_patterns = {
        token: re.compile(rf"\b{re.escape(token)}\b")
        for token in CONTINUOUS_GUARD_TOKENS
    }
    for template in root.findall("template"):
        template_name = _text(template.find("name"))
        for transition in template.findall("transition"):
            guard = _transition_guard(transition)
            if not guard:
                continue
            for token, pattern in sorted(token_patterns.items()):
                if pattern.search(guard):
                    errors.append(
                        f"{template_name} transition guard uses estimator-derived value {token}; use alpha/profile/report metadata only."
                    )
    return errors


def _check_report_event_payload_policy(root: ET.Element) -> list[str]:
    errors: list[str] = []
    reports = set(REQUIRED_BROADCAST_REPORTS)
    events = set(REQUIRED_BROADCAST_EVENTS)
    for template in root.findall("template"):
        template_name = _text(template.find("name"))
        for transition in template.findall("transition"):
            sync_text = _transition_sync(transition)
            if not sync_text:
                continue
            sync_tokens = re.findall(r"\b([A-Za-z_]\w*)[!?]", sync_text)
            if len(sync_tokens) > 1:
                errors.append(
                    f"{template_name} transition combines multiple sync events in one label: {sync_text}."
                )
                continue
            channel = sync_tokens[0] if sync_tokens else sync_text.rstrip("!?")
            if channel not in reports:
                continue
            labels_text = "\n".join(_text(label) for label in transition.findall("label"))
            combined_events = [
                event
                for event in events
                if event not in reports and re.search(rf"\b{re.escape(event)}!", labels_text)
            ]
            if combined_events:
                errors.append(
                    f"{template_name} report transition {channel}! also references event sync(s) {combined_events}; "
                    "split the alert into a separate transition or encode it in report payload."
                )
    return errors


def _check_channel_report_guarantee(root: ET.Element) -> list[str]:
    errors: list[str] = []
    template = _template_by_any_name(root, "Template_A_CH", "A_CH")
    if template is None:
        return errors
    measure_edges = [
        transition
        for transition in template.findall("transition")
        if _transition_sync(transition) == "measure_tick?"
        and _transition_target_name(template, transition) == "MeasurePending"
    ]
    if not measure_edges:
        errors.append("A_CH has no measure_tick? transition into MeasurePending.")
    for transition in measure_edges:
        if "c_meas = 0" not in _transition_assignment(transition):
            errors.append("A_CH measure_tick? transition must reset c_meas.")
    report_edges = [
        transition
        for transition in template.findall("transition")
        if _transition_source_name(template, transition) == "MeasurePending"
        and _transition_sync(transition) == "channel_report!"
    ]
    if not report_edges:
        errors.append("A_CH has no channel_report! transition from MeasurePending.")
    for transition in report_edges:
        guard = _transition_guard(transition)
        if not re.search(r"\bc_meas\s*<=\s*D_meas\b", guard):
            errors.append("A_CH channel_report! transition from MeasurePending must guard c_meas <= D_meas.")
    return errors


def _check_signal_report_guarantee(root: ET.Element) -> list[str]:
    errors: list[str] = []
    template = _template_by_any_name(root, "Template_A_SIG", "A_SIG")
    if template is None:
        return errors
    config_syncs = {"waveform_config?", "pilot_config?", "payload_sensing_config?"}
    for sync in sorted(config_syncs):
        edges = [
            transition
            for transition in template.findall("transition")
            if _transition_sync(transition) == sync
            and _transition_target_name(template, transition) == "SignalReconfiguring"
        ]
        if not edges:
            errors.append(f"A_SIG has no {sync} transition into SignalReconfiguring.")
        for transition in edges:
            if "c_sig = 0" not in _transition_assignment(transition):
                errors.append(f"A_SIG {sync} transition must reset c_sig.")
    report_edges = [
        transition
        for transition in template.findall("transition")
        if _transition_source_name(template, transition) == "SignalReconfiguring"
        and _transition_sync(transition) == "signal_report!"
    ]
    if not report_edges:
        errors.append("A_SIG has no signal_report! transition from SignalReconfiguring.")
    for transition in report_edges:
        if not re.search(r"\bc_sig\s*<=\s*D_sig\b", _transition_guard(transition)):
            errors.append("A_SIG signal_report! transition from SignalReconfiguring must guard c_sig <= D_sig.")
    return errors


def _check_bm_outcome_and_misalignment_guarantee(root: ET.Element) -> list[str]:
    errors: list[str] = []
    template = _template_by_any_name(root, "Template_A_BM", "A_BM")
    if template is None:
        return errors
    outcomes = {"beam_restored!", "handover_hint!", "beam_failure!"}
    outcome_edges: dict[str, list[ET.Element]] = {item: [] for item in outcomes}
    for transition in template.findall("transition"):
        if _transition_source_name(template, transition) != "BeamRecover":
            continue
        sync = _transition_sync(transition)
        if sync in outcomes:
            outcome_edges[sync].append(transition)
    for sync, edges in sorted(outcome_edges.items()):
        if len(edges) != 1:
            errors.append(f"BeamRecover must have exactly one {sync} outcome transition, found {len(edges)}.")
    if outcome_edges["beam_restored!"]:
        guard = _transition_guard(outcome_edges["beam_restored!"][0])
        if "BeamErrorClass == BEAMERRORCLASS_LOCKABLE" not in guard or "c_rec <= D_BM" not in guard:
            errors.append("beam_restored! must be guarded by lockable beam and c_rec <= D_BM.")
    if outcome_edges["handover_hint!"]:
        guard = _transition_guard(outcome_edges["handover_hint!"][0])
        if "BlockageClass == BLOCKAGECLASS_CONFIRMED" not in guard or "c_rec <= D_BM" not in guard:
            errors.append("handover_hint! must be guarded by confirmed blockage and c_rec <= D_BM.")
    if outcome_edges["beam_failure!"]:
        guard = _transition_guard(outcome_edges["beam_failure!"][0])
        if "c_rec == D_BM" not in guard or "BeamErrorClass != BEAMERRORCLASS_LOCKABLE" not in guard or "BlockageClass != BLOCKAGECLASS_CONFIRMED" not in guard:
            errors.append("beam_failure! must be the exclusive timeout outcome at c_rec == D_BM.")
    misalign_edges = [
        transition
        for transition in template.findall("transition")
        if _transition_source_name(template, transition) == "BeamMisalign"
        and _transition_sync(transition) == "beam_misaligned!"
    ]
    if not misalign_edges:
        errors.append("A_BM must emit beam_misaligned! from BeamMisalign.")
    for transition in misalign_edges:
        if _transition_target_name(template, transition) != "BeamRecoveryStart":
            errors.append("beam_misaligned! must lead to BeamRecoveryStart.")
    return errors


def _check_a_sq_dependency(declarations: str) -> list[str]:
    errors: list[str] = []
    match = re.search(r"int\s+highest_priority_SQ\(\)\s*\{(?P<body>.*?)\n\}", declarations, flags=re.DOTALL)
    if not match:
        return ["Missing highest_priority_SQ() body."]
    body = match.group("body")
    required = {
        "ChannelClass",
        "SignalClass",
        "BeamClass",
        "PdClass",
        "RfaClass",
        "AccClass",
        "CRBClass",
        "AoSClass",
        "CapClass",
        "CoverageClass",
    }
    missing = sorted(name for name in required if not re.search(rf"\b{re.escape(name)}\b", body))
    if missing:
        errors.append(f"highest_priority_SQ() does not depend on required class variables: {missing}.")
    return errors


def _check_sensing_report_guarantee(root: ET.Element) -> list[str]:
    errors: list[str] = []
    template = _template_by_any_name(root, "Template_A_SQ", "A_SQ")
    if template is None:
        return errors
    for sync in ("channel_report?", "signal_report?", "beam_report?"):
        edges = [
            transition
            for transition in template.findall("transition")
            if _transition_sync(transition) == sync
            and _transition_target_name(template, transition) == "SensingEvaluating"
        ]
        if not edges:
            errors.append(f"A_SQ has no {sync} transition into SensingEvaluating.")
        for transition in edges:
            if "c_sense = 0" not in _transition_assignment(transition):
                errors.append(f"A_SQ {sync} transition must reset c_sense.")
    report_edges = [
        transition
        for transition in template.findall("transition")
        if _transition_source_name(template, transition) == "SensingEvaluating"
        and _transition_sync(transition) == "sensing_report!"
    ]
    if not report_edges:
        errors.append("A_SQ has no sensing_report! transition from SensingEvaluating.")
    for transition in report_edges:
        if not re.search(r"\bc_sense\s*<=\s*D_sense\b", _transition_guard(transition)):
            errors.append("A_SQ sensing_report! transition from SensingEvaluating must guard c_sense <= D_sense.")
    return errors


def _check_phy_kpi_report_guarantee(root: ET.Element) -> list[str]:
    errors: list[str] = []
    template = _template_by_any_name(root, "Template_A_PH", "A_PH")
    if template is None:
        return errors
    for sync in ("channel_report?", "signal_report?", "beam_report?", "sensing_report?"):
        edges = [
            transition
            for transition in template.findall("transition")
            if _transition_sync(transition) == sync
            and _transition_target_name(template, transition) == "PHYKpiReporting"
        ]
        if not edges:
            errors.append(f"A_PH has no {sync} transition into PHYKpiReporting.")
        for transition in edges:
            if "c_report = 0" not in _transition_assignment(transition):
                errors.append(f"A_PH {sync} transition must reset c_report.")
    report_edges = [
        transition
        for transition in template.findall("transition")
        if _transition_source_name(template, transition) == "PHYKpiReporting"
        and _transition_sync(transition) == "phy_kpi_report!"
    ]
    if not report_edges:
        errors.append("A_PH has no phy_kpi_report! transition from PHYKpiReporting.")
    for transition in report_edges:
        if not re.search(r"\bc_report\s*<=\s*D_report\b", _transition_guard(transition)):
            errors.append("A_PH phy_kpi_report! transition from PHYKpiReporting must guard c_report <= D_report.")
    return errors


def _check_contract_violation_paths(root: ET.Element) -> list[str]:
    errors: list[str] = []
    expected = {
        "Template_A_CH": ("ass_ch()", "contract_violation_ch!", "ContractViolation_CH"),
        "Template_A_SIG": ("ass_sig()", "contract_violation_sig!", "ContractViolation_SIG"),
        "Template_A_BM": ("ass_bm()", "contract_violation_bm!", "ContractViolation_BM"),
        "Template_A_SQ": ("ass_sq()", "contract_violation_sq!", "ContractViolation_SQ"),
        "Template_A_PH": ("ass_ph()", "contract_violation_ph!", "ContractViolation_PH"),
    }
    for template_name, (assumption, sync, target) in expected.items():
        template = _template_by_any_name(root, template_name, template_name.replace("Template_", ""))
        if template is None:
            continue
        edges = [
            transition
            for transition in template.findall("transition")
            if _transition_target_name(template, transition) == target
            and _transition_sync(transition) == sync
        ]
        if not edges:
            errors.append(f"{template_name} has no contract violation path to {target} via {sync}.")
            continue
        if not any(f"!{assumption}" in _transition_guard(transition) for transition in edges):
            errors.append(f"{template_name} contract violation path must be guarded by !{assumption}.")
    return errors


def _check_deadlock_query_scope(queries: str, *, require_environment: bool) -> list[str]:
    errors: list[str] = []
    for query in _query_lines(queries):
        if "deadlock" not in query:
            continue
        if require_environment:
            continue
        if "ass_env()" not in query:
            errors.append(
                "A[] not deadlock is only valid for closed A_SYS; open-system deadlock queries must be guarded by ass_env()."
            )
    return errors


def _check_no_unbounded_leads_to_for_deadlines(queries: str) -> list[str]:
    errors: list[str] = []
    for query in _query_lines(queries):
        if "-->" in query:
            errors.append(f"Unbounded leads-to query is not allowed for bounded PHY deadlines: {query}")
    return errors


def _check_query_references(root: ET.Element, system: str, queries: str) -> list[str]:
    errors: list[str] = []
    instance_templates = _system_instance_templates(system)
    template_locations = _template_locations(root)
    instance_locations = {
        instance: template_locations.get(template, set())
        for instance, template in instance_templates.items()
    }
    for query in _query_lines(queries):
        for instance, location in re.findall(r"\b([A-Za-z_]\w*)\.([A-Za-z_]\w*)\b", query):
            if instance not in instance_locations:
                errors.append(f"Query references unknown instance {instance}: {query}")
                continue
            if location not in instance_locations[instance]:
                errors.append(f"Query references unknown location {instance}.{location}: {query}")
        if query.startswith("E<>") and "." in query and not re.search(r"\b[A-Za-z_]\w*\.[A-Za-z_]\w*\b", query):
            errors.append(f"Reachability query has no recognizable instance.location reference: {query}")
    return errors


def _template_by_name(root: ET.Element, name: str) -> ET.Element | None:
    for template in root.findall("template"):
        if _text(template.find("name")) == name:
            return template
    return None


def _template_by_any_name(root: ET.Element, *names: str) -> ET.Element | None:
    for name in names:
        template = _template_by_name(root, name)
        if template is not None:
            return template
    return None


def _template_syncs(template: ET.Element) -> set[str]:
    return {
        _text(label)
        for label in template.findall(".//label")
        if label.attrib.get("kind") == "synchronisation"
    }


def _transition_sync(transition: ET.Element) -> str:
    for label in transition.findall("label"):
        if label.attrib.get("kind") == "synchronisation":
            return _text(label)
    return ""


def _transition_guard(transition: ET.Element) -> str:
    return " && ".join(
        _text(label)
        for label in transition.findall("label")
        if label.attrib.get("kind") == "guard"
    )


def _transition_assignment(transition: ET.Element) -> str:
    return ", ".join(
        _text(label)
        for label in transition.findall("label")
        if label.attrib.get("kind") == "assignment"
    )


def _transition_source_name(template: ET.Element, transition: ET.Element) -> str:
    source = transition.find("source")
    ref = source.attrib.get("ref") if source is not None else ""
    return _location_name_by_id(template, ref)


def _transition_target_name(template: ET.Element, transition: ET.Element) -> str:
    target = transition.find("target")
    ref = target.attrib.get("ref") if target is not None else ""
    return _location_name_by_id(template, ref)


def _broadcast_declared_names(declarations: str) -> set[str]:
    names: set[str] = set()
    for match in re.finditer(r"\bbroadcast\s+chan\s+([^;]+);", declarations):
        names.update(item.strip() for item in match.group(1).split(",") if item.strip())
    return names


def _handshake_declared_names(declarations: str) -> set[str]:
    names: set[str] = set()
    for match in re.finditer(r"(?<!broadcast\s)\bchan\s+([^;]+);", declarations):
        names.update(item.strip() for item in match.group(1).split(",") if item.strip())
    return names


def _channel_usage(root: ET.Element) -> tuple[set[str], set[str]]:
    sends: set[str] = set()
    receives: set[str] = set()
    for label in root.findall(".//label"):
        if label.attrib.get("kind") != "synchronisation":
            continue
        sync = _text(label)
        if sync.endswith("!"):
            sends.add(sync[:-1])
        elif sync.endswith("?"):
            receives.add(sync[:-1])
    return sends, receives


def _system_instance_templates(system: str) -> dict[str, str]:
    return {
        match.group(1): match.group(2)
        for match in re.finditer(r"^\s*([A-Za-z_]\w*)\s*=\s*([A-Za-z_]\w*)\s*\(", system, flags=re.MULTILINE)
    }


def _template_locations(root: ET.Element) -> dict[str, set[str]]:
    data: dict[str, set[str]] = {}
    for template in root.findall("template"):
        name = _text(template.find("name"))
        data[name] = {
            _text(location.find("name"))
            for location in template.findall("location")
        }
    return data


def _query_lines(queries: str) -> list[str]:
    return [line.strip() for line in queries.splitlines() if line.strip()]


def _location_name_by_id(template: ET.Element, ref: str) -> str:
    for location in template.findall("location"):
        if location.attrib.get("id") == ref:
            return _text(location.find("name"))
    return ""
