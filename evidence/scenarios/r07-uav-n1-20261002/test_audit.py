"""Evidence corruption controls, without executing the engine."""
import copy
import unittest
from unittest.mock import patch
import audit


class EvidenceControls(unittest.TestCase):
    def setUp(self):
        self.folder = audit.HERE / 'runs/replay001'

    def corrupt_load(self, filename, field, value):
        original = audit.load
        def load(path):
            data = original(path)
            if path == self.folder / filename:
                data = copy.deepcopy(data)
                data[field] = value
            return data
        return load

    def test_verdict_laundering_is_rejected(self):
        with patch.object(audit, 'load', self.corrupt_load('result.json', 'property_verdict', 'satisfied')):
            with self.assertRaisesRegex(ValueError, 'simulation verdict'):
                audit.validate_cell(self.folder)

    def test_censored_native_run_cannot_be_positive_evidence(self):
        with patch.object(audit, 'load', self.corrupt_load('monitor.json', 'native_status', 'timeout')):
            with self.assertRaisesRegex(ValueError, 'native lifecycle'):
                audit.validate_cell(self.folder)

    def test_wrong_APP_result_is_rejected(self):
        original = audit.steps
        def changed(path):
            records = original(path)
            if path == self.folder / 'steps.jsonl':
                records[-1]['snapshot']['locations'][16] = 'Accepted'
            return records
        with patch.object(audit, 'steps', changed):
            with self.assertRaisesRegex(ValueError, 'APP endpoint'):
                audit.validate_cell(self.folder)


if __name__ == '__main__':
    unittest.main()
