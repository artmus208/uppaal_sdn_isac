"""Independent native Windows watchdog. Never reads status JSON or kills by name.

Deadlines and monitoring run without controller/disk dependencies. Telemetry is
bounded in watchdog memory and returned only AFTER cleanup; abrupt watchdog loss
means unavailable metrics, never invented success. Child stdout/trace remain raw.
"""
import json
import multiprocessing
import os
from pathlib import Path
import signal
import time
import windows_native as win

POLL=0.05

def watchdog(conn,deadline,parent_pid):
    job=None;parent=None
    try:
        win.native()
        # Ignore terminal Ctrl-C here: controller requests stop; deadlines remain live.
        signal.signal(signal.SIGINT,signal.SIG_IGN)
        parent=win.checked(win.open_process(0x100000,False,parent_pid))
        conn.send({'event':'ready'})
        while time.monotonic()<deadline:
            if win.completed(parent):return
            if not conn.poll(POLL):continue
            msg=conn.recv()
            if msg['op']=='close':return
            if msg['op']!='run':raise RuntimeError('Invalid watchdog command')
            started=time.monotonic()
            attempt_deadline=min(started+msg['cap']-min(2,msg['cap']/10),deadline-2)
            job=win.Job()
            job.launch(msg['command'],msg['cwd'],msg['stdout'],msg['stderr'])
            conn.send(dict(event='owned',pid=job.pid))
            if not conn.poll(min(2,max(0,attempt_deadline-time.monotonic()))) or conn.recv()!={'op':'go'}:
                raise RuntimeError('Controller did not acknowledge owned Windows job')
            if win.completed(parent) or time.monotonic()>=attempt_deadline:
                raise RuntimeError('Controller gone or deadline during startup')
            job.start()
            status='exited';reason=None;peak=0;cpu=0.0;private_peak=0;telemetry=[];code=None
            try:
                while True:
                    now=time.monotonic()
                    if win.completed(parent):status='error';reason='Controller died';break
                    if now>=attempt_deadline:
                        status='session_limit' if attempt_deadline==deadline-2 else 'timeout';break
                    if conn.poll():
                        if conn.recv()=={'op':'stop'}:status='stopped';break
                        raise RuntimeError('Unexpected control during attempt')
                    sample=job.metrics()
                    peak=max(peak,sample['rss_bytes'],sample['leader_peak_rss_bytes'])
                    cpu=max(cpu,sample['cpu_seconds']);private_peak=max(private_peak,sample['peak_job_private_commit_bytes'])
                    telemetry.append(dict(monotonic=now,**sample))
                    if sample['rss_bytes']>msg['memory_bytes']:status='memory_limit';break
                    if win.completed(job.process):
                        code=job.result_code()
                        # Windows conhost may outlive a fast console leader briefly.
                        # Drain within the existing deadline; never extend a slot.
                        until=min(time.monotonic()+0.25,attempt_deadline)
                        while job.has_live_descendants() and time.monotonic()<until:time.sleep(0.01)
                        if job.has_live_descendants():
                            status='error';reason='Command left descendants running after bounded exit grace'
                        if time.monotonic()>=attempt_deadline:
                            status='session_limit' if attempt_deadline==deadline-2 else 'timeout'
                        break
                    time.sleep(POLL)
            except BaseException as exc:status='error';reason=repr(exc)
            finally:
                job.terminate()
                until=min(time.monotonic()+1.5,deadline)
                while job.accounting().ActiveProcesses and time.monotonic()<until:time.sleep(0.01)
                clean=job.accounting().ActiveProcesses==0
                if not clean:status='error';reason='Owned Windows job cleanup unconfirmed'
                if code is None and win.completed(job.process):code=job.result_code()
                a=job.accounting();cpu=max(cpu,(a.TotalUserTime+a.TotalKernelTime)/1e7)
                job.close();job=None
            ended=time.monotonic()
            conn.send(dict(event='result',status=status,reason=reason,exit_code=code,
                           monotonic_start=started,monotonic_end=ended,wall_seconds=ended-started,
                           cpu_seconds=cpu,peak_rss_bytes=peak,peak_job_private_commit_bytes=private_peak,
                           metric_scope='Job cumulative CPU incl. exited descendants; max(sampled sum working sets, leader peak working set); private commit reported separately',
                           cleanup_confirmed=clean,_telemetry=telemetry))
            if status not in ['exited','timeout','memory_limit']:return
        conn.send(dict(event='halt',reason='Whole-session deadline'))
    except BaseException as exc:
        # Close job BEFORE reporting an error: a blocked/dead controller cannot keep children alive.
        if job is not None:job.close();job=None
        try:conn.send(dict(event='halt',reason=repr(exc)))
        except (BrokenPipeError,EOFError,OSError):pass
    finally:
        if job is not None:job.close()
        if parent:win.close(parent)
        conn.close()

class Guard:
    def __init__(self,seconds=1800):
        win.native()
        ctx=multiprocessing.get_context('spawn')
        self.conn,child=ctx.Pipe();self.deadline=time.monotonic()+seconds
        self.p=ctx.Process(target=watchdog,args=(child,self.deadline,os.getpid()))
        self.pid=None;self.closed=False
        self.p.start();child.close()
        if not self.conn.poll(5) or self.conn.recv()!={'event':'ready'}:
            self.close();raise RuntimeError('Windows watchdog startup failed')

    def run(self,command,directory,cap,memory_bytes,cwd=None):
        directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
        # Check telemetry destination before spawning. Runtime write failures halt after cleanup.
        log=open(directory/'telemetry.jsonl','x',encoding='utf-8')
        try:
            self.conn.send(dict(op='run',command=[str(x) for x in command],cwd=str(cwd or directory),
                                cap=cap,memory_bytes=memory_bytes,stdout=str(directory/'stdout.txt'),stderr=str(directory/'stderr.txt')))
            while True:
                if self.conn.poll(POLL):
                    msg=self.conn.recv()
                    if msg['event']=='owned':
                        self.pid=msg['pid'];self.conn.send({'op':'go'})
                    elif msg['event']=='result':
                        self.pid=None
                        samples=msg.pop('_telemetry')
                        for sample in samples:log.write(json.dumps(sample)+'\n')
                        log.flush();os.fsync(log.fileno())
                        return msg
                    else:raise RuntimeError('Watchdog failure: '+repr(msg))
                if not self.p.is_alive() or time.monotonic()>self.deadline+1:
                    raise RuntimeError('Watchdog died or exceeded whole-session deadline')
        except BaseException:self.close();raise
        finally:log.close()

    def close(self):
        if self.closed:return
        self.closed=True
        try:self.conn.send({'op':'close' if self.pid is None else 'stop'})
        except (BrokenPipeError,EOFError,OSError):pass
        self.conn.close();self.p.join(2)
        if self.p.is_alive():
            # Terminate watchdog only; Windows closes its sole job handle and kills descendants.
            self.p.terminate();self.p.join(2)
        if self.p.is_alive():raise RuntimeError('Windows watchdog termination failed')
