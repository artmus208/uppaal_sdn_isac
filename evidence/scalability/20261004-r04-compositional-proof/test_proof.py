"""Adversarial controls for the premises on which the scientific argument rests."""

from dataclasses import replace
import itertools
import json
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET

import check_proof as proof


class PremiseMutationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model_path = proof.ROOT / "evidence/scalability/family-series-68/generated/n2/model.xml"
        cls.original = cls.model_path.read_bytes()

    def tree(self):
        tree = ET.fromstring(self.original)
        shared = next(t for t in tree.findall("template") if t.findtext("name") == "SharedLoad")
        writer = next(e for e in shared.findall("transition")
                      if e.findtext("label[@kind='select']") == "server:int[-1,1]")
        return tree, shared, writer

    def rejected(self, tree, reason):
        with self.assertRaisesRegex(proof.PremiseError, reason):
            proof.check_structure(ET.tostring(tree), proof.query_for(2), 2)

    def test_accepted_instances_have_complete_relation_and_expected_counts(self):
        for n in proof.DOMAIN:
            with self.subTest(N=n):
                path = proof.ROOT / f"evidence/scalability/family-series-68/generated/n{n}/model.xml"
                p = proof.check_structure(path.read_bytes(), proof.query_for(n), n)
                graph = proof.explore(p)
                self.assertEqual(49 * n + 1, p.processes)
                self.assertEqual(2 * (n + 1), p.protected_occurrences)
                self.assertEqual(n + 1, graph["reachable_state_count"])
                self.assertEqual((n + 1) ** 2, graph["unique_source_target_pairs_including_self_loops"])
                self.assertEqual((n + 1) * (n + 2), graph["labeled_discrete_edges_including_stutter"])
                self.assertIsNone(graph["native_property_verdict"])

    def test_wrong_grant_rhs_is_rejected(self):
        tree, _, writer = self.tree()
        label = writer.find("label[@kind='assignment']")
        label.text = label.text.replace("family_grant_1=(server == 1)", "family_grant_1=(server == 0)")
        self.rejected(tree, "incorrect grant mapping")

    def test_missing_grant_reset_is_rejected(self):
        tree, _, writer = self.tree()
        label = writer.find("label[@kind='assignment']")
        label.text = label.text.replace("family_grant_1=(server == 1), ", "")
        self.rejected(tree, "all grants")

    def test_duplicate_grant_write_is_rejected(self):
        tree, _, writer = self.tree()
        label = writer.find("label[@kind='assignment']")
        label.text += ", family_grant_0=(server == 0)"
        self.rejected(tree, "duplicate")

    def test_true_initial_grant_is_rejected(self):
        tree, _, _ = self.tree()
        declaration = tree.find("declaration")
        declaration.text = declaration.text.replace("family_grant_1=false", "family_grant_1=true")
        self.rejected(tree, "initial declarations")

    def test_wrong_last_server_initialization_is_rejected(self):
        tree, _, _ = self.tree()
        declaration = tree.find("declaration")
        declaration.text = declaration.text.replace("family_last_server=-1", "family_last_server=0")
        self.rejected(tree, "initial declarations")

    def test_wrong_last_server_update_is_rejected(self):
        tree, _, writer = self.tree()
        label = writer.find("label[@kind='assignment']")
        label.text = label.text.replace("family_last_server=server", "family_last_server=0")
        self.rejected(tree, "unsupported protected update")

    def test_extra_writer_in_other_template_is_rejected(self):
        tree, _, _ = self.tree()
        edge = tree.find("template/transition")
        ET.SubElement(edge, "label", kind="assignment").text = "family_grant_1=true"
        self.rejected(tree, "unaccounted protected reference")

    def test_hidden_function_writer_is_rejected(self):
        tree, _, _ = self.tree()
        tree.find("declaration").text += "\nvoid hidden() { family_grant_0=true; }"
        self.rejected(tree, "protected reference outside")

    def test_by_reference_exposure_is_rejected(self):
        tree, _, _ = self.tree()
        ET.SubElement(tree.find("template/transition"), "label", kind="assignment").text = "mutate(family_grant_0)"
        self.rejected(tree, "unaccounted protected reference")

    def test_local_shadow_is_rejected(self):
        tree, shared, _ = self.tree()
        shared.find("declaration").text += "\nbool family_grant_0=false;"
        self.rejected(tree, "unaccounted protected reference")

    def test_selector_shadow_is_rejected(self):
        tree, shared, _ = self.tree()
        shared.find("declaration").text += "\nint server=0;"
        self.rejected(tree, "selector shadow")

    def test_selector_bound_drift_is_rejected(self):
        tree, _, writer = self.tree()
        writer.find("label[@kind='select']").text = "server:int[-1,2]"
        self.rejected(tree, "selector/domain")

    def test_selector_side_effects_are_rejected(self):
        for inserted in ("server=0", "server++", "x=mutate(server)", "x=(server=0)"):
            with self.subTest(update=inserted):
                tree, _, writer = self.tree()
                label = writer.find("label[@kind='assignment']")
                label.text = inserted + ", " + label.text
                self.rejected(tree, "selector is modified|side effect|function call|nested assignment")

    def test_writer_synchronization_is_rejected(self):
        tree, _, writer = self.tree()
        ET.SubElement(writer, "label", kind="synchronisation").text = "channel!"
        self.rejected(tree, "writer must be internal")

    def test_split_writer_is_rejected_even_with_committed_intermediate_location(self):
        tree, shared, writer = self.tree()
        label = writer.find("label[@kind='assignment']")
        label.text = label.text.replace("family_grant_1=(server == 1), ", "")
        location = ET.SubElement(shared, "location", id="intermediate")
        ET.SubElement(location, "committed")
        writer.find("target").set("ref", "intermediate")
        edge = ET.SubElement(shared, "transition")
        ET.SubElement(edge, "source", ref="intermediate")
        ET.SubElement(edge, "target", ref="shared_Publish_0")
        ET.SubElement(edge, "label", kind="assignment").text = "family_grant_1=false"
        self.rejected(tree, "exactly one protected writer")

    def test_hooks_and_external_code_are_rejected(self):
        for code in ("void __ON_CONSTRUCT__() {}", "void __before_update() {}", "import \"other\";"):
            with self.subTest(code=code):
                tree, _, _ = self.tree()
                tree.find("declaration").text += "\n" + code
                self.rejected(tree, "external code or lifecycle hook")

    def test_extra_process_instance_is_rejected(self):
        tree, _, _ = self.tree()
        system = tree.find("system")
        system.text = "other = SharedLoad();\n" + system.text.replace("system ", "system other, ")
        self.rejected(tree, "one shared_load instance")

    def test_system_parameter_alias_is_rejected(self):
        tree, _, _ = self.tree()
        system = tree.find("system")
        system.text = system.text.replace("SharedLoad()", "SharedLoad(family_grant_0)")
        self.rejected(tree, "unaccounted protected reference")

    def test_extra_protected_field_in_xml_attribute_is_rejected(self):
        tree, _, _ = self.tree()
        tree.set("extension", "family_grant_0=true")
        self.rejected(tree, "unaccounted protected reference")

    def test_unsupported_xml_and_dtd_are_rejected(self):
        tree, _, _ = self.tree()
        ET.SubElement(tree, "foreign")
        self.rejected(tree, "unsupported XML")
        with self.assertRaisesRegex(proof.PremiseError, "DTD"):
            proof.check_structure(b'<!DOCTYPE nta []>' + self.original, proof.query_for(2), 2)

    def test_query_drift_and_unaccepted_N_are_rejected(self):
        with self.assertRaisesRegex(proof.PremiseError, "query differs"):
            proof.check_structure(self.original, proof.query_for(2).replace("<= 1", "<= 2"), 2)
        with self.assertRaisesRegex(proof.PremiseError, "finite domain"):
            proof.check_structure(self.original, proof.query_for(5), 5)

    def test_unsafe_paths_and_hash_drift_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "input").write_bytes(b"changed")
            with self.assertRaisesRegex(proof.PremiseError, "hash mismatch"):
                proof.pinned(root, "input", proof.digest(b"original"))
            with self.assertRaisesRegex(proof.PremiseError, "escapes"):
                proof.pinned(root, "../outside", "irrelevant")
            with self.assertRaisesRegex(proof.PremiseError, "absolute"):
                proof.pinned(root, str((root / "input").resolve()), "irrelevant")

    def test_update_relation_is_preserved_from_every_consistent_prestate(self):
        p = proof.check_structure(self.original, proof.query_for(2), 2)
        for old_server in range(-1, 2):
            for old_bits in itertools.product((False, True), repeat=2):
                if not all(bit == (old_server == i) for i, bit in enumerate(old_bits)):
                    continue
                for selector in range(-1, 2):
                    last, bits = proof.projected_step(p, selector)
                    self.assertEqual(selector, last)
                    self.assertEqual(sum(bits), int(selector >= 0))

    def test_enumerator_detects_broken_mapping_independently_of_parser(self):
        p = proof.check_structure(self.original, proof.query_for(2), 2)
        with self.assertRaisesRegex(proof.PremiseError, "conclusion failed"):
            proof.explore(replace(p, grant_targets=(0, 0)))
        with self.assertRaisesRegex(proof.PremiseError, "conclusion failed"):
            proof.explore(replace(p, initial_grants=(True, True)))

    def test_sequential_assignments_have_unsafe_intermediate_valuation(self):
        # This is an abstract mutation witness, NOT a concrete model trace.
        old = [False, True]
        intermediate = old.copy()
        intermediate[0] = True
        complete = intermediate.copy()
        complete[1] = False
        self.assertEqual((sum(old), sum(intermediate), sum(complete)), (1, 2, 1))

    def test_certificate_reproduces_and_preserves_native_timeouts(self):
        artifacts = proof.reproduce()
        for name, data in artifacts.items():
            self.assertEqual((proof.HERE / "generated" / name).read_bytes(), data)
        history = json.loads(artifacts["historical-runs.json"])
        self.assertEqual(12, len(history["records"]))
        self.assertTrue(all(r["status"] == "timeout" and r["property_verdict"] is None
                            for r in history["records"]))


if __name__ == "__main__":
    unittest.main()
