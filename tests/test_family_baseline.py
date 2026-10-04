"""The family input freeze cannot authorize execution or replace historical inputs."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('family_checker', ROOT / 'scripts/check_family_baseline.py')
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


class FamilyBaselineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        pins = json.loads((ROOT / checker.PACKET / 'input-hashes.json').read_bytes())['files']
        paths = set(pins) | {checker.MANIFEST, checker.CONTRACT, 'manifests/current.json'}
        paths |= {checker.PACKET + name for name in checker.PINNED}
        for relative in paths:
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, target)
        self.manifest = self.root / checker.MANIFEST
        self.original = json.loads(self.manifest.read_bytes())

    def reject(self, data):
        self.manifest.write_text(json.dumps(data))
        with self.assertRaises(ValueError):
            checker.audit(self.root)

    def test_current_family_and_historical_default_coexist(self):
        result = checker.audit(self.root)
        self.assertEqual(result['models'], 4)
        self.assertEqual(result['queries'], 30)
        self.assertEqual(result['current_input_hashes_checked'], 106)
        self.assertFalse(result['activation_checked'])
        self.assertFalse(result['P4_execution_authorized'])

    def test_incomplete_family_or_query_set_rejected(self):
        for key in ('family_domain', 'models'):
            d = copy.deepcopy(self.original)
            d[key].pop()
            self.reject(d)
        d = copy.deepcopy(self.original)
        del d['models'][3]['files']['p4/u3-service.q']
        self.reject(d)

    def test_scope_widening_and_forged_decision_rejected(self):
        changes = [('claim_scope', 'service_reachability', 'satisfied'),
                   ('claim_scope', 'does_not_close', []),
                   ('operational_activation', 'P4_execution_authorized', True),
                   ('operational_activation', 'inclusion_in_a_branch_is_activation', True),
                   ('selection', 'automatic_P3_transfer', True),
                   ('input_scope_acceptance', 'decision_reference', 'https://example.org/approved'),
                   ('input_scope_acceptance', 'P1_P2_applicability', 'unlimited'),
                   ('metadata', 'frozen', 1)]
        for section, key, value in changes:
            with self.subTest(key=key):
                d = copy.deepcopy(self.original)
                d[section][key] = value
                self.reject(d)

    def test_input_drift_rejected(self):
        for name in ('model.xml', 'parameters.json', 'instance-vector.json', 'p4/u0-service.q'):
            with self.subTest(name=name):
                path = self.root / self.original['models'][0]['files'][name]['path']
                raw = path.read_bytes()
                path.write_bytes(raw + b'\n')
                with self.assertRaisesRegex(ValueError, 'input hash mismatch'):
                    checker.audit(self.root)
                path.write_bytes(raw)

    def test_manifest_and_packet_cannot_be_rehashed_together(self):
        path = self.root / checker.PACKET / 'baseline-candidate.json'
        path.write_bytes(path.read_bytes() + b'\n')
        self.original['accepted_packet']['baseline-candidate.json']['sha256'] = checker.digest(path.read_bytes())
        self.reject(self.original)

    def test_default_switch_and_selection_policy_drift_rejected(self):
        path = self.root / 'manifests/current.json'
        d = json.loads(path.read_bytes())
        d['baseline_manifest'] = checker.MANIFEST
        path.write_text(json.dumps(d))
        with self.assertRaisesRegex(ValueError, 'historical default'):
            checker.audit(self.root)
        shutil.copyfile(ROOT / 'manifests/current.json', path)
        path = self.root / checker.CONTRACT
        path.write_text(path.read_text().replace('eligible_workstream: P4', 'eligible_workstream: P3'))
        with self.assertRaisesRegex(ValueError, 'selection policy'):
            checker.audit(self.root)

    def test_operational_contract_history_not_confused_with_current(self):
        # Its accepted old hash is deliberately different from current selection policy.
        self.assertNotEqual(checker.digest((self.root / checker.CONTRACT).read_bytes()),
                            self.original['input_hashes'][checker.CONTRACT])
        self.assertEqual(checker.audit(self.root)['historical_input_hashes_checked'], 0)

    def test_invalid_paths_rejected(self):
        for value in ('../outside', '/tmp/outside', 'a/../outside', 'a\\outside', ''):
            with self.subTest(value=value), self.assertRaises(ValueError):
                checker.read(self.root, value)

    def test_symlink_escape_rejected(self):
        path = self.root / self.original['models'][0]['files']['model.xml']['path']
        path.unlink()
        try:
            path.symlink_to(ROOT / self.original['models'][0]['files']['model.xml']['path'])
        except OSError as exc:
            if os.name == 'nt' and getattr(exc, 'winerror', None) == 1314:
                self.skipTest('Windows symlink privilege is unavailable')
            raise
        with self.assertRaisesRegex(ValueError, 'escapes'):
            checker.audit(self.root)

    def test_duplicate_fields_rejected(self):
        self.manifest.write_text('{"schema_version":"uav-family-1","schema_version":"uav-family-1"}')
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            checker.audit(self.root)


if __name__ == '__main__':
    unittest.main()
