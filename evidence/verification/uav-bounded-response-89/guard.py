"""Linux-only independent monotonic watchdog; never reads a status JSON file.

The watchdog owns one Linux process group per command. The exec child waits
behind a pipe until both watchdog and controller know its group ID. Parent EOF,
deadline, stop, telemetry error and monitor error all stop the owned group.
"""
import ctypes
import json
import multiprocessing
import os
from pathlib import Path
import select
import signal
import time

POLL = 0.05

def members(pgid):
    result = []
    for entry in Path('/proc').iterdir():
        if not entry.name.isdigit():
            continue
        try:
            fields = (entry/'stat').read_text().rsplit(') ',1)[1].split()
        except (FileNotFoundError, ProcessLookupError):
            continue
        # All owned descendants remain in this native Linux group/session.
        if int(fields[2]) == pgid:
            result.append((int(entry.name), fields))
    return result

def metrics(pgid):
    rows = members(pgid)
    live = [f for _,f in rows if f[0] != 'Z']
    return dict(rss_bytes=sum(int(f[21]) for f in live)*os.sysconf('SC_PAGE_SIZE'),
                sampled_cpu_seconds=sum(int(f[11])+int(f[12]) for _,f in rows)/os.sysconf('SC_CLK_TCK'),
                live_processes=len(live))

def kill_group(pgid):
    if pgid is None:
        return
    try:
        os.killpg(pgid, signal.SIGKILL)
    except ProcessLookupError:
        pass

def reap(pid):
    _, status, usage = os.wait4(pid, 0)
    return os.waitstatus_to_exitcode(status), usage

def launch(command, cwd, stdout, stderr, conn):
    """Fork behind a gate: ownership acknowledged before exec or descendants."""
    gate_r, gate_w = os.pipe()
    ready_r, ready_w = os.pipe()
    out = open(stdout, 'xb', buffering=0)
    err = open(stderr, 'xb', buffering=0)
    try:
        parent = os.getpid()
        pid = os.fork()
        if pid == 0:
            try:
                conn.close()
                os.close(gate_w)
                os.close(ready_r)
                os.setsid()
                # Kill blocked exec child if watchdog disappears before handoff.
                libc = ctypes.CDLL(None, use_errno=True)
                if libc.prctl(1, signal.SIGKILL, 0, 0, 0) != 0 or os.getppid() != parent:
                    os._exit(125)
                signal.signal(signal.SIGINT, signal.SIG_DFL)
                signal.signal(signal.SIGTERM, signal.SIG_DFL)
                os.dup2(out.fileno(),1)
                os.dup2(err.fileno(),2)
                os.write(ready_w,b'R')
                os.close(ready_w)
                if os.read(gate_r,1) != b'G':
                    os._exit(125)
                os.close(gate_r)
                os.chdir(cwd)
                os.execv(command[0], command)
            except BaseException:
                os._exit(126)
        os.close(gate_r)
        os.close(ready_w)
        if not select.select([ready_r],[],[],2)[0] or os.read(ready_r,1) != b'R':
            # pid is ours even when setsid failed; never signal somebody else's group.
            os.kill(pid,signal.SIGKILL)
            reap(pid)
            raise RuntimeError('Exec ownership gate failed')
        return pid, gate_w
    finally:
        os.close(ready_r)
        out.close()
        err.close()

def watchdog(conn, deadline):
    current = None
    halted = False
    def stopping(*_):
        nonlocal halted
        halted = True
    signal.signal(signal.SIGTERM, stopping)
    signal.signal(signal.SIGINT, stopping)
    try:
        conn.send({'event':'ready'})
        while not halted and time.monotonic() < deadline:
            if not conn.poll(POLL):
                continue
            msg=conn.recv()
            if msg['op'] == 'close':
                return
            if msg['op'] != 'run':
                raise RuntimeError('Invalid watchdog command')
            started=time.monotonic()
            # Leave cleanup inside the approved cap, including sampling latency.
            attempt_deadline=min(started+msg['cap']-min(2,msg['cap']/10), deadline-2)
            current, gate=launch(msg['command'], msg['cwd'], msg['stdout'], msg['stderr'], conn)
            conn.send({'event':'owned','pgid':current})
            # Controller must know group before the verifier can run.
            if not conn.poll(min(2,max(0,attempt_deadline-time.monotonic()))) or conn.recv() != {'op':'go'}:
                os.close(gate)
                raise RuntimeError('Controller did not acknowledge owned process group')
            os.write(gate,b'G')
            os.close(gate)
            status='exited'
            peak=0
            max_cpu=0.0
            reason=None
            child_exit=None
            usage=None
            try:
                with open(msg['telemetry'],'x',encoding='utf-8',buffering=1) as log:
                    while True:
                        now=time.monotonic()
                        if halted:
                            status='stopped'; break
                        if now >= attempt_deadline:
                            status='session_limit' if attempt_deadline==deadline-2 else 'timeout'; break
                        if conn.poll():
                            control=conn.recv()  # EOF is a failure, followed by owned cleanup.
                            if control['op']=='stop':
                                status='stopped'; break
                            raise RuntimeError('Unexpected command during attempt')
                        sample=metrics(current)
                        peak=max(peak,sample['rss_bytes'])
                        max_cpu=max(max_cpu,sample['sampled_cpu_seconds'])
                        log.write(json.dumps({'monotonic':now,**sample})+'\n')
                        if sample['rss_bytes'] > msg['memory_bytes']:
                            status='memory_limit'; break
                        # wait4(WNOHANG) preserves kernel CPU/maxrss for a fast child.
                        pid, raw, ru=os.wait4(current,os.WNOHANG)
                        if pid:
                            child_exit=os.waitstatus_to_exitcode(raw); usage=ru
                            if sample['live_processes']:
                                # A stale sample may include the just-exited leader.
                                if any(p!=current and f[0]!='Z' for p,f in members(current)):
                                    status='error'; reason='Command left descendants running'
                            break
                        time.sleep(POLL)
            except BaseException as exc:
                status='error'; reason=repr(exc)
            finally:
                kill_group(current)
                if usage is None:
                    child_exit,usage=reap(current)
                until=time.monotonic()+1
                while any(f[0]!='Z' for _,f in members(current)) and time.monotonic()<until:
                    time.sleep(POLL)
                if any(f[0]!='Z' for _,f in members(current)):
                    status='error';reason='Owned group cleanup failed'
                current=None
            conn.send(dict(event='result',status=status,reason=reason,exit_code=child_exit,
                           monotonic_start=started,monotonic_end=time.monotonic(),
                           wall_seconds=time.monotonic()-started,
                           cpu_seconds=usage.ru_utime+usage.ru_stime,
                           sampled_group_cpu_seconds=max_cpu,
                           peak_rss_bytes=max(peak,int(usage.ru_maxrss)*1024),
                           metric_scope='CPU wait4 leader/reaped children; peak max(sampled group RSS, wait4 maxrss)',
                           cleanup_confirmed=True))
            if status not in ['exited','timeout','memory_limit']:
                return
        conn.send({'event':'halt','reason':'session deadline or stop'})
    except BaseException as exc:
        try:
            conn.send({'event':'halt','reason':repr(exc)})
        except (BrokenPipeError,EOFError,OSError):
            pass
    finally:
        kill_group(current)
        if current is not None:
            try:
                reap(current)
            except ChildProcessError:
                pass
        conn.close()

class Guard:
    def __init__(self, seconds=1800):
        if os.name!='posix' or not Path('/proc/self/stat').exists():
            raise RuntimeError('Native Linux /proc required')
        ctx=multiprocessing.get_context('spawn')
        self.conn,child=ctx.Pipe()
        self.deadline=time.monotonic()+seconds
        self.p=ctx.Process(target=watchdog,args=(child,self.deadline))
        self.p.start(); child.close()
        self.pgid=None
        if not self.conn.poll(5) or self.conn.recv()!= {'event':'ready'}:
            self.close(); raise RuntimeError('Watchdog startup failed')

    def run(self,command,directory,cap,memory_bytes,cwd=None):
        directory=Path(directory)
        directory.mkdir(parents=True,exist_ok=True)
        self.conn.send(dict(op='run',command=[str(x) for x in command],cwd=str(cwd or directory),
                            cap=cap,memory_bytes=memory_bytes,stdout=str(directory/'stdout.txt'),
                            stderr=str(directory/'stderr.txt'),telemetry=str(directory/'telemetry.jsonl')))
        try:
            while True:
                if self.conn.poll(POLL):
                    msg=self.conn.recv()
                    if msg['event']=='owned':
                        self.pgid=msg['pgid']; self.conn.send({'op':'go'})
                    elif msg['event']=='result':
                        self.pgid=None; return msg
                    else:
                        raise RuntimeError('Watchdog failure: '+repr(msg))
                if not self.p.is_alive() or time.monotonic()>self.deadline+1:
                    raise RuntimeError('Watchdog died or exceeded whole-session deadline')
        except BaseException:
            kill_group(self.pgid)
            self.close()
            raise

    def close(self):
        try:
            self.conn.send({'op':'close' if self.pgid is None else 'stop'})
        except (BrokenPipeError,EOFError,OSError):
            pass
        self.conn.close()
        self.p.join(3)
        if self.p.is_alive():
            kill_group(self.pgid)
            self.p.terminate();self.p.join(2)
        if self.p.is_alive():
            self.p.kill();self.p.join(2)
            raise RuntimeError('Watchdog failed to stop cooperatively')
