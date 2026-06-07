from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field


@dataclass
class NormalizedEvent:
    kind: str
    text: str
    formula_index: int | None = None
    status: str | None = None


@dataclass
class NormalizedVerifytaOutput:
    status: str
    events: list[NormalizedEvent] = field(default_factory=list)
    stderr_tail: str = ""

    def to_dict(self) -> dict:
        data = asdict(self)
        data["events"] = [asdict(item) for item in self.events]
        return data


@dataclass
class TraceEvent:
    kind: str
    text: str
    time: float | None = None
    automaton: str | None = None
    location: str | None = None
    source: str | None = None
    target: str | None = None
    sync: str | None = None
    updates: dict[str, str] = field(default_factory=dict)
    meaning: str | None = None


@dataclass
class ParsedTrace:
    ok: bool
    events: list[TraceEvent] = field(default_factory=list)
    locations_seen: list[str] = field(default_factory=list)
    syncs_seen: list[str] = field(default_factory=list)
    class_values: dict[str, str] = field(default_factory=dict)
    root_cause_candidates: list[str] = field(default_factory=list)
    classification: str = "unknown"
    deadline_violation: dict[str, object] | None = None
    beam_recovery: dict[str, object] = field(default_factory=dict)
    freshness: dict[str, object] = field(default_factory=dict)
    replay_hints: list[str] = field(default_factory=list)
    modeling_errors: list[str] = field(default_factory=list)
    diagnostics: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        data = asdict(self)
        data["events"] = [asdict(item) for item in self.events]
        return data


LOCATION_MEANINGS = {
    "A_CH.Outage": "channel outage classification",
    "A_CH.InterferenceLimited": "interference-limited communication channel",
    "A_SIG.SignalLimited": "signal configuration is degraded or unusable",
    "A_BM.BeamRecover": "beam recovery in progress",
    "A_BM.BeamFailed": "beam recovery failed",
    "A_BM.BeamHOAssist": "handover-assisted beam recovery",
    "A_SQ.FreshnessLimited": "controller sensing information is stale",
    "A_SQ.SensingFailure": "sensing quality failure",
    "A_PH.PHYCommunicationDegraded": "aggregate PHY communication degradation",
    "A_PH.PHYSensingDegraded": "aggregate PHY sensing degradation",
    "A_PH.PHYJointDegraded": "aggregate communication and sensing degradation",
    "A_PH.PHYFailure": "aggregate PHY failure",
    "ObsSenseReport.Violation": "PHY KPI report deadline violation",
    "ObsFreshness.Violation": "freshness response deadline violation",
    "ObsBeamRecovery.Violation": "beam recovery outcome deadline violation",
}

CLASS_VALUE_MEANINGS = {
    "PDCLASS_FAILED": "detection probability class failed",
    "PDCLASS_LOW": "detection probability class low",
    "RFACLASS_CRITICAL": "false alarm class critical",
    "AOSCLASS_EXPIRED": "controller Age of Sensing expired",
    "AOSCLASS_STALE": "controller Age of Sensing stale",
    "BEAMCLASS_FAILED": "beam class failed",
    "CHANNELCLASS_OUTAGE": "channel class outage",
    "SENSINGSTATE_FRESHNESSLIMITED": "sensing freshness limited",
    "SENSINGSTATE_SENSINGFAILURE": "sensing failure",
    "PHYSTATE_PHYFAILURE": "PHY failure",
}


def normalize_verifyta_output(result_json: dict) -> dict:
    stdout = result_json.get("stdout") or ""
    stderr = result_json.get("stderr") or ""
    events: list[NormalizedEvent] = []
    current_formula: int | None = None
    for raw in stdout.splitlines():
        line = _strip_ansi(raw).strip()
        if not line:
            continue
        match = re.search(r"Verifying formula\s+(\d+)", line)
        if match:
            current_formula = int(match.group(1))
            events.append(NormalizedEvent(kind="verify_formula", text=line, formula_index=current_formula))
            continue
        lowered = line.lower()
        if "formula is not satisfied" in lowered:
            events.append(NormalizedEvent(kind="formula_result", text=line, formula_index=current_formula, status="not_satisfied"))
        elif "formula is satisfied" in lowered:
            events.append(NormalizedEvent(kind="formula_result", text=line, formula_index=current_formula, status="satisfied"))
        elif "deadlock" in lowered:
            events.append(NormalizedEvent(kind="diagnostic", text=line, formula_index=current_formula))
        elif "error" in lowered:
            events.append(NormalizedEvent(kind="error", text=line, formula_index=current_formula))
    if stderr:
        for raw in stderr.splitlines()[-10:]:
            line = _strip_ansi(raw).strip()
            if line:
                events.append(NormalizedEvent(kind="stderr", text=line))
    return NormalizedVerifytaOutput(
        status=result_json.get("status", "unknown"),
        events=events,
        stderr_tail="\n".join((stderr or "").splitlines()[-10:]),
    ).to_dict()


def parse_trace_text(trace_text: str) -> dict:
    events: list[TraceEvent] = []
    locations_seen: list[str] = []
    syncs_seen: list[str] = []
    class_values: dict[str, str] = {}
    diagnostics: list[str] = []
    current_time: float | None = None

    for raw in trace_text.splitlines():
        line = _strip_ansi(raw).strip()
        if not line:
            continue
        delay = _parse_delay(line)
        if delay is not None:
            current_time = (current_time or 0.0) + delay
            events.append(TraceEvent(kind="delay", text=line, time=current_time))
            continue
        transition = _parse_transition(line, current_time)
        if transition is not None:
            events.append(transition)
            if transition.sync:
                syncs_seen.append(transition.sync)
            class_values.update(transition.updates)
            continue
        state_events = _parse_state_line(line, current_time)
        if state_events:
            events.extend(state_events)
            for item in state_events:
                if item.location:
                    locations_seen.append(f"{item.automaton}.{item.location}")
            continue
        updates = _parse_assignments(line)
        if updates:
            class_values.update(updates)
            events.append(TraceEvent(kind="update", text=line, time=current_time, updates=updates))
            continue
        if any(token in line for token in ("Violation", "deadlock", "not satisfied")):
            events.append(TraceEvent(kind="diagnostic", text=line, time=current_time))

    root_causes = _root_cause_candidates(locations_seen, syncs_seen, class_values)
    root_causes = _unique([*root_causes, *_textual_root_causes(trace_text)])
    analysis = _analyze_counterexample_trace(events, locations_seen, syncs_seen, class_values, trace_text)
    if not events and trace_text.strip():
        diagnostics.append("Trace text was provided but no recognizable trace events were parsed.")
    return ParsedTrace(
        ok=not diagnostics,
        events=events,
        locations_seen=_unique(locations_seen),
        syncs_seen=_unique(syncs_seen),
        class_values=class_values,
        root_cause_candidates=root_causes,
        classification=analysis["classification"],
        deadline_violation=analysis["deadline_violation"],
        beam_recovery=analysis["beam_recovery"],
        freshness=analysis["freshness"],
        replay_hints=analysis["replay_hints"],
        modeling_errors=analysis["modeling_errors"],
        diagnostics=diagnostics,
    ).to_dict()


def classify_failed_query(formula: str) -> dict:
    if "ObsSenseReport" in formula:
        return {
            "counterexample_type": "deadline_violation",
            "counterexample_classification": "modeling_error",
            "domain": "PHY KPI report deadline after sensing degradation",
            "expected_response": "phy_kpi_report!",
        }
    if "ObsFreshness" in formula:
        return {
            "counterexample_type": "deadline_violation",
            "counterexample_classification": "possible_physical_scenario",
            "domain": "freshness handling after controller AoS expiration",
            "expected_response": "sensing_report! with FreshnessLimited",
        }
    if "ObsBeamRecovery" in formula:
        return {
            "counterexample_type": "deadline_violation",
            "counterexample_classification": "possible_physical_scenario",
            "domain": "beam recovery outcome deadline",
            "expected_response": "beam_restored! or handover_hint! or beam_failure!",
        }
    if "deadlock" in formula:
        return {
            "counterexample_type": "modeling_error",
            "counterexample_classification": "modeling_error",
            "domain": "closed A_SYS progress",
            "expected_response": "some enabled transition or time progress",
        }
    if "ContractViolation" in formula:
        return {
            "counterexample_type": "environment_assumption_violation",
            "counterexample_classification": "environment_assumption_violation",
            "domain": "assume-guarantee contract",
            "expected_response": "no ContractViolation_i under ass_i()",
        }
    return {
        "counterexample_type": "unknown",
        "counterexample_classification": "unknown",
        "domain": "unknown",
        "expected_response": None,
    }


def _strip_ansi(value: str) -> str:
    return re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", value)


def _parse_delay(line: str) -> float | None:
    match = re.search(r"\b(?:delay|Delay|time elapse|Time elapse)\s*:?\s*([0-9]+(?:\.[0-9]+)?)", line)
    if match:
        return float(match.group(1))
    return None


def _parse_transition(line: str, current_time: float | None) -> TraceEvent | None:
    if "->" not in line and "--" not in line:
        sync_only = re.search(r"\b([A-Za-z_]\w*[!?])", line)
        if sync_only and any(word in line.lower() for word in ("transition", "sync")):
            return TraceEvent(kind="transition", text=line, time=current_time, sync=sync_only.group(1))
        return None
    endpoint = re.search(
        r"(?P<source>[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)?)\s*(?:--[^>]*)?->\s*(?P<target>[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)?)",
        line,
    )
    sync = re.search(r"\b([A-Za-z_]\w*[!?])", line)
    updates = _parse_assignments(line)
    source = endpoint.group("source") if endpoint else None
    target = endpoint.group("target") if endpoint else None
    meaning = LOCATION_MEANINGS.get(target or "")
    return TraceEvent(
        kind="transition",
        text=line,
        time=current_time,
        source=source,
        target=target,
        sync=sync.group(1) if sync else None,
        updates=updates,
        meaning=meaning,
    )


def _parse_state_line(line: str, current_time: float | None) -> list[TraceEvent]:
    if not re.search(r"\b(State|state|locations|Locations)\b", line):
        return []
    events = []
    for match in re.finditer(r"\b([A-Za-z_]\w*)\.([A-Za-z_]\w*)\b", line):
        full = f"{match.group(1)}.{match.group(2)}"
        events.append(
            TraceEvent(
                kind="state",
                text=line,
                time=current_time,
                automaton=match.group(1),
                location=match.group(2),
                meaning=LOCATION_MEANINGS.get(full),
            )
        )
    return events


def _parse_assignments(line: str) -> dict[str, str]:
    updates: dict[str, str] = {}
    for match in re.finditer(r"\b([A-Za-z_]\w*)\s*(?::=|=)\s*([A-Za-z_]\w*|[0-9]+(?:\.[0-9]+)?)", line):
        variable = match.group(1)
        value = match.group(2)
        if _looks_like_domain_value(variable, value):
            updates[variable] = value
    return updates


def _looks_like_domain_value(variable: str, value: str) -> bool:
    if variable.endswith("Class") or variable in {"SensingState", "PHYState"}:
        return True
    if variable in {"AoS_BS", "AoS_CTRL"}:
        return True
    return value in CLASS_VALUE_MEANINGS


def _analyze_counterexample_trace(
    events: list[TraceEvent],
    locations: list[str],
    syncs: list[str],
    class_values: dict[str, str],
    trace_text: str,
) -> dict[str, object]:
    modeling_errors = _modeling_error_details(trace_text)
    deadline = _deadline_violation_details(locations, syncs)
    beam = _beam_recovery_details(events, syncs)
    freshness = _freshness_details(class_values, syncs)
    classification = _classify_counterexample(
        locations=locations,
        syncs=syncs,
        class_values=class_values,
        trace_text=trace_text,
        modeling_errors=modeling_errors,
        deadline_violation=deadline,
    )
    replay_hints = _replay_hints(classification, class_values)
    return {
        "classification": classification,
        "deadline_violation": deadline,
        "beam_recovery": beam,
        "freshness": freshness,
        "replay_hints": replay_hints,
        "modeling_errors": modeling_errors,
    }


def _deadline_violation_details(locations: list[str], syncs: list[str]) -> dict[str, object] | None:
    specs = {
        "ObsSenseReport": {
            "trigger": "sensing_degraded",
            "responses": ["phy_kpi_report"],
            "deadline": "D_report",
            "domain": "PHY KPI report after sensing degradation",
        },
        "ObsFreshness": {
            "trigger": "aos_ctrl_expired",
            "responses": ["sensing_report"],
            "deadline": "D_sense",
            "domain": "freshness handling after controller AoS expiration",
        },
        "ObsBeamRecovery": {
            "trigger": "recovery_start",
            "responses": ["beam_restored", "handover_hint", "beam_failure"],
            "deadline": "D_BM",
            "domain": "beam recovery outcome",
        },
    }
    channels = {_sync_channel(item) for item in syncs}
    for observer, spec in specs.items():
        if f"{observer}.Violation" not in set(locations):
            continue
        observed = [name for name in spec["responses"] if name in channels]
        return {
            "observer": observer,
            "domain": spec["domain"],
            "trigger": spec["trigger"],
            "trigger_seen": spec["trigger"] in channels,
            "expected_responses": spec["responses"],
            "observed_responses": observed,
            "deadline": spec["deadline"],
            "actual_path": {
                "locations": _unique(locations)[-12:],
                "syncs": _unique(syncs)[-12:],
            },
        }
    return None


def _beam_recovery_details(events: list[TraceEvent], syncs: list[str]) -> dict[str, object]:
    outcome_channels = {"beam_restored", "handover_hint", "beam_failure"}
    observed = [_sync_channel(item) for item in syncs if _sync_channel(item) in outcome_channels]
    violation_index = _first_event_index(
        events,
        lambda event: event.automaton == "ObsBeamRecovery" and event.location == "Violation",
    )
    outcome_indices = [
        index
        for index, event in enumerate(events)
        if event.sync and _sync_channel(event.sync) in outcome_channels
    ]
    before_violation = [
        _sync_channel(events[index].sync or "")
        for index in outcome_indices
        if violation_index is None or index < violation_index
    ]
    after_violation = [
        _sync_channel(events[index].sync or "")
        for index in outcome_indices
        if violation_index is not None and index > violation_index
    ]
    if not observed:
        outcome_status = "missing"
    elif violation_index is not None and not before_violation and after_violation:
        outcome_status = "late"
    elif before_violation:
        outcome_status = "observed_before_violation"
    else:
        outcome_status = "observed"
    return {
        "triggered": any(_sync_channel(item) == "recovery_start" for item in syncs),
        "expected_outcomes": sorted(outcome_channels),
        "observed_outcomes": _unique(observed),
        "outcomes_before_violation": _unique(before_violation),
        "outcomes_after_violation": _unique(after_violation),
        "outcome_status": outcome_status,
    }


def _freshness_details(class_values: dict[str, str], syncs: list[str]) -> dict[str, object]:
    aos_bs = _float_or_none(class_values.get("AoS_BS"))
    aos_ctrl = _float_or_none(class_values.get("AoS_CTRL"))
    difference = None if aos_bs is None or aos_ctrl is None else aos_ctrl - aos_bs
    return {
        "AoSClass": class_values.get("AoSClass"),
        "AoS_BS": class_values.get("AoS_BS"),
        "AoS_CTRL": class_values.get("AoS_CTRL"),
        "AoS_CTRL_minus_AoS_BS": difference,
        "aos_ctrl_expired_seen": any(_sync_channel(item) == "aos_ctrl_expired" for item in syncs),
        "sensing_report_seen": any(_sync_channel(item) == "sensing_report" for item in syncs),
    }


def _classify_counterexample(
    *,
    locations: list[str],
    syncs: list[str],
    class_values: dict[str, str],
    trace_text: str,
    modeling_errors: list[str],
    deadline_violation: dict[str, object] | None,
) -> str:
    text = trace_text.lower()
    location_set = set(locations)
    if "contractviolation" in text or any("ContractViolation" in item for item in location_set):
        return "environment_assumption_violation"
    if "alpha" in text or "over-approx" in text or "impossible class" in text:
        return "abstraction_artifact"
    if modeling_errors:
        return "modeling_error"
    if _has_severe_physical_class(class_values) or _has_physical_degradation_location(location_set):
        return "possible_physical_scenario"
    if deadline_violation:
        return "modeling_error"
    return "unknown"


def _modeling_error_details(trace_text: str) -> list[str]:
    text = trace_text.lower()
    details: list[str] = []
    if "deadlock" in text:
        details.append("deadlock/progress mismatch")
    if "blocked handshake" in text or ("handshake" in text and "blocked" in text):
        details.append("blocked command/report handshake")
    if "impossible guard" in text or "unreachable guard" in text:
        details.append("impossible guard or unreachable clock/class predicate")
    if "non-broadcast" in text or "channel mismatch" in text:
        details.append("channel declaration/synchronisation mismatch")
    if "invariant" in text and "violation" in text:
        details.append("invariant/deadline encoding mismatch")
    return details


def _replay_hints(classification: str, class_values: dict[str, str]) -> list[str]:
    if classification != "abstraction_artifact":
        return []
    replay_values = {
        key: value
        for key, value in class_values.items()
        if key.endswith("Class") or key in {"SensingState", "PHYState"}
    }
    if not replay_values:
        return ["Replay the estimator/simulator layer for the trace segment that produced the abstract class combination."]
    combination = ", ".join(f"{key}={value}" for key, value in sorted(replay_values.items()))
    return [f"Replay estimator/simulator layer for class combination: {combination}."]


def _has_severe_physical_class(class_values: dict[str, str]) -> bool:
    severe_tokens = {
        "FAILED",
        "CRITICAL",
        "OUTAGE",
        "EXPIRED",
        "UNUSABLE",
        "STARVED",
        "EXCESSIVE",
    }
    return any(any(token in value for token in severe_tokens) for value in class_values.values())


def _has_physical_degradation_location(locations: set[str]) -> bool:
    severe_locations = {
        "A_CH.Outage",
        "A_BM.BeamFailed",
        "A_SQ.SensingFailure",
        "A_PH.PHYFailure",
        "A_PH.PHYJointDegraded",
    }
    return bool(locations & severe_locations)


def _first_event_index(events: list[TraceEvent], predicate: object) -> int | None:
    for index, event in enumerate(events):
        if predicate(event):  # type: ignore[operator]
            return index
    return None


def _sync_channel(sync: str) -> str:
    return sync[:-1] if sync.endswith(("!", "?")) else sync


def _float_or_none(value: str | None) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _root_cause_candidates(locations: list[str], syncs: list[str], class_values: dict[str, str]) -> list[str]:
    causes: list[str] = []
    location_set = set(locations)
    sync_set = set(syncs)
    if "ObsBeamRecovery.Violation" in location_set:
        if "recovery_start?" in sync_set or "recovery_start!" in sync_set:
            causes.append("Recovery was triggered but no beam_restored/handover_hint/beam_failure outcome was observed before D_BM.")
        else:
            causes.append("Beam recovery observer reached Violation; check recovery_start trigger and outcome broadcasts.")
    if "ObsFreshness.Violation" in location_set:
        if class_values.get("AoSClass") in {"AOSCLASS_STALE", "AOSCLASS_EXPIRED"}:
            causes.append("Controller AoS became stale/expired and no valid FreshnessLimited sensing_report arrived before D_sense.")
        else:
            causes.append("Freshness observer reached Violation; check aos_ctrl_expired and sensing_report response.")
    if "ObsSenseReport.Violation" in location_set:
        causes.append("Sensing degradation was not followed by phy_kpi_report before D_report.")
    if "A_BM.BeamFailed" in location_set or class_values.get("BeamClass") == "BEAMCLASS_FAILED":
        causes.append("Beam management reached failed class; replay blockage/misalignment estimator inputs.")
    if "A_CH.Outage" in location_set or class_values.get("ChannelClass") == "CHANNELCLASS_OUTAGE":
        causes.append("Channel outage class was present; this may be a physical scenario or conservative alpha_PHY over-approximation.")
    for variable, value in sorted(class_values.items()):
        meaning = CLASS_VALUE_MEANINGS.get(value)
        if meaning:
            causes.append(f"{variable}={value}: {meaning}.")
    return _unique(causes)


def _textual_root_causes(trace_text: str) -> list[str]:
    text = trace_text.lower()
    causes: list[str] = []
    if "deadlock" in text:
        causes.append("Deadlock was reported; inspect blocked handshakes, invariants, and environment progress.")
    if "blocked handshake" in text or ("handshake" in text and "blocked" in text):
        causes.append("Blocked handshake candidate; check command sender/receiver pairing and open-vs-closed model mode.")
    if "impossible guard" in text or "unreachable guard" in text:
        causes.append("Impossible guard candidate; inspect class priority predicates and clock constraints.")
    if "contractviolation" in text or "contract violation" in text:
        causes.append("Contract violation candidate; inspect environment assumptions and ass_*/gar_* predicates.")
    if "late" in text and "report" in text:
        causes.append("Late report candidate; inspect observer deadline and report-channel path.")
    return causes


def _unique(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item not in seen:
            result.append(item)
            seen.add(item)
    return result
