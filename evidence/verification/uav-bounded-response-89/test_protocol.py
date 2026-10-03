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
from guard import Guard, members
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
        a=json.loads((HERE/'approval-template.json').read_text())
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
        model=(ROOT/M_PATH).read_text()
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
            self.assertEqual(json.loads(p.read_text()),{'old':True})

class GuardTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.directory=Path(self.tmp.name)
        self.guard=Guard(15)

    def tearDown(self):
        self.guard.close();self.tmp.cleanup()

    def invoke(self,code,cap=4,memory=256*1024**2):
        return self.guard.run([sys.executable,'-c',code],self.directory,cap,memory)

    def test_success_and_error_exit(self):
        r=self.invoke('print("synthetic")')
        self.assertEqual(r['exit_code'],0);self.assertEqual(r['status'],'exited')
        self.assertIn('synthetic',(self.directory/'stdout.txt').read_text())
        self.directory=self.directory/'second'
        self.assertEqual(self.invoke('raise SystemExit(7)')['exit_code'],7)

    def test_timeout_kills_descendants_not_unrelated_child(self):
        unrelated=subprocess.Popen([sys.executable,'-c','import time;time.sleep(20)'])
        try:
            code='import subprocess,sys,time,os; print(os.getpgrp(),flush=True); subprocess.Popen([sys.executable,"-c","import time; time.sleep(20)"]);time.sleep(20)'
            r=self.invoke(code,cap=1)
            self.assertEqual(r['status'],'timeout');self.assertLess(r['wall_seconds'],1.3)
            pgid=int((self.directory/'stdout.txt').read_text().strip())
            self.assertFalse(any(f[0]!='Z' for _,f in members(pgid)))
            self.assertIsNone(unrelated.poll())
        finally:unrelated.terminate();unrelated.wait()

    def test_memory_stop(self):
        r=self.invoke('import time; x=bytearray(64*1024*1024);time.sleep(20)',memory=24*1024**2)
        self.assertEqual(r['status'],'memory_limit');self.assertGreater(r['peak_rss_bytes'],24*1024**2)

    def test_telemetry_failure_kills_group(self):
        (self.directory/'telemetry.jsonl').mkdir()
        r=self.invoke('import time;time.sleep(20)')
        self.assertEqual(r['status'],'error');self.assertTrue(r['cleanup_confirmed'])

    def test_replaced_status_json_irrelevant(self):
        (self.directory/'status.json').mkdir()
        r=self.invoke('import time;time.sleep(20)',cap=1)
        self.assertEqual(r['status'],'timeout')

    def test_session_limit_independent_of_slot_cap(self):
        self.guard.close();self.guard=Guard(3)
        r=self.invoke('import time;time.sleep(20)',cap=20)
        self.assertEqual(r['status'],'session_limit');self.assertLess(r['wall_seconds'],3)

    def test_dead_watchdog_controller_cleans_owned_group(self):
        timer=threading.Timer(0.7,lambda:os.kill(self.guard.p.pid,signal.SIGKILL));timer.start()
        try:
            with self.assertRaises((RuntimeError,EOFError,ConnectionResetError)):
                self.invoke('import os,time;print(os.getpgrp(),flush=True);time.sleep(20)',cap=5)
            pgid=int((self.directory/'stdout.txt').read_text().strip())
            time.sleep(0.1)
            self.assertFalse(any(f[0]!='Z' for _,f in members(pgid)))
        finally:timer.join()

    def test_controller_eof_stops_owned_group(self):
        self.guard.conn.send(dict(op='run',command=[sys.executable,'-c','import time;time.sleep(20)'],
                                  cwd=str(self.directory),cap=5,memory_bytes=256*1024**2,
                                  stdout=str(self.directory/'stdout.txt'),stderr=str(self.directory/'stderr.txt'),
                                  telemetry=str(self.directory/'telemetry.jsonl')))
        self.assertTrue(self.guard.conn.poll(3))
        msg=self.guard.conn.recv();self.assertEqual(msg['event'],'owned')
        pgid=msg['pgid'];self.guard.conn.send({'op':'go'});self.guard.conn.close()
        self.guard.p.join(3)
        self.assertFalse(self.guard.p.is_alive())
        self.assertFalse(any(f[0]!='Z' for _,f in members(pgid)))

    def test_stop_command(self):
        timer=threading.Timer(0.5,lambda:self.guard.conn.send({'op':'stop'}));timer.start()
        try:self.assertEqual(self.invoke('import time;time.sleep(20)')['status'],'stopped')
        finally:timer.join()

if __name__=='__main__':unittest.main()
