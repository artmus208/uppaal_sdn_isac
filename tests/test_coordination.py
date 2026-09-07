"""Regression coverage for run ownership and exact-byte audit provenance."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


checker = module("coordination", ROOT / "scripts/check_coordination.py")
auditor = module("baseline_audit", ROOT / "evidence/governance/20260906-baseline/audit_hashes.py")


class RunStorageTests(unittest.TestCase):
    def setUp(self):
        self.text = (ROOT / "manifests/collaboration-v1.yaml").read_text()

    def test_canonical_storage(self):
        self.assertEqual(checker.check_run_storage(self.text), [])

    def test_invalid_mappings(self):
        for value in ("evidence/runs/<run_id>/", "evidence/scalability/runs/<run_id>/",
                      "evidence/verification/../runs/<run_id>/", "/tmp/<run_id>/"):
            with self.subTest(value=value):
                self.assertTrue(checker.check_run_storage(self.text.replace(
                    "evidence/verification/runs/<run_id>/", value)))
        for text in (
            self.text.replace('    P4: "evidence/scalability/runs/<run_id>/"\n', ''),
            self.text.replace('  manifest_filename:', '    P3: "duplicate"\n  manifest_filename:'),
            self.text.replace('  manifest_filename:', '  storage_pattern: "evidence/runs/<run_id>/"\n  manifest_filename:'),
            self.text.replace('      - evidence/verification/**', '      - evidence/other/**'),
        ):
            self.assertTrue(checker.check_run_storage(text))


class HashAuditTests(unittest.TestCase):
    def setUp(self):
        # No extra dependency is required by the ordinary project/CI suite.
        # JSON is a YAML subset; inject its parser for fixtures only. Real YAML
        # parsing is exercised by the recorded CLI audit with pinned PyYAML.
        import types
        from unittest.mock import patch
        self.yaml_patch = patch.dict(sys.modules, {"yaml": types.SimpleNamespace(
            safe_load=json.loads, __version__="json-fixture-parser")})
        self.yaml_patch.start()
        self.addCleanup(self.yaml_patch.stop)
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        self.git("init", "-q")
        self.git("config", "user.name", "Audit fixture")
        self.git("config", "user.email", "fixture@example.invalid")
        for path, data in (("z.txt", b"z\r\n"), ("a.txt", b"a\n")):
            (self.repo / path).write_bytes(data)
        paths = ["z.txt", "a.txt"]
        def aggregate(order):
            return auditor.digest(''.join(f'{auditor.digest((self.repo/p).read_bytes())}  {p}\n'
                                          for p in order).encode())
        self.manifest = {
            "metadata": {"id": "fixture", "frozen": False}, "gate_1": {"status": "pending"},
            "files": [{"path": p, "sha256": auditor.digest((self.repo/p).read_bytes())} for p in paths],
            "hashing": {"common_hashes": {
                "source_hash": {"inputs": paths, "value": aggregate(paths), "construction":
                    "sha256 of concatenated sha256sum records in the listed order"},
                "generator_hash": {"inputs": paths, "value": aggregate(sorted(paths)), "construction":
                    "sha256 of concatenated sha256sum records for the listed files in bytewise path order"}}}}
        self.save()
        self.git("add", ".")
        self.git("-c", "core.autocrlf=false", "commit", "-qm", "fixture")

    def git(self, *args):
        return subprocess.check_output(["git", *args], cwd=self.repo, stderr=subprocess.PIPE)

    def save(self):
        target = self.repo / auditor.MANIFEST
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.manifest))

    def test_exact_bytes_and_committed_manifest(self):
        self.assertEqual(auditor.audit(self.repo)["hash_status"], "match")
        (self.repo / "z.txt").write_bytes(b"z\n")
        dirty = auditor.audit(self.repo)
        self.assertEqual(dirty["mismatch_count"], 1)
        self.assertEqual(dirty["common_hash_mismatch_count"], 2)
        self.manifest["metadata"]["id"] = "dirty"
        self.save()
        clean = auditor.audit(self.repo, "HEAD")
        self.assertEqual(clean["hash_status"], "match")
        self.assertEqual(clean["baseline_id"], "fixture")
        self.assertEqual(clean["input_mode"], "exact_git_blobs")

    def test_missing_input_and_immutable_output(self):
        output = self.repo / "result.json"
        self.assertEqual(auditor.run(self.repo, None, output), 0)
        original = output.read_bytes()
        (self.repo / "a.txt").unlink()
        self.assertEqual(auditor.run(self.repo, None, self.repo / "missing.json"), 1)
        self.assertEqual(auditor.run(self.repo, None, output), 2)
        self.assertEqual(output.read_bytes(), original)
        self.assertIsNone(auditor.audit(self.repo)["common_hashes"][0]["actual_sha256"])

    def test_invalid_input_and_construction(self):
        self.manifest["files"][0]["path"] = "../outside"
        self.save()
        with self.assertRaises(ValueError):
            auditor.audit(self.repo)
        self.manifest["files"][0]["path"] = "z.txt"
        self.manifest["hashing"]["common_hashes"]["source_hash"]["construction"] = "unknown"
        self.save()
        with self.assertRaises(ValueError):
            auditor.audit(self.repo)


if __name__ == "__main__":
    unittest.main()
