"""Failure-contract tests: no native executable or verifier invoked."""
import importlib.util
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('diagnostics78',HERE/'run_diagnostics.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)

class DiagnosticsTests(unittest.TestCase):
    def good(self):return {'status':'success','exit_code':0,'wrapper_exit_code':0,'process_reaped':True,'samples':1}
    def test_failed_or_censored_run_never_promotes_partial_verdict(self):
        for status in ('timeout','memory_limit','error','monitor_error'):
            raw=self.good();raw['status']=status
            self.assertEqual(r.classify(raw,'-- Formula is satisfied.',''),(status,None))
    def test_cleanup_sampling_exit_required(self):
        for field,bad in [('process_reaped',False),('samples',0),('exit_code',1),('wrapper_exit_code',2)]:
            raw=self.good();raw[field]=bad
            self.assertEqual(r.classify(raw,'-- Formula is satisfied.',''),('monitor_error',None))
    def test_exact_single_verdict_and_formula_index(self):
        for text in ('','-- Formula is satisfied.\n-- Formula is NOT satisfied.','Verifying formula 2\n-- Formula is satisfied.'):
            self.assertEqual(r.classify(self.good(),text,''),('verdict_error',None))
        self.assertEqual(r.classify(self.good(),'Verifying formula 1\n-- Formula is NOT satisfied.',''),('success','violated'))
    def test_error_diagnostic_overrides_verdict(self):
        self.assertEqual(r.classify(self.good(),'-- Formula is satisfied.','Error: invalid expression'),('tool_error',None))
    def test_wall_budget_includes_elapsed_outside_invocation(self):
        with patch.object(r.time,'monotonic',return_value=100):b=r.Budget()
        with patch.object(r.time,'monotonic',return_value=334.9):b.require(65)
        with patch.object(r.time,'monotonic',return_value=335.1):
            with self.assertRaisesRegex(RuntimeError,'budget'):b.require(65)
    def test_watchdog_uses_config_result_not_config_stem(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'tool.config.json';p.write_text(json.dumps({'result':'C:\\scope\\tool.monitor.json'}))
            with patch.object(r.subprocess,'check_output',return_value='/actual/tool.monitor.json\n'):
                self.assertEqual(r.native_result_path(p),Path('/actual/tool.monitor.json'))
    def test_early_wrapper_exit_with_live_pid_triggers_cleanup(self):
        with tempfile.TemporaryDirectory() as t:
            folder=Path(t);cfg=folder/'tool.config.json';cfg.write_text('{}')
            result=folder/'tool.monitor.json';result.write_text(json.dumps({'status':'monitor_error','process_id':123,'process_reaped':False}))
            with patch.object(r,'win',side_effect=str), patch.object(r,'native_result_path',return_value=result), patch.object(r.subprocess,'run',return_value=SimpleNamespace(stdout=b'out',stderr=b'err',returncode=2)), patch.object(r,'cleanup',return_value={'process_absence_confirmed':True}) as clean:
                raw=r.invoke(folder/'monitor.ps1',cfg,50,SimpleNamespace(timeout=lambda n:n))
                clean.assert_called_once_with(cfg)
                self.assertEqual(raw['status'],'monitor_error')
                self.assertEqual(cfg.with_suffix('.wrapper.stdout.txt').read_bytes(),b'out')
                self.assertFalse((folder/'wrapper.stdout.txt').exists())
    def test_unconfirmed_live_pid_cleanup_fails_closed(self):
        with tempfile.TemporaryDirectory() as t:
            folder=Path(t);cfg=folder/'tool.config.json';cfg.write_text('{}')
            result=folder/'tool.monitor.json';result.write_text(json.dumps({'status':'error','process_id':123,'process_reaped':False}))
            with patch.object(r,'win',side_effect=str), patch.object(r,'native_result_path',return_value=result), patch.object(r.subprocess,'run',return_value=SimpleNamespace(stdout=b'',stderr=b'',returncode=2)), patch.object(r,'cleanup',return_value={'process_absence_confirmed':False}):
                with self.assertRaisesRegex(RuntimeError,'cleanup unconfirmed'):
                    r.invoke(folder/'monitor.ps1',cfg,50,SimpleNamespace(timeout=lambda n:n))
    def test_approved_query_snapshot_and_limits(self):
        protocol,_=r.pins()
        self.assertEqual([q['id'] for q in protocol['queries']],['d1-kpi-consumed','d2-service-ready','d3-useful-grant'])
        self.assertEqual(protocol['total_wall_seconds'],300)
        for q in protocol['queries']:
            self.assertEqual(q['arguments'][q['arguments'].index('-o')+1],'0')
            self.assertEqual(q['arguments'][q['arguments'].index('-r')+1],'78')

if __name__=='__main__':unittest.main()
