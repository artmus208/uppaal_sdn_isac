from __future__ import annotations

from dataclasses import asdict, dataclass

from .alpha import default_profile
from .generator import UppaalXmlBuilder


@dataclass(frozen=True)
class PhyScenario:
    name: str
    description: str
    category: str
    expected_status: str
    timeout_sec: float = 10.0

    def to_dict(self) -> dict:
        return asdict(self)


SCENARIOS = [
    PhyScenario(
        name="obs_sense_report_success",
        description="sensing_degraded? is followed by phy_kpi_report? before D_report.",
        category="observer",
        expected_status="satisfied",
    ),
    PhyScenario(
        name="obs_sense_report_violation",
        description="sensing_degraded? is not followed by phy_kpi_report?; ObsSenseReport must reach Violation.",
        category="observer-negative",
        expected_status="not_satisfied",
    ),
    PhyScenario(
        name="obs_freshness_success",
        description="aos_ctrl_expired? is followed by sensing_report? with FreshnessLimited before D_sense.",
        category="observer",
        expected_status="satisfied",
    ),
    PhyScenario(
        name="obs_freshness_violation",
        description="aos_ctrl_expired? is not followed by a valid FreshnessLimited sensing_report? before D_sense.",
        category="observer-negative",
        expected_status="not_satisfied",
    ),
    PhyScenario(
        name="obs_beam_recovery_success",
        description="recovery_start? is followed by beam_restored? before D_BM.",
        category="observer",
        expected_status="satisfied",
    ),
    PhyScenario(
        name="obs_beam_recovery_violation",
        description="recovery_start? has no recovery outcome before D_BM; ObsBeamRecovery must reach Violation.",
        category="observer-negative",
        expected_status="not_satisfied",
    ),
]


def list_scenarios() -> list[dict]:
    return [item.to_dict() for item in SCENARIOS]


def get_scenario(name: str) -> PhyScenario:
    for item in SCENARIOS:
        if item.name == name:
            return item
    known = ", ".join(item.name for item in SCENARIOS)
    raise KeyError(f"Unknown PHY scenario {name!r}. Known scenarios: {known}.")


def generate_scenario_model(name: str, profile: dict | None = None) -> dict:
    scenario = get_scenario(name)
    profile = profile or default_profile()
    deadlines = profile["deadlines"]
    if name.startswith("obs_sense_report"):
        return _observer_scenario(
            scenario=scenario,
            profile=profile,
            trigger="sensing_degraded",
            responses=["phy_kpi_report"],
            deadline_name="D_report",
            deadline_value=int(deadlines["D_report"]),
            observer_name="ObsSenseReport",
            success=name.endswith("_success"),
            query="A[] not ObsSenseReport.Violation",
        )
    if name.startswith("obs_freshness"):
        return _observer_scenario(
            scenario=scenario,
            profile=profile,
            trigger="aos_ctrl_expired",
            responses=["sensing_report"],
            deadline_name="D_sense",
            deadline_value=int(deadlines["D_sense"]),
            observer_name="ObsFreshness",
            success=name.endswith("_success"),
            query="A[] not ObsFreshness.Violation",
            response_assignment="SensingState = SENSINGSTATE_FRESHNESSLIMITED",
            response_guard="SensingState == SENSINGSTATE_FRESHNESSLIMITED",
            trigger_assignment="SensingState = SENSINGSTATE_FRESHNESSLIMITED",
            extra_declarations="typedef int[0,1] SensingStateT;\nconst int SENSINGSTATE_SENSINGQOSOK = 0;\nconst int SENSINGSTATE_FRESHNESSLIMITED = 1;\nSensingStateT SensingState = SENSINGSTATE_SENSINGQOSOK;",
        )
    if name.startswith("obs_beam_recovery"):
        return _observer_scenario(
            scenario=scenario,
            profile=profile,
            trigger="recovery_start",
            responses=["beam_restored", "handover_hint", "beam_failure"],
            deadline_name="D_BM",
            deadline_value=int(deadlines["D_BM"]),
            observer_name="ObsBeamRecovery",
            success=name.endswith("_success"),
            query="A[] not ObsBeamRecovery.Violation",
            chosen_response="beam_restored",
        )
    raise AssertionError(f"Unhandled scenario {name}")


def _observer_scenario(
    *,
    scenario: PhyScenario,
    profile: dict,
    trigger: str,
    responses: list[str],
    deadline_name: str,
    deadline_value: int,
    observer_name: str,
    success: bool,
    query: str,
    chosen_response: str | None = None,
    response_assignment: str | None = None,
    trigger_assignment: str | None = None,
    response_guard: str | None = None,
    extra_declarations: str = "",
) -> dict:
    builder = UppaalXmlBuilder()
    all_channels = sorted(set([trigger, *responses]))
    builder.declaration(
        "\n".join(
            [
                f"const int {deadline_name} = {deadline_value};",
                "clock c_obs, c_driver;",
                f"broadcast chan {', '.join(all_channels)};",
                extra_declarations,
            ]
        )
    )
    _add_driver(
        builder,
        trigger=trigger,
        response=chosen_response or responses[0],
        deadline_name=deadline_name,
        success=success,
        response_assignment=response_assignment,
        trigger_assignment=trigger_assignment,
    )
    _add_compact_observer(
        builder,
        observer_name=observer_name,
        trigger=trigger,
        responses=responses,
        deadline_name=deadline_name,
        response_guard=response_guard,
    )
    builder.system(
        "\n".join(
            [
                "Driver = Template_Driver();",
                f"{observer_name} = Template_{observer_name}();",
                f"system Driver, {observer_name};",
            ]
        )
    )
    return {
        "name": scenario.name,
        "description": scenario.description,
        "expected_status": scenario.expected_status,
        "timeout_sec": scenario.timeout_sec,
        "model_xml": builder.to_xml(),
        "queries": query + "\n",
        "profile": profile,
    }


def _add_driver(
    builder: UppaalXmlBuilder,
    *,
    trigger: str,
    response: str,
    deadline_name: str,
    success: bool,
    response_assignment: str | None,
    trigger_assignment: str | None,
) -> None:
    wait_invariant = f"c_driver <= {deadline_name}" if success else None
    template = builder.template(
        "Template_Driver",
        "Start",
        [
            ("Start", None),
            ("WaitResponse", wait_invariant),
            ("Done", None),
        ],
    )
    trigger_updates = "c_driver = 0"
    if trigger_assignment:
        trigger_updates = f"{trigger_updates}, {trigger_assignment}"
    builder.add_transition(template, "Start", "WaitResponse", sync=f"{trigger}!", assignment=trigger_updates)
    if success:
        builder.add_transition(
            template,
            "WaitResponse",
            "Done",
            guard=f"c_driver <= {deadline_name}",
            sync=f"{response}!",
            assignment=response_assignment,
        )
    builder.add_transition(template, "Done", "Done")


def _add_compact_observer(
    builder: UppaalXmlBuilder,
    *,
    observer_name: str,
    trigger: str,
    responses: list[str],
    deadline_name: str,
    response_guard: str | None,
) -> None:
    template = builder.template(
        f"Template_{observer_name}",
        "Idle",
        [
            ("Idle", None),
            ("Wait", None),
            ("Violation", None),
        ],
    )
    builder.add_transition(template, "Idle", "Wait", sync=f"{trigger}?", assignment="c_obs = 0")
    for response in responses:
        guard = f"c_obs <= {deadline_name}"
        if response_guard:
            guard = f"{guard} && {response_guard}"
        builder.add_transition(template, "Wait", "Idle", guard=guard, sync=f"{response}?")
    builder.add_transition(template, "Wait", "Violation", guard=f"c_obs > {deadline_name}")
    builder.add_transition(template, "Idle", "Idle")
    builder.add_transition(template, "Violation", "Violation")
