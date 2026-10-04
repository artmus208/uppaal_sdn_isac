import contextlib
import errno
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

from uppaal_mcp import verification_manager as m


class ManagerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.model = self.root/'model.xml'; self.model.write_text('<nta/>')
        self.queries = self.root/'queries.q'; self.queries.write_text('A[] true\nE<> true\n')
        self.fake = self.root/'fake.py'
        self.fake.write_text('''import sys,time,pathlib
if '--version' in sys.argv:
 print('fake verifier for software tests'); sys.exit(0)
q=pathlib.Path(sys.argv[-1]).read_text()
print('Verifying formula 1',flush=True)
print(' -- Throughput: 123 states/sec, Load: 456 states',flush=True)
if 'slow' in q: time.sleep(3)
if 'memory' in q:
 b=bytearray(64*1024*1024); time.sleep(3)
if 'missing' in q: sys.exit(0)
print(' -- Formula is '+('NOT satisfied' if 'false' in q else 'satisfied')+'.',flush=True)
if 'failure' in q: sys.exit(1)
''')
        self.queue = self.root/'queue'

    def init(self, text=None, **kwargs):
        if text: self.queries.write_text(text)
        m.initialize(self.queue, self.model, self.queries, sys.executable, **kwargs)
        cfg = m.read(self.queue/'queue.json')
        # Python interprets --version before the fake script for preflight.
        cfg['options'] = [str(self.fake)]
        m.save(self.queue/'queue.json', cfg)

    def run_queue(self):
        with contextlib.redirect_stdout(io.StringIO()):
            return m.start(self.queue, interval=.03)

    def results(self):
        return [m.read(p) for p in sorted(self.queue.glob('attempts/*/result.json'))]

    def worker(self):
        env = dict(os.environ, PYTHONPATH=str(Path(m.__file__).parents[1]), PYTHONDONTWRITEBYTECODE='1')
        p = subprocess.Popen([sys.executable, '-m', 'uppaal_mcp.verification_manager', 'start', str(self.queue)],
                             env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        def cleanup():
            if p.poll() is None:
                m.save(self.queue/'control.json', {'action':'stop'})
                try: p.wait(timeout=5)
                except subprocess.TimeoutExpired: p.kill(); p.wait()
            p.stderr.close()
        self.addCleanup(cleanup)
        return p

    def wait_phase(self, phase):
        until = time.monotonic()+8
        while time.monotonic() < until:
            if m.read(self.queue/'status.json')['phase'] == phase: return
            time.sleep(.03)
        self.fail('Did not reach '+phase)

    def test_queue_preserves_negative_verdict_and_skips_completed(self):
        self.init('A[] true\nA[] false\n')
        self.assertEqual(self.run_queue(), 0)
        self.assertEqual({r['verdict'] for r in self.results()}, {'satisfied','violated'})
        before = {str(p):p.read_bytes() for p in self.queue.glob('attempts/**/*') if p.is_file()}
        self.assertEqual(self.run_queue(), 0)
        self.assertEqual(before, {str(p):p.read_bytes() for p in self.queue.glob('attempts/**/*') if p.is_file()})
        self.assertFalse(m.status(self.queue)['worker_active'])

    def test_timeout_keeps_logs_and_retries_new_attempt(self):
        self.init('A[] slow\n', timeout=.15)
        self.assertEqual(self.run_queue(), 2)
        first = self.results()[0]
        self.assertEqual(first['status'], 'timeout'); self.assertIsNone(first['verdict'])
        self.assertTrue((self.queue/'attempts'/first['run_id']/'stdout.txt').read_text())
        self.run_queue(); self.assertEqual(len(self.results()), 2)
        self.assertEqual(next(r for r in self.results() if r['run_id'] == first['run_id']), first)

    def test_memory_limit_measures_real_child(self):
        self.init('A[] memory\n', memory_mib=32)
        self.assertEqual(self.run_queue(), 2)
        self.assertEqual(self.results()[0]['status'], 'memory_limit')
        self.assertGreater(self.results()[0]['peak_rss_bytes'], 32*1024**2)

    def test_partial_verdict_nonzero_exit_is_error(self):
        self.init('A[] failure\n')
        self.run_queue()
        self.assertEqual(self.results()[0]['status'], 'error')
        self.assertIsNone(self.results()[0]['verdict'])

    def test_empty_result_is_error(self):
        self.init('A[] missing\n'); self.run_queue()
        self.assertEqual(self.results()[0]['status'], 'error')

    def test_snapshot_isolation_and_tamper_detection(self):
        self.init(); self.model.write_text('changed external original')
        self.assertEqual(self.run_queue(), 0)
        (self.queue/'model.xml').write_text('changed queue snapshot')
        with self.assertRaisesRegex(ValueError, 'input changed'): self.run_queue()

    def test_exclusive_worker(self):
        self.init()
        with m.lock_queue(self.queue):
            with self.assertRaisesRegex(RuntimeError, 'active worker'): self.run_queue()

    def test_pause_resume_and_stop_from_separate_process(self):
        self.init('A[] slow\nE<> slow\n')
        p = self.worker(); self.wait_phase('running')
        self.assertTrue(m.status(self.queue)['worker_active'])
        m.save(self.queue/'control.json', {'action':'pause'})
        self.wait_phase('paused')
        self.assertEqual(len(self.results()), 1)
        time.sleep(.15); self.assertEqual(len(self.results()), 1)
        m.save(self.queue/'control.json', {'action':'run'})
        self.wait_phase('running')
        child = m.read(self.queue/'attempts'/m.read(self.queue/'status.json')['attempt']/'attempt.json')['pid']
        m.save(self.queue/'control.json', {'action':'stop'})
        self.assertEqual(p.wait(timeout=5), 2)
        self.assertFalse(m.alive(child))
        self.assertEqual({r['status'] for r in self.results()}, {'success','stopped'})
        self.assertEqual(self.run_queue(), 0)
        self.assertEqual(len(self.results()), 3)

    def test_missing_metrics_fail_closed(self):
        self.init('A[] slow\n')
        with patch.object(m, 'sample', return_value={'rss_bytes':None,'peak_rss_bytes':None,'cpu_seconds':None}): self.run_queue()
        self.assertEqual(self.results()[0]['status'], 'monitor_error')

    def test_orphan_refuses_restart(self):
        self.init('A[] true\n')
        attempt=self.queue/'attempts'/'001-orphan'; attempt.mkdir(parents=True)
        m.save(attempt/'attempt.json', {'pid':os.getpid()})
        with self.assertRaisesRegex(RuntimeError, 'may still be alive'): self.run_queue()

    def test_recover_dead_attempt_without_overwriting(self):
        self.init('A[] true\n')
        attempt=self.queue/'attempts'/'001-dead'; attempt.mkdir(parents=True)
        m.save(attempt/'attempt.json', {'pid':None})
        self.assertEqual(self.run_queue(), 0)
        self.assertTrue((attempt/'attempt.json').exists())
        self.assertEqual(len(list((self.queue/'attempts').iterdir())), 2)

    @unittest.skipIf(os.name == 'nt', 'POSIX flock failure injection')
    def test_unsupported_lock_is_not_reported_as_live_worker(self):
        self.init()
        with patch('fcntl.flock', side_effect=OSError(errno.EINVAL, 'unsupported')):
            with self.assertRaisesRegex(RuntimeError, 'filesystem'):
                m.status(self.queue)

    def test_limits_reject_nonfinite(self):
        with self.assertRaises(ValueError): self.init(timeout=float('nan'))
        self.assertFalse(self.queue.exists())

@unittest.skipUnless(os.name == 'nt', 'Native Windows job regression')
class WindowsProcessTreeTests(unittest.TestCase):
    setUp = ManagerTests.setUp
    init = ManagerTests.init
    run_queue = ManagerTests.run_queue
    results = ManagerTests.results
    worker = ManagerTests.worker

    def tree(self, mode, **limits):
        child = self.root/'child.py'
        child.write_text('''import os,sys,time,pathlib
pathlib.Path(sys.argv[1]).write_text(str(os.getpid()))
b=bytearray(128*1024*1024)
if sys.argv[2]=='success':
 print('Verifying formula 1',flush=True)
 print(' -- Formula is satisfied.',flush=True)
else: time.sleep(30)
''')
        marker = self.root/'child.pid'
        self.fake.write_text('''import sys,subprocess,pathlib,time
if '--version' in sys.argv: sys.exit(0)
subprocess.Popen([sys.executable, sys.argv[1], sys.argv[2], sys.argv[3]])
while not pathlib.Path(sys.argv[2]).exists(): time.sleep(.01)
if sys.argv[3]=='wait': time.sleep(30)
''')
        self.init('A[] true\n', **limits)
        cfg = m.read(self.queue/'queue.json')
        cfg['options'] = [str(self.fake), str(child), str(marker), mode]
        m.save(self.queue/'queue.json', cfg)
        return marker

    def child_gone(self, marker):
        self.assertTrue(marker.exists(), 'child must have actually started')
        pid = int(marker.read_text())
        deadline = time.monotonic()+5
        while m.alive(pid) and time.monotonic()<deadline:
            time.sleep(.02)
        self.assertFalse(m.alive(pid), f'owned child {pid} survived cleanup')

    def test_child_memory_limit_and_unrelated_process_survives(self):
        outsider = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)'])
        self.addCleanup(lambda: (outsider.kill(), outsider.wait()) if outsider.poll() is None else None)
        marker = self.tree('wait', memory_mib=96)
        self.assertEqual(self.run_queue(), 2)
        result = self.results()[0]
        self.assertEqual(result['status'], 'memory_limit')
        self.assertIsNone(result['verdict'])
        self.assertGreater(result['peak_rss_bytes'], 96*1024**2)
        self.child_gone(marker)
        self.assertIsNone(outsider.poll())

    def test_timeout_cleans_child_after_leader_exit(self):
        marker = self.tree('exit', timeout=1, memory_mib=256)
        self.assertEqual(self.run_queue(), 2)
        self.assertEqual(self.results()[0]['status'], 'timeout')
        self.child_gone(marker)

    def test_stop_cleans_owned_descendants(self):
        marker = self.tree('wait', memory_mib=256)
        worker = self.worker()
        deadline = time.monotonic()+8
        while not marker.exists() and time.monotonic()<deadline:
            time.sleep(.02)
        self.assertTrue(marker.exists())
        m.save(self.queue/'control.json', {'action':'stop'})
        self.assertEqual(worker.wait(timeout=8), 2)
        self.assertEqual(self.results()[0]['status'], 'stopped')
        self.child_gone(marker)

    def test_child_output_after_leader_exit_remains_successful(self):
        marker = self.tree('success', memory_mib=256)
        self.assertEqual(self.run_queue(), 0)
        self.assertEqual(self.results()[0]['verdict'], 'satisfied')
        self.child_gone(marker)
        session = next((self.queue/'sessions').glob('*/session.json'))
        self.assertIn('aggregate', m.read(session)['hardware']['memory_measurement'])

    def test_job_setup_failure_keeps_error_without_verdict(self):
        self.init('A[] true\n')
        with patch('uppaal_mcp.windows_process.create_job', return_value=None):
            self.assertEqual(self.run_queue(), 2)
        self.assertEqual(self.results()[0]['status'], 'error')
        self.assertIsNone(self.results()[0]['verdict'])

    def test_job_monitor_failure_cleans_descendants(self):
        from uppaal_mcp.windows_process import WindowsProcess
        marker = self.tree('wait', memory_mib=256)
        original = WindowsProcess.sample
        def fail_once_child_started(proc):
            if marker.exists():
                raise OSError('injected owned-job monitor failure')
            return original(proc)
        with patch.object(WindowsProcess, 'sample', fail_once_child_started):
            self.assertEqual(self.run_queue(), 2)
        self.assertEqual(self.results()[0]['status'], 'monitor_error')
        self.assertIsNone(self.results()[0]['verdict'])
        self.child_gone(marker)


if __name__ == '__main__': unittest.main()
