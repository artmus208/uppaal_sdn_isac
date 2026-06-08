from __future__ import annotations

import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from uppaal_mcp.mac.alpha import check_no_continuous_guards, default_profile, validate_threshold_policy
from uppaal_mcp.mac.benchmarks import generate_benchmark_model, validate_all_benchmarks
from uppaal_mcp.mac.extractor import extract_contract_model
from uppaal_mcp.mac.generator import generate_uppaal_model
from uppaal_mcp.mac.ir import MacContractModel
from uppaal_mcp.mac.layout import validate_generated_layout
from uppaal_mcp.mac.property_pack import generate_property_pack
from uppaal_mcp.mac.reports import generate_report_bundle
from uppaal_mcp.mac.tools import generate_uppaal_from_contract, verify_property_pack
from uppaal_mcp.mac.validators import validate_contract_ir, validate_generated_model
from uppaal_mcp.validation import validate_model_text


ROOT = Path(__file__).resolve().parents[1]
MAC_TEX = ROOT / "levels_tex" / "MAC_resource_scheduling_formalization.tex"


class MacLayerTests(unittest.TestCase):
    def test_extract_contract_from_article(self) -> None:
        contract = extract_contract_model(MAC_TEX.read_text(encoding="utf-8"), source_name=MAC_TEX.name)
        self.assertTrue(contract["extractor"]["ok"], contract["extractor"]["diagnostics"])
        self.assertEqual(contract["mac_components"], ["A_SCH", "A_Q", "A_BUF", "A_RSRC", "A_MAC_AGG"])
        self.assertEqual(contract["env_components"], ["A_ENV_MAC"])
        self.assertIn("A_MAC", contract["extractor"]["compositions"])
        self.assertIn("P7", contract["extractor"]["policies_found"])

    def test_contract_validation(self) -> None:
        contract = MacContractModel.from_dict(extract_contract_model(MAC_TEX.read_text(encoding="utf-8")))
        report = validate_contract_ir(contract)
        self.assertTrue(report.ok, report.errors)

    def test_generated_model_validates_static_and_generic(self) -> None:
        generated = generate_uppaal_model()
        semantic = validate_generated_model(generated.model_xml, generated.queries)
        self.assertTrue(semantic.ok, semantic.errors)
        generic = validate_model_text(generated.model_xml, generated.queries)
        self.assertTrue(generic.ok, generic.errors)
        self.assertIn("Template_A_SCH", generic.templates)
        self.assertIn("A[] not deadlock", generic.queries)

    def test_generation_modes(self) -> None:
        minimal = generate_uppaal_from_contract(tex_path=str(MAC_TEX), mode="minimal")
        self.assertTrue(minimal["semantic_validation"]["ok"], minimal["semantic_validation"]["errors"])
        self.assertNotIn("Template_ObsPhyAck", minimal["model_xml"])
        debug = generate_uppaal_from_contract(tex_path=str(MAC_TEX), mode="with_debug_counters")
        self.assertTrue(debug["semantic_validation"]["ok"], debug["semantic_validation"]["errors"])
        self.assertIn("policy_enabled_count", debug["queries"])

    def test_alpha_profile_and_continuous_guard_rejection(self) -> None:
        self.assertTrue(validate_threshold_policy(default_profile()).ok)
        generated = generate_uppaal_model()
        self.assertTrue(check_no_continuous_guards(generated.model_xml).ok)
        broken = generated.model_xml.replace("queueClass == Q_CRIT", "queue_length_raw > 100", 1)
        self.assertFalse(check_no_continuous_guards(broken).ok)

    def test_property_pack_and_static_verify(self) -> None:
        generated = generate_uppaal_model()
        pack = generate_property_pack(model_xml=generated.model_xml, include_negative=True)
        self.assertIn("negative_property_pack", pack)
        result = verify_property_pack(model_xml=generated.model_xml, queries=generated.queries, static_only=True)
        self.assertEqual(result["status"], "validated")

    def test_reports_include_policy_map(self) -> None:
        generated = generate_uppaal_model()
        reports = generate_report_bundle(
            contract_json=generated.contract,
            model_xml=generated.model_xml,
            queries=generated.queries,
        )
        self.assertIn("policy_report.md", reports["reports"])
        self.assertIn("policy_map.md", reports["reports"])

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
        broken = generate_benchmark_model("broken_continuous_guard")
        self.assertFalse(broken["validation"]["ok"])
        self.assertIn("queue_length_raw", ";".join(broken["validation"]["errors"]))

    def test_article_golden_fixtures(self) -> None:
        generated = generate_uppaal_from_contract(tex_path=str(MAC_TEX))
        self.assertEqual(
            generated["model_xml"],
            (ROOT / "tests/fixtures/mac_model_article.golden.xml").read_text(encoding="utf-8"),
        )
        self.assertEqual(
            generated["queries"],
            (ROOT / "tests/fixtures/mac_queries_article.golden.q").read_text(encoding="utf-8"),
        )


if __name__ == "__main__":
    unittest.main()
