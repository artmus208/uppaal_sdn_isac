"""Evidence audit mutation controls; no verifier execution."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

HERE=Path(__file__).resolve().parent
ROOT=next(p for p in HERE.parents if (p/'manifests/current.json').exists())
spec=importlib.util.spec_from_file_location('audit_evidence',HERE/'audit_evidence.py')
audit_module=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit_module)

class EvidenceAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records=json.loads((HERE/'campaign-002/runs.json').read_bytes())

    def test_retained_evidence(self):
        result=audit_module.audit(ROOT)
        self.assertEqual(result['scheduled_cells'],117)

    def rejected(self,mutate,message):
        rows=copy.deepcopy(self.records);mutate(rows)
        with self.assertRaisesRegex(ValueError,message):audit_module.audit(ROOT,rows)

    def test_missing_cell_rejected(self):
        self.rejected(lambda rows:rows.pop(),'missing scheduled cell')

    def test_fabricated_timeout_verdict_rejected(self):
        def mutate(rows):
            cell=next(x for x in rows if x['phase']=='model-checking' and x['status']=='timeout')
            cell['property_verdict']='satisfied'
        self.rejected(mutate,'censored cell contains verdict')

    def test_model_hash_drift_rejected(self):
        def mutate(rows):
            cell=next(x for x in rows if x['phase']=='model-checking' and x['status']=='success')
            cell['model_hash']='0'*64
        self.rejected(mutate,'model hash mismatch')

    def test_changed_result_rejected(self):
        def mutate(rows):
            cell=next(x for x in rows if x['phase']=='model-checking' and x['status']=='success')
            cell['property_verdict']='invented'
        self.rejected(mutate,'verdict differs from raw stdout')

if __name__=='__main__':unittest.main()
