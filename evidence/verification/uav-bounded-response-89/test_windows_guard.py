"""Real Windows synthetic controls only; never invokes UPPAAL. Run natively."""
import ctypes
import json
import multiprocessing
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
import guard
from guard import Guard
import windows_native as win


def broken_monitor(conn,deadline,parent):
    with patch.object(win.Job,'metrics',side_effect=OSError('synthetic monitor failure')):
        guard.watchdog(conn,deadline,parent)


def controller_process(directory):
    g=Guard(15)
    Path(directory,'watchdog.pid').write_text(str(g.p.pid))
    try:g.run([sys.executable,'-c',tree_code()],directory,10,256*1024**2)
    finally:g.close()


def tree_code():
    leaf='import os,time; print(os.getpid(),flush=True); time.sleep(30)'
    middle='import os,subprocess,sys,time; print(os.getpid(),flush=True); subprocess.Popen([sys.executable,"-c",'+repr(leaf)+']); time.sleep(30)'
    return 'import os,subprocess,sys,time; print(os.getpid(),flush=True); subprocess.Popen([sys.executable,"-c",'+repr(middle)+'],creationflags=0x200); time.sleep(30)'


@unittest.skipUnless(os.name=='nt','Requires real native Windows; Linux execution is NOT Windows test evidence')
class WindowsControls(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='issue89 space ');self.directory=Path(self.tmp.name)
        self.guard=Guard(20)

    def tearDown(self):
        self.guard.close();self.tmp.cleanup()

    def invoke(self,code,cap=5,memory=256*1024**2):
        return self.guard.run([sys.executable,'-c',code],self.directory,cap,memory)

    def stopped(self,pids):
        until=time.monotonic()+3
        for pid in pids:
            h=win.open_process(0x100000,False,pid)
            if not h:
                self.assertEqual(ctypes.get_last_error(),87);continue
            try:
                while not win.completed(h) and time.monotonic()<until:time.sleep(.02)
                self.assertTrue(win.completed(h),'Owned PID still running: '+str(pid))
            finally:win.close(h)

    def pids(self,count=3):
        path=self.directory/'stdout.txt';until=time.monotonic()+5
        while time.monotonic()<until:
            if path.exists():
                lines=path.read_text(encoding='utf-8').splitlines()
                if len(lines)>=count:return [int(x) for x in lines]
            time.sleep(.02)
        self.fail('Synthetic child PID output missing')

    def owned(self):
        self.guard.conn.send(dict(op='run',command=[sys.executable,'-c',tree_code()],cwd=str(self.directory),
                                 cap=10,memory_bytes=256*1024**2,stdout=str(self.directory/'stdout.txt'),stderr=str(self.directory/'stderr.txt')))
        self.assertTrue(self.guard.conn.poll(5));msg=self.guard.conn.recv()
        self.assertEqual(msg['event'],'owned',msg);self.guard.pid=msg['pid'];return msg['pid']

    def test_native_identity_api_layout_and_pe(self):
        self.assertEqual(ctypes.sizeof(win.EXT_LIMIT),144)
        self.assertEqual(ctypes.sizeof(win.STARTUP_EX),112)
        h=win.identity();self.assertEqual(h['os'],'Windows');self.assertGreater(h['physical_ram_bytes'],0)
        self.assertEqual(win.pe_info(sys.executable)['machine'],'0x8664')
        self.assertIsInstance(win.existing_verifiers(),list)
        for content in [b'\x7fELF'+b'\0'*100,b'MZ'+b'\0'*100]:
            p=self.directory/'bad.exe';p.write_bytes(content)
            with self.assertRaises(ValueError):win.pe_info(p)
        content=bytearray(Path(sys.executable).read_bytes());off=int.from_bytes(content[60:64],'little')
        content[off+23]|=0x20;p.write_bytes(content)
        with self.assertRaises(ValueError):win.pe_info(p)

    def test_approval_binds_native_host_python_path_and_binary(self):
        from driver import verify_native_inputs
        root=Path(r'C:\issue89-persistent')
        a=dict(win.identity(),persistent_checkout=str(root),verifyta_path=sys.executable,
               executable_sha256=win.pe_info(sys.executable)['sha256'])
        cfg=dict(verifyta_path=sys.executable,executable_sha256=a['executable_sha256'])
        self.assertEqual(verify_native_inputs(a,cfg,root),Path(sys.executable).resolve())
        for key in ['os','native_host','machine_guid_sha256','python_path','python_sha256','python_version','executable_sha256','persistent_checkout']:
            with self.assertRaises((ValueError,OSError),msg=key):verify_native_inputs(dict(a,**{key:'WRONG'}),cfg,root)
        unc=Path(r'\\wsl.localhost\Ubuntu\tmp\issue89')
        with self.assertRaisesRegex(ValueError,'persistent Windows'):verify_native_inputs(dict(a,persistent_checkout=str(unc)),cfg,unc)
        with self.assertRaisesRegex(ValueError,'Verifier path'):verify_native_inputs(a,dict(cfg,verifyta_path=r'C:\wrong.exe'),root)

    def test_success_nonzero_and_argument_quoting(self):
        code='import sys; print(repr(sys.argv[1]))'
        arg='space with "quote" and trailing \\'
        r=self.guard.run([sys.executable,'-c',code,arg],self.directory,5,256*1024**2)
        self.assertEqual(r['status'],'exited',r);self.assertEqual(r['exit_code'],0)
        self.assertEqual((self.directory/'stdout.txt').read_text(encoding='utf-8').strip(),repr(arg));self.assertTrue(r['cleanup_confirmed'])
        self.directory=self.directory/'nonzero'
        self.assertEqual(self.invoke('raise SystemExit(7)')['exit_code'],7)

    def test_fast_exit_waits_for_owned_console_host_within_deadline(self):
        for i in range(12):
            r=self.guard.run([sys.executable,'-c','pass'],self.directory/str(i),3,256*1024**2)
            self.assertEqual(r['status'],'exited',r);self.assertEqual(r['exit_code'],0)
            self.assertTrue(r['cleanup_confirmed'])

    def test_timeout_owned_tree_and_unrelated_survives(self):
        unrelated=subprocess.Popen([sys.executable,'-c','import time;time.sleep(30)'])
        try:
            r=self.invoke(tree_code(),cap=2)
            self.assertEqual(r['status'],'timeout');self.assertLess(r['wall_seconds'],2)
            self.stopped(self.pids());self.assertIsNone(unrelated.poll())
            self.assertGreater(r['peak_rss_bytes'],0);self.assertGreaterEqual(r['cpu_seconds'],0)
        finally:unrelated.terminate();unrelated.wait(3)

    def test_memory_stop_includes_descendant(self):
        leaf='import time; x=bytearray(80*1024*1024); time.sleep(30)'
        r=self.invoke('import subprocess,sys,time; subprocess.Popen([sys.executable,"-c",'+repr(leaf)+']);time.sleep(30)',memory=48*1024**2)
        self.assertEqual(r['status'],'memory_limit');self.assertGreater(r['peak_rss_bytes'],48*1024**2)
        self.assertTrue(r['cleanup_confirmed'])

    def test_breakaway_rejected(self):
        code='import subprocess,sys\ntry: subprocess.Popen([sys.executable,"-c","pass"],creationflags=0x1000000)\nexcept OSError: print("denied")\nelse: raise SystemExit(99)'
        r=self.invoke(code);self.assertEqual(r['exit_code'],0)
        self.assertEqual((self.directory/'stdout.txt').read_text(encoding='utf-8').strip(),'denied')

    def test_stop_command(self):
        timer=threading.Timer(.6,lambda:self.guard.conn.send({'op':'stop'}));timer.start()
        try:
            r=self.invoke(tree_code());self.assertEqual(r['status'],'stopped');self.stopped(self.pids())
        finally:timer.join()

    def test_status_json_unreadable_and_session_deadline(self):
        (self.directory/'status.json').mkdir()
        self.guard.close();self.guard=Guard(4)
        r=self.invoke(tree_code(),cap=15)
        self.assertEqual(r['status'],'session_limit');self.assertLess(r['wall_seconds'],4);self.stopped(self.pids())

    def test_watchdog_death_kills_tree(self):
        self.owned();self.guard.conn.send({'op':'go'});pids=self.pids()
        self.guard.p.terminate();self.guard.p.join(3);self.stopped(pids)

    def test_watchdog_death_before_resume_kills_suspended_child(self):
        pid=self.owned();self.guard.p.terminate();self.guard.p.join(3);self.stopped([pid])
        self.assertEqual((self.directory/'stdout.txt').read_bytes(),b'')

    def test_controller_eof_before_resume(self):
        pid=self.owned();self.guard.conn.close();self.guard.p.join(3)
        self.assertFalse(self.guard.p.is_alive());self.stopped([pid])

    def test_dead_controller_stops_tree(self):
        p=multiprocessing.get_context('spawn').Process(target=controller_process,args=(str(self.directory),));p.start()
        try:
            pids=self.pids();watchdog=int((self.directory/'watchdog.pid').read_text(encoding='utf-8'))
            p.terminate();p.join(3);self.stopped(pids+[watchdog])
        finally:
            if p.is_alive():p.terminate();p.join(3)

    def test_blocked_controller_does_not_block_deadline(self):
        self.guard.close();self.guard=Guard(4)
        self.owned();self.guard.conn.send({'op':'go'});pids=self.pids()
        # Controller does not consume pipe events; watchdog terminates job first.
        time.sleep(2.3);self.stopped(pids)
        self.assertTrue(self.guard.conn.poll(2));r=self.guard.conn.recv();self.assertEqual(r['status'],'session_limit')

    def test_monitor_failure_halts_and_cleans(self):
        self.guard.close()
        ctx=multiprocessing.get_context('spawn');g=Guard.__new__(Guard)
        g.conn,c=ctx.Pipe();g.deadline=time.monotonic()+15;g.pid=None;g.closed=False
        g.p=ctx.Process(target=broken_monitor,args=(c,g.deadline,os.getpid()));g.p.start();c.close()
        self.guard=g;self.assertTrue(g.conn.poll(5));self.assertEqual(g.conn.recv(),{'event':'ready'})
        r=self.invoke('import time;time.sleep(30)')
        self.assertEqual(r['status'],'error');self.assertIn('synthetic monitor failure',r['reason']);self.assertTrue(r['cleanup_confirmed'])

    def test_telemetry_unwritable_blocks_launch(self):
        (self.directory/'telemetry.jsonl').mkdir()
        with self.assertRaises(OSError):self.invoke('raise SystemExit(99)')
        self.assertFalse((self.directory/'stdout.txt').exists())

    def test_telemetry_flush_failure_stops_controller(self):
        with patch('guard.os.fsync',side_effect=OSError('synthetic telemetry write failure')):
            with self.assertRaisesRegex(OSError,'synthetic telemetry'):self.invoke('print("done")')
        self.assertFalse(self.guard.p.is_alive())

    def test_leader_exit_with_descendants_is_error(self):
        code='import subprocess,sys; subprocess.Popen([sys.executable,"-c","import time;time.sleep(30)"])'
        r=self.invoke(code);self.assertEqual(r['status'],'error');self.assertTrue(r['cleanup_confirmed'])

if __name__=='__main__':unittest.main(verbosity=2)
