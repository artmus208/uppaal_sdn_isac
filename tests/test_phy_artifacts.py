"""PHY export cache identity and integrity; synthetic results, no verifier."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from uppaal_mcp.phy import artifacts
from uppaal_mcp.phy.generator import generate_uppaal_model


class PhyArtifactCacheTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.generated = generate_uppaal_model()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.inputs = dict(
            source_text="Synthetic source\n",
            contract_json=deepcopy(self.generated.contract),
            model_xml=self.generated.model_xml,
            queries=self.generated.queries,
            profile=deepcopy(self.generated.profile),
            result_json={"status": "satisfied", "query_results": []},
            trace_text="State: A_CH.ChannelAvailable\n",
            verifyta_version="synthetic-test",
            verifyta_command=["synthetic-verifyta", "model.xml", "queries.q"],
            options=["-o", "1"],
        )

    def export(self, **changes):
        return artifacts.export_run_artifacts(self.root, **{**self.inputs, **changes})

    def snapshot(self, exported):
        return {Path(p).name: Path(p).read_bytes() for p in exported["files"]}

    def test_identical_export_reuses_complete_bundle_unchanged(self):
        first = self.export()
        original = self.snapshot(first)
        second = self.export()
        self.assertFalse(first["cache_hit"])
        self.assertTrue(second["cache_hit"])
        self.assertEqual(second["metadata"], first["metadata"])
        self.assertEqual(self.snapshot(second), original)
        self.assertIn("artifact_checksums.json", original)

    def test_timeout_does_not_reuse_or_overwrite_success(self):
        first = self.export()
        original = self.snapshot(first)
        failed_result = {"status": "timeout", "query_results": []}
        second = self.export(result_json=failed_result)
        self.assertFalse(second["cache_hit"])
        self.assertNotEqual(first["run_id"], second["run_id"])
        self.assertEqual(second["metadata"]["result_status"], "timeout")
        result = Path(second["artifact_dir"]) / "results.json"
        self.assertEqual(json.loads(result.read_text(encoding="utf-8")), failed_result)
        self.assertEqual(self.snapshot(first), original)

    def test_public_export_wrapper_returns_the_requested_result(self):
        from uppaal_mcp.phy.tools import export_run_artifacts

        inputs = {key: value for key, value in self.inputs.items() if key != "source_text"}
        inputs["tex_text"] = self.inputs["source_text"]
        first = export_run_artifacts(output_root=str(self.root), **inputs)
        inputs["result_json"] = {"status": "timeout", "query_results": []}
        second = export_run_artifacts(output_root=str(self.root), **inputs)
        self.assertNotEqual(first["artifact_dir"], second["artifact_dir"])
        self.assertFalse(second["cache_hit"])
        self.assertEqual(second["metadata"]["result_status"], "timeout")

    def test_each_material_input_changes_cache_identity(self):
        first = self.export()
        contract = deepcopy(self.inputs["contract_json"])
        contract["cache_test_marker"] = "changed"
        variants = dict(
            source_text="Different source\n", contract_json=contract,
            model_xml=self.inputs["model_xml"] + "\n",
            queries=self.inputs["queries"] + "\n",
            profile={**self.inputs["profile"], "cache_test_marker": "changed"},
            result_json={"status": "not_satisfied", "query_results": []},
            trace_text="State: A_CH.ChannelOutage\n",
            verifyta_version="synthetic-other", verifyta_command=["other-verifyta"],
            options=["-o", "2"],
        )
        for key, value in variants.items():
            with self.subTest(input=key):
                other = self.export(**{key: value})
                self.assertFalse(other["cache_hit"])
                self.assertNotEqual(other["cache_key"], first["cache_key"])
                self.assertTrue(self.export(**{key: value})["cache_hit"])

    def test_absent_optional_content_differs_from_empty_content(self):
        for key, empty, filename in (("source_text", "", "source.tex"),
                                      ("result_json", {}, "results.json"),
                                      ("trace_text", "", "trace.txt")):
            with self.subTest(input=key):
                absent = self.export(**{key: None})
                present = self.export(**{key: empty})
                self.assertNotEqual(absent["run_id"], present["run_id"])
                self.assertFalse((Path(absent["artifact_dir"]) / filename).exists())
                self.assertTrue((Path(present["artifact_dir"]) / filename).exists())

    def test_exported_text_retains_exact_utf8_and_mixed_newlines(self):
        changes = dict(source_text="Источник\r\nsecond\n", queries="// Проверка\r\nA[] not deadlock\n",
                       model_xml=self.inputs["model_xml"].replace("\n", "\r\n", 1),
                       trace_text="State: A_CH.ChannelAvailable\r\n\n")
        result = self.export(**changes)
        folder = Path(result["artifact_dir"])
        for key, filename, hash_key in (("source_text", "source.tex", "source_hash"),
                                        ("model_xml", "model.xml", "model_hash"),
                                        ("queries", "queries.q", "query_hash"),
                                        ("trace_text", "trace.txt", None)):
            with self.subTest(file=filename):
                data = (folder / filename).read_bytes()
                self.assertEqual(data, changes[key].encode("utf-8"))
                if hash_key:
                    self.assertEqual(hashlib.sha256(data).hexdigest(), result["metadata"]["hashes"][hash_key])

    def test_missing_or_changed_bundle_file_is_rejected_and_preserved(self):
        first = self.export()
        folder = Path(first["artifact_dir"])
        for filename in self.snapshot(first):
            for action in ("missing", "changed"):
                with self.subTest(file=filename, action=action):
                    self.export(force=True)
                    target = folder / filename
                    if action == "missing":
                        target.unlink()
                    else:
                        target.write_bytes(b"corrupted\n")
                    damaged = {p.name: p.read_bytes() for p in folder.iterdir()}
                    with self.assertRaisesRegex(ValueError, "cache|Cache"):
                        self.export()
                    self.assertEqual({p.name: p.read_bytes() for p in folder.iterdir()}, damaged)

    def test_force_rebuilds_damaged_bundle_then_allows_a_hit(self):
        first = self.export()
        note = Path(first["artifact_dir"]) / "user-note.txt"
        note.write_bytes(b"Keep this unrelated file.\n")
        target = Path(first["artifact_dir"]) / "results.json"
        target.write_text('{"status":"timeout"}', encoding="utf-8")
        rebuilt = self.export(force=True)
        self.assertFalse(rebuilt["cache_hit"])
        self.assertEqual(first["artifact_dir"], rebuilt["artifact_dir"])
        self.assertEqual(json.loads(target.read_text(encoding="utf-8")), self.inputs["result_json"])
        cached = self.export()
        self.assertTrue(cached["cache_hit"])
        self.assertEqual(note.read_bytes(), b"Keep this unrelated file.\n")
        self.assertNotIn(str(note), rebuilt["files"])
        self.assertNotIn(str(note), cached["files"])

    def test_metadata_must_match_request_even_with_updated_checksum(self):
        exported = self.export()
        folder = Path(exported["artifact_dir"])
        path = folder / "run_metadata.json"
        metadata = json.loads(path.read_text(encoding="utf-8"))
        metadata["result_status"] = "timeout"
        path.write_text(json.dumps(metadata), encoding="utf-8")
        index_path = folder / "artifact_checksums.json"
        index = json.loads(index_path.read_text(encoding="utf-8"))
        index["files"][path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
        index_path.write_text(json.dumps(index), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "cache|Cache"):
            self.export()

    def test_checksum_index_requires_complete_local_file_set(self):
        exported = self.export()
        index_path = Path(exported["artifact_dir"]) / "artifact_checksums.json"
        original = json.loads(index_path.read_text(encoding="utf-8"))
        incomplete = deepcopy(original)
        del incomplete["files"]["report.md"]
        outside = deepcopy(original)
        outside["files"]["../outside"] = "0" * 64
        for index in ([], {}, {**original, "schema_version": True}, incomplete, outside):
            with self.subTest(index=index):
                index_path.write_text(json.dumps(index), encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "cache|Cache"):
                    self.export()

    def test_interrupted_export_cannot_be_reported_as_cache_hit(self):
        original = artifacts._write_text

        def fail_on_queries(path, text, files):
            if path.name == "queries.q":
                raise OSError("synthetic disk failure")
            return original(path, text, files)

        with patch.object(artifacts, "_write_text", side_effect=fail_on_queries):
            with self.assertRaisesRegex(OSError, "synthetic disk failure"):
                self.export()
        with self.assertRaisesRegex(ValueError, "cache|Cache"):
            self.export()
        self.assertFalse(self.export(force=True)["cache_hit"])
        self.assertTrue(self.export()["cache_hit"])

    def test_metadata_without_trace_matches_export_and_json_hash_is_canonical(self):
        exported = self.export(trace_text=None)
        args = {key: value for key, value in self.inputs.items() if key != "trace_text"}
        metadata = artifacts.build_run_metadata(**args)
        self.assertEqual(metadata["cache_key"], exported["cache_key"])
        for input_name, hash_name in (("contract_json", "contract_hash"), ("result_json", "result_hash")):
            canonical = json.dumps(self.inputs[input_name], ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            self.assertEqual(hashlib.sha256(canonical.encode()).hexdigest(), metadata["hashes"][hash_name])


if __name__ == "__main__":
    unittest.main()
