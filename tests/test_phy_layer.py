import asyncio
import json
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from uppaal_mcp.phy.alpha import (
    check_boundary_policy,
    check_no_continuous_guards,
    default_profile,
    validate_threshold_policy,
)
from uppaal_mcp.phy.defaults import build_default_contract
from uppaal_mcp.phy.extractor import analyze_latex
from uppaal_mcp.phy.generator import generate_uppaal_model
from uppaal_mcp.phy.ir import PhyContractModel
from uppaal_mcp.phy.layout import validate_generated_layout
from uppaal_mcp.phy.scenarios import generate_scenario_model, list_scenarios
from uppaal_mcp.phy.tools import (
    check_channel_semantics,
    explain_counterexample,
    export_diagram,
    extract_contract,
    export_property_pack,
    export_report,
    export_run_artifacts,
    generate_diagram,
    phy_get_benchmark,
    phy_list_benchmarks,
    phy_validate_benchmarks,
    generate_property_pack,
    generate_report,
    verify_property_pack,
)
from uppaal_mcp.phy.trace import classify_failed_query, normalize_verifyta_output, parse_trace_text
from uppaal_mcp.phy.validators import validate_contract_ir, validate_generated_model
from uppaal_mcp.validation import validate_model_text


ROOT = Path(__file__).resolve().parents[1]
ARTICLE_TEX = ROOT / "levels_tex" / "PHY_level_formalization_reviewed-2026-06-06-143000.tex"
FIXTURES = ROOT / "tests" / "fixtures"


class PhyLayerTests(unittest.TestCase):
    def test_default_contract_has_closed_system_components(self) -> None:
        contract = build_default_contract()
        self.assertEqual(contract.phy_components, ["A_CH", "A_SIG", "A_BM", "A_SQ", "A_PH"])
        self.assertEqual(contract.env_components, ["ENV_CH", "ENV_TARGET", "ENV_MAC", "ENV_NET"])
        self.assertTrue({item.name for item in contract.env} >= {"ENV_CH", "ENV_TARGET", "ENV_MAC", "ENV_NET"})
        self.assertIn("ChannelClass", {item.name for item in contract.variables})
        roundtrip = PhyContractModel.from_dict(contract.to_dict())
        self.assertEqual(len(roundtrip.variables), len(contract.variables))
        self.assertEqual(len(roundtrip.env), len(contract.env))
        report = validate_contract_ir(contract)
        self.assertTrue(report.ok, report.errors)

    def test_generated_model_contains_required_templates_and_queries(self) -> None:
        generated = generate_uppaal_model()
        report = validate_generated_model(generated.model_xml, generated.queries)
        self.assertTrue(report.ok, report.errors)
        self.assertEqual(generated.generation_mode, "with_observers")
        self.assertEqual(generated.layout, "readable")
        self.assertTrue(generated.layout_validation["ok"], generated.layout_validation["errors"])
        self.assertIn("coordinate convention", generated.model_map)
        self.assertIn("Channel classifier", generated.template_map)
        self.assertIn("handshake command", generated.channels_map)
        for name in ("A_CH", "A_SIG", "A_BM", "A_SQ", "A_PH", "ENV_CH", "ENV_TARGET", "ENV_MAC", "ENV_NET"):
            self.assertIn(name, generated.model_xml)
        self.assertIn("A[] not deadlock", generated.queries)
        self.assertIn("A[] not ObsBeamRecovery.Violation", generated.queries)
        for sync in ("phy_outage!", "channel_degraded!", "mobility_alert!", "multipath_alert!", "blockage_detected!", "signal_degraded!", "degradation_event!"):
            self.assertIn(sync, generated.model_xml)

    def test_generation_modes_minimal_and_negative_scenarios(self) -> None:
        minimal = generate_uppaal_model(mode="minimal")
        self.assertEqual(minimal.generation_mode, "minimal")
        self.assertNotIn("ObsBeamRecovery", minimal.model_xml)
        self.assertNotIn("ch_enabled_count <= 1", minimal.queries)
        minimal_report = validate_generated_model(minimal.model_xml, minimal.queries, require_observers=False)
        self.assertTrue(minimal_report.ok, minimal_report.errors)
        negative = generate_uppaal_model(mode="with_negative_scenarios")
        self.assertTrue(negative.include_negative_scenarios)
        self.assertIn("Negative scenarios are emitted by the benchmark suite", negative.model_xml)
        extended = generate_uppaal_model(mode="with_extended_observers")
        self.assertTrue(extended.include_extended_observers)
        self.assertIn("ObsChannelReport = Template_ObsChannelReport();", extended.model_xml)
        self.assertIn("A[] not ObsPhyKpiReport.Violation", extended.queries)
        extended_report = validate_generated_model(extended.model_xml, extended.queries)
        self.assertTrue(extended_report.ok, extended_report.errors)

    def test_open_system_mode_excludes_environment_and_wraps_queries(self) -> None:
        generated = generate_uppaal_model(mode="open_system")
        self.assertEqual(generated.system_mode, "open")
        self.assertNotIn("ENV_CH = Template_ENV_CH();", generated.model_xml)
        self.assertIn("A[] (ass_env() imply (not deadlock))", generated.queries)
        report = validate_generated_model(
            generated.model_xml,
            generated.queries,
            require_environment=False,
        )
        self.assertTrue(report.ok, report.errors)
        bare_deadlock = validate_generated_model(
            generated.model_xml,
            "A[] not deadlock\n",
            require_environment=False,
        )
        self.assertFalse(bare_deadlock.ok)
        self.assertTrue(any("closed A_SYS" in item for item in bare_deadlock.errors), bare_deadlock.errors)

    def test_alpha_rejects_continuous_guard_tokens(self) -> None:
        report = check_no_continuous_guards("guard SINR_c < SINR_min")
        self.assertFalse(report.ok)
        self.assertIn("SINR_c", report.errors[0])

    def test_profile_policy(self) -> None:
        self.assertTrue(validate_threshold_policy(default_profile()).ok)
        report = validate_threshold_policy({"boundary_policy": "optimistic", "deadlines": {}})
        self.assertFalse(report.ok)
        boundary = check_boundary_policy({
            "boundary_policy": "worse_class",
            "boundary_policy_overrides": {"PdClass": "better_class"},
        })
        self.assertFalse(boundary.ok)
        self.assertTrue(any("PdClass" in item for item in boundary.errors), boundary.errors)

    def test_extract_contract_returns_serializable_ir(self) -> None:
        data = extract_contract(tex_text=r"\A{PHY} \A{ENV} \A{SYS} \alpha_{PHY} A_CH A_SIG A_BM A_SQ A_PH ENV_CH ENV_TARGET ENV_MAC ENV_NET Observer")
        self.assertEqual(data["phy_components"], ["A_CH", "A_SIG", "A_BM", "A_SQ", "A_PH"])
        self.assertIn("extractor", data)

    def test_article_latex_extractor_has_complete_evidence(self) -> None:
        text = ARTICLE_TEX.read_text(encoding="utf-8")
        report = analyze_latex(text)
        self.assertTrue(report.ok, report.diagnostics)
        self.assertEqual(len(report.class_sets), 28)
        self.assertEqual(len(report.channels), 45)
        self.assertEqual(len(report.queries), 17)
        self.assertIn("A_SYS", report.marker_lines)
        self.assertIn("A_ENV", report.marker_lines)
        self.assertEqual(report.compositions["A_PHY"]["components"], ["A_CH", "A_SIG", "A_BM", "A_SQ", "A_PH"])
        self.assertEqual(report.compositions["A_SYS"]["components"], ["A_PHY", "A_ENV"])
        self.assertEqual(report.compositions["A_ENV"]["components"], ["ENV_CH", "ENV_TARGET", "ENV_MAC", "ENV_NET"])
        self.assertEqual(report.x_disc["variables"], [item.name for item in build_default_contract().classes])
        self.assertEqual(report.clock_resets["c_rec"]["reset"], "вход в BeamRecover")
        self.assertEqual(report.invariants["BeamRecover"]["formula"], "c_rec <= D_BM")
        self.assertIn("MeasurePending", report.automata_sketches["A_CH"]["locations"])
        self.assertGreaterEqual(report.automata_sketches["A_CH"]["transition_count"], 6)
        self.assertIn("TickWait", "\n".join(report.env_sketches["ENV_CH"]["statements"]))
        self.assertIn("channel_report!", report.assume_guarantee["A_CH"]["guarantee"])

    def test_article_contract_golden_fixture(self) -> None:
        actual = extract_contract(tex_path=str(ARTICLE_TEX))
        actual_text = json.dumps(actual, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        expected_text = (FIXTURES / "phy_contract_article.golden.json").read_text(encoding="utf-8")
        self.assertEqual(actual_text, expected_text)

    def test_article_generated_model_and_queries_golden_fixtures(self) -> None:
        contract = PhyContractModel.from_dict(extract_contract(tex_path=str(ARTICLE_TEX)))
        generated = generate_uppaal_model(contract, layout="readable")
        expected_model = (FIXTURES / "phy_model_article.readable.golden.xml").read_text(encoding="utf-8")
        expected_queries = (FIXTURES / "phy_queries_article.golden.q").read_text(encoding="utf-8")
        self.assertEqual(generated.model_xml, expected_model)
        self.assertEqual(generated.queries, expected_queries)
        compact = generate_uppaal_model(contract, layout="compact")
        compact_report = validate_generated_model(compact.model_xml, compact.queries)
        self.assertTrue(compact_report.ok, compact_report.errors)
        self.assertFalse(validate_generated_layout(compact.model_xml).ok)

    def test_readable_layout_keeps_locations_labels_and_loops_apart(self) -> None:
        generated = generate_uppaal_model(layout="readable")
        layout_report = validate_generated_layout(generated.model_xml)
        self.assertTrue(layout_report.ok, layout_report.errors)
        root = ET.fromstring(generated.model_xml)
        template = _template_by_name(root, "Template_A_CH")
        points = _location_points(template)
        self.assertLess(points["ChannelNominal"][0], points["ContractViolation_CH"][0])
        self.assertLess(points["Outage"][1], points["ChannelNominal"][1])
        self.assertGreater(points["MeasurePending"][1], points["ChannelNominal"][1])
        for template_name in ("Template_A_CH", "Template_A_SIG", "Template_A_BM", "Template_A_SQ", "Template_A_PH"):
            template = _template_by_name(root, template_name)
            self.assertGreater(len({point[1] for point in _location_points(template).values()}), 1)
            for transition in template.findall("transition"):
                label_points = [
                    (label.attrib["x"], label.attrib["y"])
                    for label in transition.findall("label")
                    if "x" in label.attrib and "y" in label.attrib
                ]
                self.assertEqual(len(label_points), len(set(label_points)))
        self.assertTrue(_has_self_loop_nail(root, "Template_A_CH", "ChannelNominal"))
        self.assertTrue(_has_self_loop_nail(root, "Template_A_PH", "PHYCommunicationDegraded"))

    def test_diagram_export_includes_dot_svg_and_maps(self) -> None:
        generated = generate_uppaal_model()
        diagram = generate_diagram(model_xml=generated.model_xml, contract_json=generated.contract)
        self.assertTrue(diagram["layout_validation"]["ok"], diagram["layout_validation"])
        self.assertIn("digraph PHY", diagram["model.dot"])
        self.assertIn("<svg", diagram["model.svg"])
        self.assertIn("PHY Channels Map", diagram["channels_map.md"])
        with tempfile.TemporaryDirectory() as tmp:
            exported = export_diagram(
                output_dir=tmp,
                model_xml=generated.model_xml,
                contract_json=generated.contract,
            )
            names = {Path(item).name for item in exported["files"]}
            for name in ("model_map.md", "template_map.md", "channels_map.md", "model.dot", "model.svg", "layout_validation.json"):
                self.assertIn(name, names)

    def test_article_latex_extractor_flags_missing_a_env(self) -> None:
        text = ARTICLE_TEX.read_text(encoding="utf-8")
        broken = (
            text.replace(r"\A{ENV}", "AENVREMOVED")
            .replace("A_ENV", "AENVREMOVED")
            .replace("ENV_CH", "ENVCHREMOVED")
            .replace(r"ENV\_CH", "ENVCHREMOVED")
        )
        report = analyze_latex(broken)
        self.assertFalse(report.ok)
        self.assertTrue(any("A_ENV" in item for item in report.diagnostics), report.diagnostics)
        self.assertTrue(any("ENV_CH" in item for item in report.diagnostics), report.diagnostics)

    def test_negative_waveform_location_fixture_is_rejected(self) -> None:
        generated = generate_uppaal_model()
        broken = generated.model_xml.replace(">SignalNominal</name>", ">OFDM</name>", 1)
        report = validate_generated_model(broken, generated.queries)
        self.assertFalse(report.ok)
        self.assertTrue(any("waveform OFDM" in item for item in report.errors), report.errors)

    def test_property_pack_includes_contract_and_observer_queries(self) -> None:
        generated = generate_uppaal_model()
        pack = generate_property_pack(
            model_xml=generated.model_xml,
            profile=generated.profile,
            include_negative=True,
        )
        self.assertIn("A[] (ass_ch() imply not A_CH.ContractViolation_CH)", pack["queries"])
        self.assertIn("A[] not ObsFreshness.Violation", pack["queries"])
        self.assertTrue(pack["model_validation"]["ok"], pack["model_validation"]["errors"])
        self.assertEqual(pack["summary"]["query_count"], 17)
        self.assertEqual(pack["queries_json"][0]["name"], "deadlock_free")
        self.assertEqual(pack["queries_json"][0]["section"], "properties")
        self.assertIn("negative_property_pack", pack)
        self.assertEqual(pack["negative_property_pack"]["count"], 5)

    def test_property_pack_export_writes_queries_and_metadata(self) -> None:
        contract = extract_contract(tex_path=str(ARTICLE_TEX))
        with tempfile.TemporaryDirectory() as tmp:
            result = export_property_pack(
                output_dir=tmp,
                contract_json=contract,
                include_negative=True,
            )
            names = {Path(item).name for item in result["files"]}
            self.assertIn("queries.q", names)
            self.assertIn("queries.json", names)
            self.assertIn("property_pack.json", names)
            self.assertIn("negative_property_pack.json", names)
            self.assertEqual(result["summary"]["query_count"], 17)

    def test_verify_property_pack_static_only(self) -> None:
        generated = generate_uppaal_model()
        result = verify_property_pack(
            model_xml=generated.model_xml,
            queries=generated.queries,
            static_only=True,
        )
        self.assertEqual(result["status"], "validated")
        self.assertTrue(result["static_validation"]["ok"], result["static_validation"])

    def test_channel_semantics_check_accepts_generated_model(self) -> None:
        generated = generate_uppaal_model()
        report = check_channel_semantics(model_xml=generated.model_xml, contract_json=generated.contract)
        self.assertTrue(report["ok"], report["errors"])

    def test_generated_model_validator_rejects_missing_priority_helper(self) -> None:
        generated = generate_uppaal_model()
        broken = generated.model_xml.replace("int highest_priority_CH()", "int removed_priority_CH()", 1)
        report = validate_generated_model(broken)
        self.assertFalse(report.ok)
        self.assertTrue(any("highest_priority_CH" in item for item in report.errors), report.errors)

    def test_generated_model_validator_rejects_active_observer_sync(self) -> None:
        generated = generate_uppaal_model()
        broken = generated.model_xml.replace("sensing_degraded?", "sensing_degraded!", 1)
        report = validate_generated_model(broken)
        self.assertFalse(report.ok)
        self.assertTrue(any("listen passively" in item for item in report.errors), report.errors)

    def test_generated_model_validator_rejects_wrong_report_variable_writer(self) -> None:
        generated = generate_uppaal_model()
        broken = generated.model_xml.replace(
            "ChannelClass = highest_priority_CH()",
            "ChannelClass = highest_priority_CH(), PHYState = PHYSTATE_PHYFAILURE",
            1,
        )
        report = validate_generated_model(broken)
        self.assertFalse(report.ok)
        self.assertTrue(any("writes PHYState" in item for item in report.errors), report.errors)

    def test_generated_model_validator_rejects_bad_beam_failure_timeout(self) -> None:
        generated = generate_uppaal_model()
        broken = generated.model_xml.replace("c_rec == D_BM", "c_rec &lt;= D_BM", 1)
        report = validate_generated_model(broken)
        self.assertFalse(report.ok)
        self.assertTrue(any("beam_failure" in item and "c_rec == D_BM" in item for item in report.errors), report.errors)

    def test_generated_model_validator_rejects_bad_query_references(self) -> None:
        generated = generate_uppaal_model()
        report = validate_generated_model(generated.model_xml, "E<> A_PH.NoSuchLocation\n")
        self.assertFalse(report.ok)
        self.assertTrue(any("A_PH.NoSuchLocation" in item for item in report.errors), report.errors)

    def test_generated_model_validator_rejects_unbounded_leads_to_query(self) -> None:
        generated = generate_uppaal_model()
        report = validate_generated_model(generated.model_xml, "A_PH.PHYNormal --> A_PH.PHYFailure\n")
        self.assertFalse(report.ok)
        self.assertTrue(any("Unbounded leads-to" in item for item in report.errors), report.errors)

    def test_generated_model_validator_rejects_estimator_values_in_transition_guards(self) -> None:
        generated = generate_uppaal_model()
        broken = generated.model_xml.replace("env_scenario == SCENARIO_NORMAL", "SINR_c &lt; SINR_min", 1)
        report = validate_generated_model(broken, generated.queries)
        self.assertFalse(report.ok)
        self.assertTrue(any("estimator-derived value SINR_c" in item for item in report.errors), report.errors)

    def test_generated_model_validator_rejects_report_and_alert_on_one_transition(self) -> None:
        generated = generate_uppaal_model()
        broken = generated.model_xml.replace("channel_report!", "channel_report!, channel_degraded!", 1)
        report = validate_generated_model(broken, generated.queries)
        self.assertFalse(report.ok)
        self.assertTrue(any("combines multiple sync events" in item for item in report.errors), report.errors)

    def test_generated_model_validator_rejects_missing_report_deadline_guard(self) -> None:
        generated = generate_uppaal_model()
        broken = generated.model_xml.replace(" &amp;&amp; c_meas &lt;= D_meas", "", 1)
        report = validate_generated_model(broken, generated.queries)
        self.assertFalse(report.ok)
        self.assertTrue(any("c_meas <= D_meas" in item for item in report.errors), report.errors)

    def test_generated_model_validator_rejects_missing_sensing_dependencies(self) -> None:
        generated = generate_uppaal_model()
        broken = generated.model_xml.replace("ChannelClass", "ChannelClassRemoved").replace("SignalClass", "SignalClassRemoved")
        report = validate_generated_model(broken, generated.queries)
        self.assertFalse(report.ok)
        self.assertTrue(any("highest_priority_SQ()" in item and "ChannelClass" in item for item in report.errors), report.errors)

    def test_generated_model_validator_rejects_bad_contract_violation_guard(self) -> None:
        generated = generate_uppaal_model()
        broken = generated.model_xml.replace("!ass_ch()", "ass_ch()")
        report = validate_generated_model(broken, generated.queries)
        self.assertFalse(report.ok)
        self.assertTrue(any("!ass_ch()" in item for item in report.errors), report.errors)

    def test_generated_model_validator_rejects_undeclared_and_dangling_channel(self) -> None:
        generated = generate_uppaal_model()
        broken = generated.model_xml.replace("power_cmd?", "power_cmd_missing?")
        report = validate_generated_model(broken)
        self.assertFalse(report.ok)
        self.assertTrue(any("undeclared channel power_cmd_missing" in item for item in report.errors), report.errors)
        self.assertTrue(any("power_cmd has no receiver" in item for item in report.errors), report.errors)

    def test_generated_model_validator_rejects_bad_class_range(self) -> None:
        generated = generate_uppaal_model()
        broken = generated.model_xml.replace("typedef int[0,3] SINRClassT;", "typedef int[0,99] SINRClassT;", 1)
        report = validate_generated_model(broken)
        self.assertFalse(report.ok)
        self.assertTrue(any("SINRClass" in item and "bounded int" in item for item in report.errors), report.errors)

    def test_report_bundle_and_export_artifacts(self) -> None:
        contract = extract_contract(tex_path=str(ARTICLE_TEX))
        generated = generate_uppaal_model()
        bundle = generate_report(
            contract_json=contract,
            model_xml=generated.model_xml,
            queries=generated.queries,
            profile=generated.profile,
        )
        self.assertIn("report.md", bundle["reports"])
        self.assertIn("traceability_matrix.md", bundle["reports"])
        self.assertIn("publication_tables.md", bundle["reports"])
        self.assertIn("model_map.md", bundle["reports"])
        self.assertIn("template_map.md", bundle["reports"])
        self.assertIn("channels_map.md", bundle["reports"])
        self.assertIn("properties.csv", bundle["reports"])
        self.assertIn("Property | Category | Query", bundle["reports"]["report.md"])
        self.assertIn("A_SYS = A_PHY || A_ENV", bundle["reports"]["traceability_matrix.md"])
        self.assertIn("coordinate convention", bundle["reports"]["model_map.md"])
        with tempfile.TemporaryDirectory() as tmp:
            exported = export_report(
                output_dir=tmp,
                contract_json=contract,
                model_xml=generated.model_xml,
                queries=generated.queries,
                profile=generated.profile,
            )
            names = {Path(item).name for item in exported["files"]}
            self.assertIn("contract.json", names)
            self.assertIn("model.xml", names)
            self.assertIn("queries.q", names)
            self.assertIn("coverage_report.md", names)
            self.assertIn("publication_tables.md", names)
            self.assertIn("properties.csv", names)
            self.assertIn("model_map.md", names)
            self.assertIn("template_map.md", names)
            self.assertIn("channels_map.md", names)

    def test_run_artifact_export_writes_layout_and_uses_cache_key(self) -> None:
        contract = extract_contract(tex_path=str(ARTICLE_TEX))
        generated = generate_uppaal_model()
        result_json = {
            "status": "satisfied",
            "query_results": [{"formula": "A[] not deadlock", "status": "satisfied"}],
        }
        trace_text = "State: ObsBeamRecovery.Violation A_BM.BeamRecover\n"
        with tempfile.TemporaryDirectory() as tmp:
            first = export_run_artifacts(
                output_root=tmp,
                contract_json=contract,
                tex_path=str(ARTICLE_TEX),
                model_xml=generated.model_xml,
                queries=generated.queries,
                result_json=result_json,
                trace_text=trace_text,
                profile=generated.profile,
                verifyta_version="UPPAAL 5.0.0",
            )
            self.assertFalse(first["cache_hit"])
            self.assertTrue(first["cache_key"])
            self.assertIn("model_hash", first["metadata"]["hashes"])
            names = {Path(item).name for item in first["files"]}
            for name in ("source.tex", "contract.json", "model.xml", "queries.q", "results.json", "trace.txt", "trace_explanation.md", "report.md", "model_map.md", "template_map.md", "channels_map.md", "run_metadata.json"):
                self.assertIn(name, names)
            second = export_run_artifacts(
                output_root=tmp,
                contract_json=contract,
                tex_path=str(ARTICLE_TEX),
                model_xml=generated.model_xml,
                queries=generated.queries,
                result_json=result_json,
                trace_text=trace_text,
                profile=generated.profile,
                verifyta_version="UPPAAL 5.0.0",
            )
            self.assertTrue(second["cache_hit"])
            self.assertEqual(first["cache_key"], second["cache_key"])
            self.assertEqual(first["metadata"]["created_at"], second["metadata"]["created_at"])

    def test_compact_observer_scenarios_generate_valid_models(self) -> None:
        names = [item["name"] for item in list_scenarios()]
        self.assertIn("obs_beam_recovery_success", names)
        self.assertTrue(all(item["timeout_sec"] > 0 for item in list_scenarios()))
        for name in names:
            with self.subTest(name=name):
                scenario = generate_scenario_model(name)
                self.assertGreater(scenario["timeout_sec"], 0)
                report = validate_model_text(scenario["model_xml"], scenario["queries"])
                self.assertTrue(report.ok, report.errors)
                self.assertIn("A[] not Obs", scenario["queries"])

    def test_benchmark_suite_covers_positive_and_broken_models(self) -> None:
        names = {item["name"] for item in phy_list_benchmarks()}
        for name in (
            "nominal_phy",
            "channel_outage",
            "interference_limited",
            "mobility_limited",
            "multipath_limited",
            "signal_reconfiguring",
            "signal_limited",
            "beam_recovery_success",
            "beam_handover_hint",
            "beam_failure_timeout",
            "sensing_probability_limited",
            "sensing_freshness_limited",
            "sensing_failure",
            "phy_communication_degraded",
            "phy_sensing_degraded",
            "phy_joint_degraded",
            "broken_report_channel_declared_as_chan",
            "broken_continuous_guard",
            "broken_c_rec_gt_d_bm",
            "broken_phy_state_outside_a_ph",
            "broken_missing_a_env",
        ):
            self.assertIn(name, names)
        summary = phy_validate_benchmarks()
        self.assertTrue(summary["ok"], summary)
        self.assertEqual(summary["count"], 21)

    def test_benchmark_models_expose_expected_static_validation(self) -> None:
        positive = phy_get_benchmark("nominal_phy")
        self.assertTrue(positive["static_ok"], positive["semantic_validation"])
        self.assertIn("BENCHMARK_SCENARIO", positive["model_xml"])
        broken = phy_get_benchmark("broken_missing_a_env")
        self.assertFalse(broken["static_ok"])
        self.assertTrue(any("ENV_CH" in item for item in broken["semantic_validation"]["errors"]))

    def test_trace_normalizer_and_failed_query_classifier(self) -> None:
        normalized = normalize_verifyta_output(
            {
                "status": "not_satisfied",
                "stdout": "Verifying formula 1 at queries.q:1\n -- Formula is NOT satisfied.\n",
                "stderr": "",
            }
        )
        self.assertEqual(normalized["events"][-1]["status"], "not_satisfied")
        classified = classify_failed_query("A[] not ObsBeamRecovery.Violation")
        self.assertEqual(classified["counterexample_type"], "deadline_violation")
        self.assertIn("beam recovery", classified["domain"])

    def test_trace_parser_extracts_domain_root_cause(self) -> None:
        trace = """
State: Driver.Start ObsBeamRecovery.Idle A_BM.BeamRecover
Transition: Driver.Start -> Driver.Wait sync recovery_start! update BeamClass = BEAMCLASS_RECOVERING
Delay: 6
State: ObsBeamRecovery.Violation A_BM.BeamRecover
update BeamClass = BEAMCLASS_FAILED
"""
        parsed = parse_trace_text(trace)
        self.assertTrue(parsed["ok"], parsed["diagnostics"])
        self.assertIn("ObsBeamRecovery.Violation", parsed["locations_seen"])
        self.assertIn("recovery_start!", parsed["syncs_seen"])
        self.assertEqual(parsed["class_values"]["BeamClass"], "BEAMCLASS_FAILED")
        self.assertEqual(parsed["classification"], "possible_physical_scenario")
        self.assertEqual(parsed["deadline_violation"]["deadline"], "D_BM")
        self.assertEqual(parsed["beam_recovery"]["outcome_status"], "missing")
        self.assertTrue(any("Recovery was triggered" in item for item in parsed["root_cause_candidates"]))

    def test_trace_parser_extracts_textual_root_causes(self) -> None:
        parsed = parse_trace_text("deadlock: blocked handshake on recovery_cmd; impossible guard in A_BM; ContractViolation_BM")
        joined = "\n".join(parsed["root_cause_candidates"])
        self.assertIn("Deadlock", joined)
        self.assertIn("Blocked handshake", joined)
        self.assertIn("Impossible guard", joined)
        self.assertIn("Contract violation", joined)
        self.assertEqual(parsed["classification"], "environment_assumption_violation")

    def test_trace_parser_classifies_abstraction_artifact_and_freshness(self) -> None:
        parsed = parse_trace_text(
            "alpha over-approximation: State: ObsFreshness.Violation A_SQ.FreshnessLimited\n"
            "Transition: ENV_NET.Wait -> ENV_NET.Tick sync aos_ctrl_expired!\n"
            "update AoS_BS = 3 AoS_CTRL = 12 AoSClass = AOSCLASS_EXPIRED ChannelClass = CHANNELCLASS_OUTAGE\n"
        )
        self.assertEqual(parsed["classification"], "abstraction_artifact")
        self.assertTrue(parsed["replay_hints"], parsed)
        self.assertEqual(parsed["freshness"]["AoS_CTRL_minus_AoS_BS"], 9.0)
        self.assertEqual(parsed["deadline_violation"]["deadline"], "D_sense")

    def test_explain_counterexample_uses_parsed_trace(self) -> None:
        trace = """
State: ObsBeamRecovery.Idle A_BM.BeamRecover
Transition: Driver.Start -> Driver.Wait sync recovery_start!
Delay: 6
State: ObsBeamRecovery.Violation A_BM.BeamRecover
"""
        explanation = explain_counterexample(
            result_json={
                "status": "not_satisfied",
                "query_results": [
                    {
                        "formula": "A[] not ObsBeamRecovery.Violation",
                        "status": "not_satisfied",
                    }
                ],
                "stdout": "Verifying formula 1\n -- Formula is NOT satisfied.\n",
            },
            trace_text=trace,
        )
        self.assertEqual(explanation["counterexample_type"], "deadline_violation")
        self.assertEqual(explanation["counterexample_classification"], "modeling_error")
        self.assertIsNotNone(explanation["parsed_trace"])
        self.assertTrue(any("Recovery was triggered" in item for item in explanation["reasons"]))


class PhyMcpRegistrationTests(unittest.TestCase):
    def test_phy_tools_are_registered_when_mcp_is_installed(self) -> None:
        from uppaal_mcp.server import build_mcp
        try:
            mcp = build_mcp()
        except RuntimeError:
            self.skipTest("mcp package is not installed")
        tools = asyncio.run(mcp.list_tools())
        names = {tool.name for tool in tools}
        self.assertIn("phy_extract_contract", names)
        self.assertIn("phy_generate_uppaal_model", names)
        self.assertIn("phy_verify_contract", names)
        self.assertIn("phy_verify_property_pack", names)
        self.assertIn("phy_export_run_artifacts", names)
        self.assertIn("phy_export_property_pack", names)
        self.assertIn("phy_generate_report", names)
        self.assertIn("phy_export_report", names)
        self.assertIn("phy_check_channel_semantics", names)
        self.assertIn("phy_validate_layout", names)
        self.assertIn("phy_export_diagram", names)
        self.assertIn("phy_verify_scenario", names)
        self.assertIn("phy_list_benchmarks", names)
        self.assertIn("phy_get_benchmark", names)
        self.assertIn("phy_validate_benchmarks", names)


def _template_by_name(root: ET.Element, name: str) -> ET.Element:
    for template in root.findall("template"):
        if template.findtext("name") == name:
            return template
    raise AssertionError(f"Missing template {name}")


def _location_points(template: ET.Element) -> dict[str, tuple[int, int]]:
    return {
        location.findtext("name") or "": (
            int(location.attrib["x"]),
            int(location.attrib["y"]),
        )
        for location in template.findall("location")
    }


def _has_self_loop_nail(root: ET.Element, template_name: str, location_name: str) -> bool:
    template = _template_by_name(root, template_name)
    location_id = None
    for location in template.findall("location"):
        if location.findtext("name") == location_name:
            location_id = location.attrib["id"]
            break
    if location_id is None:
        return False
    for transition in template.findall("transition"):
        source = transition.find("source")
        target = transition.find("target")
        if source is None or target is None:
            continue
        if source.attrib.get("ref") == location_id and target.attrib.get("ref") == location_id:
            return bool(transition.findall("nail"))
    return False


if __name__ == "__main__":
    unittest.main()
