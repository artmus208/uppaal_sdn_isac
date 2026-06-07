from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass, field

from .alpha import default_profile
from .generator import GeneratedPhyModel, generate_uppaal_model
from .validators import validate_generated_model


@dataclass(frozen=True)
class BenchmarkScenario:
    name: str
    description: str
    category: str
    queries: list[str]
    forced_scenario: str | None = None
    expected_static_ok: bool = True
    expected_validation_error: str | None = None
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


BENCHMARKS: list[BenchmarkScenario] = [
    BenchmarkScenario(
        name="nominal_phy",
        description="Closed A_SYS under nominal environment class updates.",
        category="positive",
        forced_scenario="SCENARIO_NORMAL",
        queries=["A[] not deadlock", "E<> A_PH.PHYNormal"],
    ),
    BenchmarkScenario(
        name="channel_outage",
        description="Channel outage reaches A_CH.Outage and aggregate joint degradation.",
        category="positive",
        forced_scenario="SCENARIO_JOINT_DEGRADED",
        queries=["E<> A_CH.Outage", "E<> A_PH.PHYJointDegraded"],
    ),
    BenchmarkScenario(
        name="interference_limited",
        description="Interference-limited channel path reaches A_CH.InterferenceLimited.",
        category="positive",
        forced_scenario="SCENARIO_COMM_DEGRADED",
        queries=["E<> A_CH.InterferenceLimited", "E<> A_PH.PHYCommunicationDegraded"],
    ),
    BenchmarkScenario(
        name="mobility_limited",
        description="Mobility-limited channel path reaches A_CH.MobilityLimited.",
        category="positive",
        forced_scenario="SCENARIO_SENSING_DEGRADED",
        queries=["E<> A_CH.MobilityLimited"],
        metadata={"required_env_updates": ["DopplerClass = DOPPLERCLASS_HIGH"]},
    ),
    BenchmarkScenario(
        name="multipath_limited",
        description="Multipath-limited channel benchmark profile.",
        category="positive-static",
        forced_scenario="SCENARIO_SENSING_DEGRADED",
        queries=["E<> A_CH.MultipathLimited"],
        metadata={"required_env_updates": ["DelaySpreadClass = DELAYSPREADCLASS_HIGH"]},
    ),
    BenchmarkScenario(
        name="signal_reconfiguring",
        description="Signal reconfiguration path after MAC/SDN config command.",
        category="positive",
        forced_scenario="SCENARIO_NORMAL",
        queries=["E<> A_SIG.SignalReconfiguring"],
    ),
    BenchmarkScenario(
        name="signal_limited",
        description="Signal-limited path after failed payload/DRT/BLER classes.",
        category="positive-static",
        forced_scenario="SCENARIO_COMM_DEGRADED",
        queries=["E<> A_SIG.SignalLimited"],
        metadata={"required_env_updates": ["BLERClass = BLERCLASS_CRITICAL", "DRTClass = DRTCLASS_BAD"]},
    ),
    BenchmarkScenario(
        name="beam_recovery_success",
        description="Beam recovery reaches restored outcome before D_BM.",
        category="positive",
        forced_scenario="SCENARIO_NORMAL",
        queries=["E<> A_BM.BeamLock", "A[] (A_BM.BeamRecover imply c_rec <= D_BM)"],
    ),
    BenchmarkScenario(
        name="beam_handover_hint",
        description="Beam recovery handover-assist outcome benchmark.",
        category="positive",
        forced_scenario="SCENARIO_COMM_DEGRADED",
        queries=["E<> A_BM.BeamHOAssist"],
    ),
    BenchmarkScenario(
        name="beam_failure_timeout",
        description="Beam recovery timeout outcome reaches A_BM.BeamFailed.",
        category="positive",
        forced_scenario="SCENARIO_JOINT_DEGRADED",
        queries=["E<> A_BM.BeamFailed"],
    ),
    BenchmarkScenario(
        name="sensing_probability_limited",
        description="Low detection probability benchmark for sensing quality.",
        category="positive-static",
        forced_scenario="SCENARIO_SENSING_DEGRADED",
        queries=["E<> A_SQ.ProbabilityLimited"],
        metadata={"required_env_updates": ["PdClass = PDCLASS_LOW"]},
    ),
    BenchmarkScenario(
        name="sensing_freshness_limited",
        description="Stale Age of Sensing reaches A_SQ.FreshnessLimited.",
        category="positive",
        forced_scenario="SCENARIO_SENSING_DEGRADED",
        queries=["E<> A_SQ.FreshnessLimited"],
    ),
    BenchmarkScenario(
        name="sensing_failure",
        description="Failed sensing classes reach A_SQ.SensingFailure.",
        category="positive",
        forced_scenario="SCENARIO_JOINT_DEGRADED",
        queries=["E<> A_SQ.SensingFailure"],
    ),
    BenchmarkScenario(
        name="phy_communication_degraded",
        description="Aggregate communication degradation benchmark.",
        category="positive",
        forced_scenario="SCENARIO_COMM_DEGRADED",
        queries=["E<> A_PH.PHYCommunicationDegraded"],
    ),
    BenchmarkScenario(
        name="phy_sensing_degraded",
        description="Aggregate sensing degradation benchmark.",
        category="positive",
        forced_scenario="SCENARIO_SENSING_DEGRADED",
        queries=["E<> A_PH.PHYSensingDegraded"],
    ),
    BenchmarkScenario(
        name="phy_joint_degraded",
        description="Aggregate joint degradation benchmark.",
        category="positive",
        forced_scenario="SCENARIO_JOINT_DEGRADED",
        queries=["E<> A_PH.PHYJointDegraded"],
    ),
    BenchmarkScenario(
        name="broken_report_channel_declared_as_chan",
        description="Intentionally broken model: report/event channels are not broadcast.",
        category="negative-static",
        expected_static_ok=False,
        expected_validation_error="broadcast chan",
        queries=["A[] not deadlock"],
    ),
    BenchmarkScenario(
        name="broken_continuous_guard",
        description="Intentionally broken model: continuous SINR_c appears in a guard.",
        category="negative-static",
        expected_static_ok=False,
        expected_validation_error="SINR_c",
        queries=["A[] not deadlock"],
    ),
    BenchmarkScenario(
        name="broken_c_rec_gt_d_bm",
        description="Intentionally broken model: BeamRecover uses c_rec > D_BM.",
        category="negative-static",
        expected_static_ok=False,
        expected_validation_error="c_rec > D_BM",
        queries=["A[] not deadlock"],
    ),
    BenchmarkScenario(
        name="broken_phy_state_outside_a_ph",
        description="Intentionally broken model: A_CH writes PHYState.",
        category="negative-static",
        expected_static_ok=False,
        expected_validation_error="writes PHYState",
        queries=["A[] not deadlock"],
    ),
    BenchmarkScenario(
        name="broken_missing_a_env",
        description="Intentionally broken model: closed system misses ENV templates/instances.",
        category="negative-static",
        expected_static_ok=False,
        expected_validation_error="ENV_CH",
        queries=["A[] not deadlock"],
    ),
]


def list_benchmarks() -> list[dict]:
    return [item.to_dict() for item in BENCHMARKS]


def get_benchmark(name: str) -> BenchmarkScenario:
    for item in BENCHMARKS:
        if item.name == name:
            return item
    known = ", ".join(item.name for item in BENCHMARKS)
    raise KeyError(f"Unknown PHY benchmark {name!r}. Known benchmarks: {known}.")


def generate_benchmark_model(name: str, profile: dict | None = None) -> dict:
    benchmark = get_benchmark(name)
    profile = profile or default_profile()
    generated = generate_uppaal_model(profile=profile, include_observers=True)
    model_xml = _force_scenario(generated.model_xml, benchmark)
    model_xml = _apply_negative_mutation(model_xml, benchmark)
    queries = "\n".join(benchmark.queries) + "\n"
    validation = validate_generated_model(model_xml, queries).to_dict()
    return {
        "name": benchmark.name,
        "description": benchmark.description,
        "category": benchmark.category,
        "expected_static_ok": benchmark.expected_static_ok,
        "expected_validation_error": benchmark.expected_validation_error,
        "forced_scenario": benchmark.forced_scenario,
        "metadata": dict(benchmark.metadata),
        "model_xml": model_xml,
        "queries": queries,
        "profile": profile,
        "semantic_validation": validation,
        "static_ok": validation["ok"],
        "ok": validation["ok"] == benchmark.expected_static_ok and _expected_error_seen(validation, benchmark),
    }


def validate_all_benchmarks(profile: dict | None = None) -> dict:
    results = [
        _without_model_payload(generate_benchmark_model(item.name, profile=profile))
        for item in BENCHMARKS
    ]
    return {
        "ok": all(item["ok"] for item in results),
        "count": len(results),
        "results": results,
    }


def _force_scenario(model_xml: str, benchmark: BenchmarkScenario) -> str:
    if not benchmark.forced_scenario:
        return model_xml
    scenario = benchmark.forced_scenario
    text = model_xml.replace(
        "int[0,3] env_scenario = SCENARIO_NORMAL;",
        f"const int BENCHMARK_SCENARIO = {scenario};\nint[0,3] env_scenario = BENCHMARK_SCENARIO;",
    )
    text = re.sub(r"env_scenario = SCENARIO_[A-Z_]+", "env_scenario = BENCHMARK_SCENARIO", text)
    if benchmark.metadata.get("required_env_updates"):
        updates = ", ".join(benchmark.metadata["required_env_updates"])
        text = text.replace("TimingOk = true,", f"TimingOk = true, {updates},", 1)
    return text.replace(
        "// Generated from PHY contract IR. Continuous PHY metrics stay outside timed automata.",
        f"// Benchmark scenario: {benchmark.name}\n// Generated from PHY contract IR. Continuous PHY metrics stay outside timed automata.",
    )


def _apply_negative_mutation(model_xml: str, benchmark: BenchmarkScenario) -> str:
    if benchmark.name == "broken_report_channel_declared_as_chan":
        return model_xml.replace("broadcast chan ", "chan ", 1)
    if benchmark.name == "broken_continuous_guard":
        return model_xml.replace("env_scenario == SCENARIO_NORMAL", "SINR_c &lt; SINR_min", 1)
    if benchmark.name == "broken_c_rec_gt_d_bm":
        return model_xml.replace("c_rec == D_BM", "c_rec &gt; D_BM", 1)
    if benchmark.name == "broken_phy_state_outside_a_ph":
        return model_xml.replace(
            "ChannelClass = highest_priority_CH()",
            "ChannelClass = highest_priority_CH(), PHYState = PHYSTATE_PHYFAILURE",
            1,
        )
    if benchmark.name == "broken_missing_a_env":
        return _remove_env_from_model(model_xml)
    return model_xml


def _remove_env_from_model(model_xml: str) -> str:
    root = ET.fromstring(model_xml)
    for template in list(root.findall("template")):
        name = template.findtext("name") or ""
        if name.startswith("Template_ENV"):
            root.remove(template)
    system = root.find("system")
    if system is not None and system.text:
        lines = []
        for line in system.text.splitlines():
            stripped = line.strip()
            if stripped.startswith("ENV_"):
                continue
            if stripped.startswith("system "):
                for env_name in ("ENV_CH", "ENV_TARGET", "ENV_MAC", "ENV_NET"):
                    stripped = stripped.replace(f", {env_name}", "")
                lines.append(stripped)
            else:
                lines.append(line)
        system.text = "\n".join(lines)
    ET.indent(root, space="  ")
    xml_body = ET.tostring(root, encoding="unicode")
    return (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<!DOCTYPE nta PUBLIC "-//Uppaal Team//DTD Flat System 1.6//EN" '
        '"http://www.it.uu.se/research/group/darts/uppaal/flat-1_6.dtd">\n'
        f"{xml_body}\n"
    )


def _expected_error_seen(validation: dict, benchmark: BenchmarkScenario) -> bool:
    if benchmark.expected_static_ok:
        return validation["ok"]
    needle = benchmark.expected_validation_error or ""
    return bool(needle) and any(needle in error for error in validation.get("errors", []))


def _without_model_payload(data: dict) -> dict:
    return {key: value for key, value in data.items() if key not in {"model_xml", "queries"}}
