import copy
import gzip
import json
import unittest
from inspect_replay import ROOT, validate_cell

class SavedEvidenceControls(unittest.TestCase):
    def setUp(self):
        folder = ROOT / "native-002/replay"
        self.result = json.loads((folder / "result.json").read_text())
        self.monitor = json.loads((folder / "monitor.json").read_text())
        self.steps = [json.loads(s) for s in gzip.decompress((folder / "steps.jsonl.gz").read_bytes()).splitlines()]
    def test_saved_positive(self):
        self.assertEqual(validate_cell(self.result, self.monitor, self.steps, "replay")["accepted_transitions"], 68)
    def test_discrete_corruption_fails(self):
        self.steps[-1]["selected"]["family_grant_0"] = 0
        with self.assertRaisesRegex(ValueError, "service endpoint"):
            validate_cell(self.result, self.monitor, self.steps, "replay")
    def test_clock_corruption_fails(self):
        self.steps[-1]["reachable_zone"][0][1] = -17
        with self.assertRaisesRegex(ValueError, "exactly 10"):
            validate_cell(self.result, self.monitor, self.steps, "replay")
    def test_false_property_claim_fails(self):
        self.result["property_verdict"] = "satisfied"
        with self.assertRaisesRegex(ValueError, "query verdict"):
            validate_cell(self.result, self.monitor, self.steps, "replay")

if __name__ == "__main__":
    unittest.main()
