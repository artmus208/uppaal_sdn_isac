"""Operational v2 selection stays separate from frozen generation inputs."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('activation_checker', ROOT / 'scripts/check_coordination.py')
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


class CoordinationActivationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        paths = ['manifests/current.json', 'manifests/v2.md', 'manifests/v2-migration.md',
                 'manifests/collaboration-v2.yaml', 'manifests/v1.md',
                 'manifests/collaboration-v1.yaml', 'manifests/baselines/reviewer-r1.yaml',
                 'AGENTS.md', 'CONTRIBUTING.md', 'CONTRIBUTING-v2.md', '.github/ISSUE_TEMPLATE/workstream.yml',
                 '.github/PULL_REQUEST_TEMPLATE.md', '.github/CODEOWNERS', '.github/workflows/ci.yml']
        for relative in paths:
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, target)
        self.pointer = self.root / 'manifests/current.json'
        self.config = json.loads(self.pointer.read_text())

    def check(self):
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return checker.structural_checks(self.root)

    def test_current_v2_and_historical_v1_coexist(self):
        self.assertEqual(checker.current_configuration(self.root)['scientific_plan'], 'manifests/v2.md')
        self.assertEqual(self.check(), 0)
        # A change to the operational plan is not drift of the frozen v1 hash.
        path = self.root / 'manifests/v2.md'
        path.write_text(path.read_text() + '\nEditorial clarification in the operational plan.\n')
        self.assertEqual(self.check(), 0)

    def test_missing_or_invalid_pointer_never_falls_back(self):
        self.pointer.unlink()
        self.assertEqual(self.check(), 1)
        for value in ('{', 'null', '[]', '{}', json.dumps({**self.config, 'schema_version': True}),
                      json.dumps({**self.config, 'schema_version': 2}),
                      json.dumps({**self.config, 'unexpected': 'field'})):
            with self.subTest(value=value):
                self.pointer.write_text(value)
                self.assertEqual(self.check(), 1)

    def test_bad_paths_and_contract_disagreement_are_rejected(self):
        for value in ('manifests/missing.md', '../outside.md', str(ROOT / 'manifests/v2.md'),
                      'manifests/v1.md', None):
            with self.subTest(value=value):
                self.pointer.write_text(json.dumps({**self.config, 'scientific_plan': value}))
                self.assertEqual(self.check(), 1)
        self.pointer.write_text(json.dumps({**self.config, 'collaboration_manifest': 'manifests/collaboration-v1.yaml'}))
        self.assertEqual(self.check(), 1)
        self.pointer.write_text(json.dumps({**self.config, 'activation_issue': ''}))
        self.assertEqual(self.check(), 1)

    def test_historical_input_drift_is_rejected(self):
        for relative in ('manifests/v1.md', 'manifests/collaboration-v1.yaml',
                         'manifests/baselines/reviewer-r1.yaml', 'CONTRIBUTING.md'):
            with self.subTest(path=relative):
                path = self.root / relative
                original = path.read_bytes()
                path.write_bytes(original + b'\n# drift\n')
                self.assertEqual(self.check(), 1)
                path.write_bytes(original)

    def test_owner_and_gate_changes_are_rejected(self):
        path = self.root / 'manifests/collaboration-v2.yaml'
        original = path.read_text()
        mutations = [
            ('atomic_comment_ids: [C01, C02, C03, C04, C05, C06]', 'atomic_comment_ids: [C01, C02, C03, C04, C05, R03]'),
            ('accept_after: [P3_core_evidence_accepted, gate_1]', 'accept_after: [P3_complete, gate_1]'),
            ('accept_after: [P4]', 'accept_after: []'),
            ('start_after: [P1, P2, P3, P4, P5, P6, P7]', 'start_after: [P1, P2, P3, P4, P5, P6]'),
            ('series_requires: [accepted_configuration_family, gate_1]', 'series_requires: [gate_1]'),
        ]
        for before, after in mutations:
            with self.subTest(before=before):
                self.assertIn(before, original)
                path.write_text(original.replace(before, after))
                self.assertEqual(self.check(), 1)
        path.write_text(original)
        self.assertEqual(self.check(), 0)

    def test_migration_ids_remain_unique_and_conditional(self):
        path = self.root / 'manifests/v2-migration.md'
        original = path.read_text()
        for changed in (original.replace('| R03 | P4 |', '| R03 | P2 |'),
                        original + '\n| C01 | P3 | duplicate |\n',
                        original.replace('| D01 | P9b (условно) |', '| D01 | P9b |')):
            with self.subTest(changed=changed[-80:]):
                path.write_text(changed)
                self.assertEqual(self.check(), 1)


class FrozenGenerationTests(unittest.TestCase):
    def test_generator_ignores_operational_v2_and_reproduces_frozen_bytes(self):
        from uppaal_mcp.integrated.generator import generate
        operational = {str((ROOT / p).resolve()) for p in
                       ('manifests/current.json', 'manifests/v2.md', 'manifests/collaboration-v2.yaml')}
        original = Path.read_bytes

        def guarded_read(path):
            if str(path.resolve()) in operational:
                raise AssertionError('Generator must not consume operational v2 inputs')
            return original(path)

        with patch.object(Path, 'read_bytes', guarded_read):
            result = generate(ROOT)
        frozen = ROOT / 'evidence/governance/20260906-baseline/gate1-20260923'
        self.assertEqual(result.model_xml.encode(), (frozen / 'model.xml').read_bytes())
        self.assertEqual(result.queries.encode(), (frozen / 'candidate-queries.q').read_bytes())
        self.assertIn('manifests/v1.md', result.metadata['source_hashes'])
        self.assertIn('manifests/collaboration-v1.yaml', result.metadata['source_hashes'])
        self.assertNotIn('manifests/v2.md', result.metadata['source_hashes'])
        self.assertEqual(result.metadata['context_document_hashes']['AGENTS.md']['role'],
                         'operational_context_not_model_input')


if __name__ == '__main__':
    unittest.main()
