from __future__ import annotations

import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from uppaal_mcp.layers import available_layer_adapters
from uppaal_mcp.sdn.alpha import check_no_continuous_guards, default_profile, validate_threshold_policy
from uppaal_mcp.sdn.benchmarks import generate_benchmark_model, validate_all_benchmarks
from uppaal_mcp.sdn.extractor import extract_contract_model
from uppaal_mcp.sdn.generator import generate_uppaal_model
from uppaal_mcp.sdn.ir import SdnContractModel
from uppaal_mcp.sdn.layout import validate_generated_layout
from uppaal_mcp.sdn.property_pack import generate_property_pack
from uppaal_mcp.sdn.reports import generate_report_bundle
from uppaal_mcp.sdn.tools import generate_uppaal_from_contract, verify_property_pack
from uppaal_mcp.sdn.validators import validate_contract_ir, validate_generated_model
from uppaal_mcp.validation import validate_model_text


ROOT = Path(__file__).resolve().parents[1]
SDN_TEX = ROOT / "levels_tex" / "SDN_RIC_control_plane_formalization.tex"


class SdnLayerTests(unittest.TestCase):
    def test_extract_contract_from_article(self) -> None:
        contract = extract_contract_model(SDN_TEX.read_text(encoding="utf-8"), source_name=SDN_TEX.name)
        self.assertTrue(contract["extractor"]["ok"], contract["extractor"]["diagnostics"])
        self.assertEqual(contract["sdn_components"], ["A_MON", "A_RISK", "A_POLICY", "A_RULE", "A_REC", "A_SDN_AGG"])
        self.assertEqual(contract["env_components"], ["A_ENV_SDN"])
        self.assertIn("A_SDN", contract["extractor"]["compositions"])
        self.assertIn("POL_REJECT", contract["extractor"]["policies_found"])
        self.assertIn("service_admission", contract["extractor"]["interfaces_found"])

    def test_contract_validation(self) -> None:
        contract = SdnContractModel.from_dict(extract_contract_model(SDN_TEX.read_text(encoding="utf-8")))
        report = validate_contract_ir(contract)
        self.assertTrue(report.ok, report.errors)

    def test_generated_model_validates_static_and_generic(self) -> None:
        generated = generate_uppaal_model()
        semantic = validate_generated_model(generated.model_xml, generated.queries)
        self.assertTrue(semantic.ok, semantic.errors)
        generic = validate_model_text(generated.model_xml, generated.queries)
        self.assertTrue(generic.ok, generic.errors)
        self.assertIn("Template_A_POLICY", generic.templates)
        self.assertIn("A[] not ObsRuleMiss.Violation", generic.queries)

    def test_generation_modes(self) -> None:
        minimal = generate_uppaal_from_contract(tex_path=str(SDN_TEX), mode="minimal")
        self.assertTrue(minimal["semantic_validation"]["ok"], minimal["semantic_validation"]["errors"])
        self.assertNotIn("Template_ObsRuleMiss", minimal["model_xml"])
        open_system = generate_uppaal_from_contract(tex_path=str(SDN_TEX), mode="open_system")
        self.assertTrue(open_system["semantic_validation"]["ok"], open_system["semantic_validation"]["errors"])
        self.assertNotIn("A_ENV_SDN = Template_A_ENV_SDN();", open_system["model_xml"])
        self.assertNotIn("A[] not deadlock", open_system["queries"])
        optional_sec = generate_uppaal_from_contract(tex_path=str(SDN_TEX), mode="with_optional_sec")
        self.assertTrue(optional_sec["semantic_validation"]["ok"], optional_sec["semantic_validation"]["errors"])
        self.assertIn("Template_A_SEC", optional_sec["model_xml"])

    def test_alpha_profile_and_raw_guard_rejection(self) -> None:
        self.assertTrue(validate_threshold_policy(default_profile()).ok)
        generated = generate_uppaal_model()
        self.assertTrue(check_no_continuous_guards(generated.model_xml).ok)
        self.assertFalse(check_no_continuous_guards('<label kind="guard">raw_delay &gt; 5</label>').ok)

    def test_property_pack_and_static_verify(self) -> None:
        generated = generate_uppaal_model()
        pack = generate_property_pack(model_xml=generated.model_xml, include_negative=True)
        self.assertIn("negative_property_pack", pack)
        self.assertIn("stale_telemetry", pack["static_checks"])
        result = verify_property_pack(model_xml=generated.model_xml, queries=generated.queries, static_only=True)
        self.assertEqual(result["status"], "validated")

    def test_reports_include_interface_artifacts(self) -> None:
        generated = generate_uppaal_model()
        reports = generate_report_bundle(contract_json=generated.contract, model_xml=generated.model_xml, queries=generated.queries)
        self.assertIn("interface_report.md", reports["reports"])
        self.assertIn("interface_map.md", reports["reports"])

    def test_readable_layout_has_separated_labels_and_loop_lanes(self) -> None:
        generated = generate_uppaal_model(layout="readable")
        report = validate_generated_layout(generated.model_xml)
        self.assertTrue(report.ok, report.errors)
        self.assertEqual(report.warnings, [])
        root = ET.fromstring(generated.model_xml)
        for template in root.findall("template"):
            for transition in template.findall("transition"):
                label_points = [
                    (label.attrib["x"], label.attrib["y"])
                    for label in transition.findall("label")
                    if "x" in label.attrib and "y" in label.attrib
                ]
                self.assertEqual(len(label_points), len(set(label_points)))
                source = transition.find("source")
                target = transition.find("target")
                if source is not None and target is not None and source.attrib.get("ref") == target.attrib.get("ref"):
                    self.assertTrue(transition.findall("nail"))

    def test_benchmark_suite_positive_and_broken(self) -> None:
        result = validate_all_benchmarks()
        self.assertTrue(result["ok"], result["results"])
        broken = generate_benchmark_model("broken_stale_optimistic_reconfig")
        self.assertFalse(broken["validation"]["ok"])
        self.assertIn("optimistic_reconfig", ";".join(broken["validation"]["errors"]))

    def test_layer_adapter_registry_contains_sdn(self) -> None:
        adapters = available_layer_adapters()
        self.assertIn("sdn", adapters)
        self.assertEqual(adapters["sdn"].source_name, "SDN_RIC_control_plane_formalization.tex")

    def test_article_golden_fixtures(self) -> None:
        readable = generate_uppaal_from_contract(tex_path=str(SDN_TEX), layout="readable")
        compact = generate_uppaal_from_contract(tex_path=str(SDN_TEX), layout="compact")
        self.assertEqual(readable["model_xml"], (ROOT / "tests/fixtures/sdn_model_article.readable.golden.xml").read_text(encoding="utf-8"))
        self.assertEqual(compact["model_xml"], (ROOT / "tests/fixtures/sdn_model_article.golden.xml").read_text(encoding="utf-8"))
        self.assertEqual(readable["queries"], (ROOT / "tests/fixtures/sdn_queries_article.golden.q").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
