"""Negative proposal controls, including wrong-model historical trace attribution."""
import copy
import json
import unittest

import check


class BaselineControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(check.read(check.PACKET + '/proposed-baseline.yaml'))
        cls.hashes = json.loads(check.read(check.PACKET + '/input-hashes.json'))

    def reject_manifest(self, mutate, message):
        m = copy.deepcopy(self.manifest)
        mutate(m)
        with self.assertRaisesRegex(ValueError, message):
            check.check(m, expensive=False)

    def reject_file(self, path, mutate, message):
        content = check.read(path)
        changed = mutate(content)
        self.assertNotEqual(content, changed)
        reader = lambda p: changed if p == path else check.read(p)
        with self.assertRaisesRegex(ValueError, message):
            check.check(reader=reader, expensive=False)

    def test_positive_static_proposal(self):
        self.assertEqual(check.check(expensive=False)['queries_without_verdict'], 11)

    def test_model_hash_substitution(self):
        self.reject_manifest(lambda m: m['model'].update(sha256='0' * 64), 'model hash substitution')

    def test_parameter_change(self):
        self.reject_file(check.CANDIDATE + '/parameters.json', lambda b: b.replace(b'"D_service": 40', b'"D_service": 41'), 'input hash drift')

    def test_instance_order_change(self):
        def mutate(b):
            d = json.loads(b)
            d['system_order'][0], d['system_order'][1] = d['system_order'][1], d['system_order'][0]
            return json.dumps(d).encode()
        self.reject_file(check.CANDIDATE + '/instance-vector.json', mutate, 'input hash drift')

    def test_query_formula_change(self):
        self.reject_file(check.CANDIDATE + '/queries/success.q', lambda b: b.replace(b'Completed', b'Accepted'), 'input hash drift')

    def test_old_trace_attributed_to_new_model(self):
        # Actual PR81 source hashes and run ID; no invented synthetic old-model identity.
        old = json.loads(check.read('evidence/scenarios/r07-uav-n1-20261002/runs/sim001/provenance.json'))
        evidence = json.loads(check.read(check.PACKET + '/machine-evidence-inventory.json'))
        row = copy.deepcopy(evidence['runs'][6])
        expected = json.loads(check.read(check.CANDIDATE + '/results.json'))['runs'][6]
        old_result = json.loads(check.read('evidence/scenarios/r07-uav-n1-20261002/runs/sim001/result.json'))
        old['model_hash'] = old_result['model_hash']
        self.assertNotEqual(old['model_hash'], check.MODEL)
        row.update(model_hash=old['model_hash'], run_id=old['run_id'], source_commit=old['source_commit'])
        with self.assertRaisesRegex(ValueError, 'cross-baseline'):
            check.validate_run(row, expected)

    def test_unfounded_freeze(self):
        self.reject_manifest(lambda m: m['metadata'].update(status='frozen', frozen=True), 'unsupported accepted/frozen')

    def test_unfounded_gate_acceptance(self):
        self.reject_manifest(lambda m: m['gate_1'].update(passed=True, status='accepted'), 'unsupported Gate')

    def test_unfounded_activation(self):
        self.reject_manifest(lambda m: m['operational_activation'].update(status='activated'), 'unsupported activation')

    def test_historical_pointer_substitution(self):
        self.reject_file('manifests/current.json', lambda b: b.replace(b'reviewer-r1.yaml', b'uav-service-completion-r1.yaml'), 'input hash drift')

    def test_proposed_query_verdict(self):
        self.reject_manifest(lambda m: m['query_set']['verdicts'].update(success='satisfied'), 'manifest query verdict')

    def test_execution_checkpoint_relabelled(self):
        evidence = json.loads(check.read(check.PACKET + '/machine-evidence-inventory.json'))
        row = copy.deepcopy(evidence['runs'][6])
        expected = json.loads(check.read(check.CANDIDATE + '/results.json'))['runs'][6]
        row['source_commit'] = check.PUBLICATION
        with self.assertRaisesRegex(ValueError, 'cross-baseline'):
            check.validate_run(row, expected)


if __name__ == '__main__':
    unittest.main()
