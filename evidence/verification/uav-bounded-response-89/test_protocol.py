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

class RunnerIdentityTests(unittest.TestCase):
    def approval(self):
        import driver
        a=json.loads((HERE/'approval-template.json').read_text(encoding='utf-8'))
        a.update(approver='vadimnbkg',runner='vadimnbkg',native_execution_authorized=True,
                 hnom_restrictions_and_materialization_approved=True,
                 decision_url='https://github.com/artmus208/uppaal_sdn_isac/issues/89#issuecomment-5969141901',
                 preparation_head='a'*40,config_hash=driver.digest((HERE/'config.json').read_bytes()))
        return a

    def test_declared_accounts_pass_approval_without_impersonation(self):
        import driver
        seal=(HERE/'seal.json').read_text(encoding='utf-8').strip()
        for approver,runner in [('vadimnbkg','vadimnbkg'),('artmus208','vadimnbkg'),('artmus208','artmus208')]:
            with self.subTest(approver=approver,runner=runner):
                a=self.approval();a.update(approver=approver,runner=runner)
                with patch.object(driver,'git',return_value=seal),patch.object(driver,'verify_native_inputs',return_value=Path('verifyta.exe')) as native:
                    inventory,config,tool=driver.verify_approval(a)
                self.assertEqual(len(inventory),6)
                self.assertEqual(config['max_attempts'],6)
                native.assert_called_once_with(a,config,ROOT)
                self.assertEqual(driver.runner_branch(a),'codex/'+runner+'/89-uav-bounded-response-runs')

    def test_missing_or_invalid_account_rejected_before_native_calls(self):
        import driver
        for field in ('approver','runner'):
            for value in (None,'',' ',123,'../other','two accounts','-invalid','x'*40):
                with self.subTest(field=field,value=value):
                    a=self.approval();a[field]=value
                    with patch.object(driver,'verify_native_inputs') as native,self.assertRaisesRegex(ValueError,'Explicit GitHub account'):
                        driver.verify_approval(a)
                    native.assert_not_called()

    def test_declared_accounts_do_not_bypass_approval_or_hashes(self):
        import driver
        seal=(HERE/'seal.json').read_text(encoding='utf-8').strip()
        for change,error in [({'native_execution_authorized':False},'approval required'),
                             ({'hnom_restrictions_and_materialization_approved':False},'approval required'),
                             ({'decision_url':'https://example.com/'},'decision URL'),
                             ({'config_hash':'0'*64},'Configuration approval mismatch'),
                             ({'query_hashes':[]},'Query approval mismatch'),
                             ({'hnom_hash':'0'*64},'Hnom hash/diff mismatch')]:
            with self.subTest(change=change):
                a=self.approval();a.update(change)
                with patch.object(driver,'git',return_value=seal),patch.object(driver,'verify_native_inputs') as native,self.assertRaisesRegex(ValueError,error):
                    driver.verify_approval(a)
                native.assert_not_called()

    def test_wrong_runner_branch_rejected_before_native_calls(self):
        import audit
        import driver
        with patch.object(audit,'audit_preparation'),patch.object(driver,'git',return_value='codex/artmus208/89-uav-bounded-response-runs'),patch.object(driver,'verify_approval') as verify,self.assertRaisesRegex(ValueError,'declared Runner branch'):
            driver.run(self.approval())
        verify.assert_not_called()

    def test_checkpoint_exports_declared_runner_branch(self):
        import driver
        branch=driver.runner_branch(self.approval())
        def fake_git(*args,**kwargs):
            if args==('branch','--show-current'):return branch
            if args==('rev-parse','HEAD'):return 'b'*40
            return ''
        with tempfile.TemporaryDirectory() as d,patch.object(driver,'EXEC',Path(d)),patch.object(driver,'git',side_effect=fake_git) as git:
            self.assertEqual(driver.checkpoint('synthetic checkpoint',branch),'b'*40)
            git.assert_any_call('bundle','create',str(Path(d)/'recovery'/('b'*40+'.bundle')),branch,timeout=60)

    def test_checkpoint_preserves_modified_file_status_columns(self):
        import driver
        branch=driver.runner_branch(self.approval())
        def output(command,**kwargs):
            args=tuple(command[1:])
            if args==('branch','--show-current'):return branch+'\n'
            if args==('status','--porcelain','--untracked-files=all'):
                return ' M '+driver.SCOPE+'/execution/ledger.json\n'
            if args==('rev-parse','HEAD'):return 'b'*40+'\n'
            return ''
        with tempfile.TemporaryDirectory() as d,patch.object(driver,'EXEC',Path(d)),patch.object(driver.subprocess,'check_output',side_effect=output):
            self.assertEqual(driver.checkpoint('modified execution record',branch),'b'*40)

    def test_session_records_declared_accounts_and_branch(self):
        import audit
        import driver
        a=self.approval();branch=driver.runner_branch(a)
        def fake_git(*args,**kwargs):
            if args==('branch','--show-current'):return branch
            if args==('remote','get-url','origin'):return 'https://github.com/artmus208/uppaal_sdn_isac.git'
            if args==('rev-parse','HEAD'):return 'b'*40
            return ''
        cfg=json.loads((HERE/'config.json').read_text(encoding='utf-8'))
        with tempfile.TemporaryDirectory() as d:
            execution=Path(d);(execution/'model.xml').write_bytes(b'synthetic model')
            with patch.object(driver,'EXEC',execution),patch.object(audit,'audit_preparation'),patch.object(driver,'git',side_effect=fake_git),patch.object(driver,'verify_approval',return_value=([],cfg,Path(__file__))),patch.object(driver.win,'existing_verifiers',return_value=[]),patch.object(driver.win,'identity',return_value={'physical_ram_bytes':1024**3,'processor':'synthetic'}),patch.object(driver,'derive',return_value=(b'synthetic model',[])),patch.object(driver,'Guard',side_effect=RuntimeError('synthetic stop before native execution')) as guard,patch.object(driver,'checkpoint') as checkpoint:
                self.assertEqual(driver.run(a),1)
            session=json.loads((execution/'session.json').read_text(encoding='utf-8'))
            self.assertEqual(session['runner'],'vadimnbkg')
            self.assertEqual(session['approver'],'vadimnbkg')
            self.assertEqual(session['runner_branch'],branch)
            self.assertEqual(session['approval'],a)
            self.assertEqual(session['status'],'stopped')
            guard.assert_called_once_with(1800)
            checkpoint.assert_called_once_with('retain final native session disposition',branch)

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
