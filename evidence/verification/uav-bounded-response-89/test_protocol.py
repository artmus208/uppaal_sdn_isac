"""Synthetic software controls. No UPPAAL executable or model query is run."""
import json
import os
from pathlib import Path
import signal
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

from prepare import HERE, ROOT, M_PATH, derive, products, queries, tree
from guard import Guard
from driver import parse_verdict, save

class IntegrityTests(unittest.TestCase):
    def test_offline_audit_rejects_query_and_code_tampering(self):
        import audit
        for relative in ['queries/Q4.q','guard.py']:
            with tempfile.TemporaryDirectory() as d:
                target=Path(d)/'package';shutil.copytree(HERE,target)
                (target/relative).write_bytes((target/relative).read_bytes()+b' ')
                with patch.object(audit,'HERE',target),self.assertRaises(ValueError):
                    audit.audit_preparation()

    def test_missing_approval_rejected_before_native_calls(self):
        from driver import verify_approval
        a=json.loads((HERE/'approval-template.json').read_text(encoding='utf-8'))
        with self.assertRaisesRegex(ValueError,'approval required'):verify_approval(a)

class ModelTests(unittest.TestCase):
    def test_exact_allowed_changes_and_preservation(self):
        source=(ROOT/M_PATH).read_bytes(); derived,changes=derive(source)
        m=ET.fromstring(source);h=ET.fromstring(derived)
        allowed={'u0_Boundary_E_PHY_INPUT','SharedLoad','u0_Boundary_E_FAULT'}
        self.assertEqual(m.findtext('declaration'),h.findtext('declaration'))
        self.assertEqual(m.findtext('system'),h.findtext('system'))
        for a,b in zip(m.findall('template'),h.findall('template')):
            name=a.findtext('name')
            if name not in allowed:self.assertEqual(tree(a),tree(b));continue
            expected=[c for c in changes if c['template']==name]
            ats=a.findall('transition')
            for change in expected:
                tr=ats[change['transition_index']]
                if change['kind']=='select':tr.find("label[@kind='select']").text=change['after']
                else:a.remove(tr)
            self.assertEqual(tree(a),tree(b))
        shared=h.find("template[name='SharedLoad']")
        self.assertIn('server:int[-1,0]',[x.text for x in shared.findall("transition/label[@kind='select']")])
        self.assertEqual(sum(c['kind']=='remove_external_injection_edge' for c in changes),15)
        self.assertFalse((HERE/'execution/model.xml').exists())

    def test_source_drift_rejected(self):
        with self.assertRaises(ValueError):derive((ROOT/M_PATH).read_bytes()+b' ')

    def test_formulas_and_receipt_boundaries(self):
        q=queries()
        self.assertEqual(q[1],b'E<> (c82_request_id==1 && c82_active)\n')
        self.assertIn(b'c82_receipt_sample_band==0',q[3])
        self.assertNotIn(b'c82_sample_age',q[3])
        self.assertTrue(q[4].startswith(b'(c82_request_id==1 && c82_active) -->'))
        self.assertIn(b'ServiceTimeout',q[6])
        self.assertNotIn(b'ServiceTimeout',q[4])
        model=(ROOT/M_PATH).read_text(encoding='utf-8')
        self.assertEqual(model.count('c82_service_age=0;'),1)  # reset only at actual send
        self.assertIn('c82_sample_age&lt;5',model)
        self.assertIn('c82_service_age==c82_D_service',model)

    def test_reproducible_products(self):
        for path,data in products().items():self.assertEqual((HERE/path).read_bytes(),data)

class ResultTests(unittest.TestCase):
    def test_fail_closed_parser(self):
        header='Verifying formula 1 at line 1\n'
        self.assertTrue(parse_verdict(0,header+'Formula is satisfied.',''))
        self.assertFalse(parse_verdict(0,header+'Formula is NOT satisfied.',''))
        for rc,text,err in [(1,header+'Formula is satisfied.',''),(0,'Formula is satisfied.',''),
                             (0,header+'Formula is satisfied.','Error: invalid expression'),
                             (0,header+'Formula is satisfied.\nFormula is NOT satisfied.',''),
                             (0,header+'Formula MAY be satisfied.','')]:
            self.assertIsNone(parse_verdict(rc,text,err))

    def test_atomic_write_failure_retains_old_record(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'status.json';save(p,{'old':True})
            p.with_name('status.json.tmp').mkdir()
            with self.assertRaises(OSError):save(p,{'old':False})
            self.assertEqual(json.loads(p.read_text(encoding='utf-8')),{'old':True})

if __name__=='__main__':unittest.main()
