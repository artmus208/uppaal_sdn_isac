"""Persistent native verifyta queue. Run with python -m uppaal_mcp.verification_manager."""
from __future__ import annotations

import argparse
import csv
import errno
import ctypes
import hashlib
import json
import math
import os
import platform
import re
import shutil
import subprocess
import sys
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from .validation import parse_queries_text
from .verifyta import parse_verifyta_outcomes, summarize_status


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def save(path, value):
    path = Path(path)
    tmp = path.with_name(path.name + '.' + uuid4().hex + '.tmp')
    try:
        with tmp.open('w', encoding='utf-8', newline='\n') as f:
            json.dump(value, f, ensure_ascii=False, indent=2)
            f.write('\n')
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)


class QueueBusy(RuntimeError):
    pass


@contextmanager
def lock_queue(directory):
    """OS lock, automatically released on owner exit; never steal a live queue."""
    with (directory / 'worker.lock').open('a+b') as f:
        f.seek(0, 2)
        if f.tell() == 0:
            f.write(b'0'); f.flush()
        f.seek(0)
        try:
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            if exc.errno in (errno.EACCES, errno.EAGAIN):
                raise QueueBusy('Queue already has an active worker') from exc
            raise RuntimeError('Queue filesystem cannot provide an OS lock; use a local disk (not WSL/UNC storage)') from exc
        try:
            yield
        finally:
            if os.name == 'nt':
                f.seek(0)
                msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(f, fcntl.LOCK_UN)


def alive(pid):
    if os.name == 'nt':
        from ctypes import wintypes as w
        k = ctypes.WinDLL('kernel32', use_last_error=True)
        k.OpenProcess.restype = w.HANDLE
        k.OpenProcess.argtypes = [w.DWORD, w.BOOL, w.DWORD]
        k.GetExitCodeProcess.argtypes = [w.HANDLE, ctypes.POINTER(w.DWORD)]
        k.CloseHandle.argtypes = [w.HANDLE]
        h = k.OpenProcess(0x1000, False, pid)
        if not h:
            return ctypes.get_last_error() == 5  # access denied: conservatively live
        try:
            code = w.DWORD()
            return not k.GetExitCodeProcess(h, ctypes.byref(code)) or code.value == 259
        finally:
            k.CloseHandle(h)
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def sample(proc):
    """RSS/working set (not private bytes), OS peak and cumulative CPU seconds."""
    if os.name == 'nt':
        from ctypes import wintypes as w
        class Counters(ctypes.Structure):
            _fields_ = [('cb', w.DWORD), ('PageFaultCount', w.DWORD)] + [(n, ctypes.c_size_t) for n in
                ('PeakWorkingSetSize', 'WorkingSetSize', 'QuotaPeakPagedPoolUsage', 'QuotaPagedPoolUsage',
                 'QuotaPeakNonPagedPoolUsage', 'QuotaNonPagedPoolUsage', 'PagefileUsage', 'PeakPagefileUsage')]
        k = ctypes.WinDLL('kernel32', use_last_error=True)
        ps = ctypes.WinDLL('psapi', use_last_error=True)
        ps.GetProcessMemoryInfo.argtypes = [w.HANDLE, ctypes.POINTER(Counters), w.DWORD]
        k.GetProcessTimes.argtypes = [w.HANDLE] + [ctypes.POINTER(w.FILETIME)] * 4
        h = w.HANDLE(int(proc._handle))
        m = Counters(); m.cb = ctypes.sizeof(m)
        ok = ps.GetProcessMemoryInfo(h, ctypes.byref(m), m.cb)
        times = [w.FILETIME() for _ in range(4)]
        cpu_ok = k.GetProcessTimes(h, *(ctypes.byref(t) for t in times))
        ticks = lambda t: (t.dwHighDateTime << 32) + t.dwLowDateTime
        return {'rss_bytes': m.WorkingSetSize if ok else None,
                'peak_rss_bytes': m.PeakWorkingSetSize if ok else None,
                'cpu_seconds': sum(ticks(t) for t in times[2:]) / 1e7 if cpu_ok else None}
    try:
        status = Path(f'/proc/{proc.pid}/status').read_text()
        fields = Path(f'/proc/{proc.pid}/stat').read_text().rsplit(')', 1)[1].split()
        def kb(key):
            m = re.search(r'^' + key + r':\s+(\d+)', status, re.M)
            return int(m[1]) * 1024 if m else None
        return {'rss_bytes': kb('VmRSS'), 'peak_rss_bytes': kb('VmHWM'),
                'cpu_seconds': (int(fields[11]) + int(fields[12])) / os.sysconf('SC_CLK_TCK')}
    except (OSError, ValueError, IndexError):
        return {'rss_bytes': None, 'peak_rss_bytes': None, 'cpu_seconds': None}


def progress(path):
    with path.open('rb') as f:
        f.seek(0, 2); f.seek(max(0, f.tell() - 16384))
        matches = re.findall(rb'Throughput:\s*(\d+) states/sec, Load:\s*(\d+) states', f.read())
    return {'throughput': int(matches[-1][0]), 'load': int(matches[-1][1])} if matches else {'throughput': None, 'load': None}


def initialize(directory, model, queries, executable, timeout=600, memory_mib=2048):
    if not all(math.isfinite(x) and x > 0 for x in (timeout, memory_mib)):
        raise ValueError('Time and memory limits must be finite and positive')
    executable = Path(shutil.which(str(executable)) or executable).resolve(strict=True)
    if os.name != 'nt' and executable.suffix.lower() == '.exe':
        raise ValueError('Run this manager in Windows Python for Windows verifyta; WSL PID metrics are not native metrics')
    if os.name != 'nt' and not sys.platform.startswith('linux'):
        raise ValueError('Resource monitoring supports native Windows and Linux only')
    if os.name == 'nt' and str(directory).startswith('\\\\'):
        raise ValueError('Store the queue on a local Windows drive, not a WSL/UNC path')
    model_bytes = Path(model).read_bytes()
    query_bytes = Path(queries).read_bytes()
    formulas = parse_queries_text(query_bytes.decode('utf-8-sig'))
    if not formulas:
        raise ValueError('No queries: use a .q file with one formula per line')
    directory.mkdir(parents=True, exist_ok=False)
    (directory/'model.xml').write_bytes(model_bytes)
    (directory/'queries.q').write_bytes(query_bytes)
    tasks = []
    for n, formula in enumerate(formulas, 1):
        name = f'query-{n:03d}.q'
        (directory/name).write_bytes((formula+'\n').encode())
        tasks.append({'id': f'{n:03d}', 'query': formula, 'file': name, 'query_hash': digest(directory/name)})
    save(directory/'queue.json', {'schema': 1, 'created_at': now(), 'model_hash': digest(directory/'model.xml'),
         'query_pack_hash': digest(directory/'queries.q'), 'executable': str(executable), 'executable_hash': digest(executable),
         'timeout_seconds': timeout, 'memory_stop_bytes': int(memory_mib*1024**2), 'options': ['-o', '0', '-t', '0'], 'tasks': tasks})
    save(directory/'control.json', {'action': 'run'})
    save(directory/'status.json', {'phase': 'ready', 'updated_at': now()})


def verify_inputs(directory, config):
    for name, expected in [('model.xml', config['model_hash']), ('queries.q', config['query_pack_hash']),
                           *[(t['file'], t['query_hash']) for t in config['tasks']]]:
        if digest(directory/name) != expected:
            raise ValueError('Queue input changed: '+name)
    if digest(config['executable']) != config['executable_hash']:
        raise ValueError('Verifier executable changed; initialize a new queue')


def control(directory):
    action = read(directory/'control.json')['action']
    if action not in ('run', 'pause', 'stop'):
        raise ValueError('Invalid queue control')
    return action


def status(directory):
    result = read(directory/'status.json')
    try:
        with lock_queue(directory):
            result['worker_active'] = False
    except QueueBusy:
        result['worker_active'] = True
    return result


def history(directory, task):
    return sorted((directory/'attempts').glob(task['id']+'-*'))


def completed(directory, task, config):
    for attempt in history(directory, task):
        rp = attempt/'result.json'
        if not rp.exists():
            meta = read(attempt/'attempt.json')
            if meta.get('pid') and alive(meta['pid']):
                raise RuntimeError(f'Unfinished child PID {meta["pid"]} may still be alive; inspect {attempt}')
            continue
        r = read(rp)
        if (r['status'] == 'success' and r['verdict'] in ('satisfied', 'violated') and
            r['model_hash'] == config['model_hash'] and r['query_hash'] == task['query_hash']):
            return True
    return False


def publish(directory, phase, **kwargs):
    value = {'phase': phase, 'updated_at': now(), **kwargs}
    save(directory/'status.json', value)
    print(json.dumps(value, ensure_ascii=False), flush=True)


def run_attempt(directory, config, task, session, interval):
    attempt = directory/'attempts'/(task['id']+'-'+uuid4().hex)
    attempt.mkdir(parents=True)
    command = [config['executable'], *config['options'], '-X', str(attempt/'trace'), str(directory/'model.xml'), str(directory/task['file'])]
    meta = {'run_id': attempt.name, 'started_at': now(), 'command': command, 'cwd': str(Path(config['executable']).parent),
            'model_hash': config['model_hash'], 'query_hash': task['query_hash'], 'formula': task['query'], 'session': session,
            'timeout_seconds': config['timeout_seconds'], 'memory_stop_bytes': config['memory_stop_bytes'], 'pid': None}
    save(attempt/'attempt.json', meta)
    started = time.monotonic(); proc = None; reason = None; peak = None; cpu = None
    try:
        with (attempt/'stdout.txt').open('wb') as stdout, (attempt/'stderr.txt').open('wb') as stderr, (attempt/'telemetry.csv').open('w', newline='') as telemetry:
            writer = csv.DictWriter(telemetry, fieldnames=['elapsed_seconds','rss_bytes','peak_rss_bytes','cpu_seconds','throughput','load'])
            writer.writeheader()
            proc = subprocess.Popen(command, cwd=meta['cwd'], stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr)
            meta['pid'] = proc.pid; save(attempt/'attempt.json', meta)
            while True:
                metrics = sample(proc)
                if metrics['peak_rss_bytes'] is not None: peak = max(peak or 0, metrics['peak_rss_bytes'])
                if metrics['cpu_seconds'] is not None: cpu = metrics['cpu_seconds']
                elapsed = time.monotonic()-started
                row = {'elapsed_seconds': elapsed, **metrics, **progress(attempt/'stdout.txt')}
                writer.writerow(row); telemetry.flush()
                publish(directory, 'running', task=task['id'], attempt=attempt.name, **row)
                if proc.poll() is not None: break
                if control(directory) == 'stop': reason = 'stopped'
                elif elapsed >= config['timeout_seconds']: reason = 'timeout'
                elif metrics['rss_bytes'] is None: reason = 'monitor_error'
                elif metrics['rss_bytes'] > config['memory_stop_bytes']: reason = 'memory_limit'
                if reason:
                    proc.kill(); proc.wait(); break
                time.sleep(interval)
    except KeyboardInterrupt:
        reason = 'stopped'
        save(directory/'control.json', {'action': 'stop'})
    except Exception as exc:
        reason = 'error'
        meta['manager_error'] = f'{type(exc).__name__}: {exc}'
    finally:
        if proc is not None and proc.poll() is None:
            proc.kill(); proc.wait()
    text = lambda name: (attempt/name).read_text(encoding='utf-8', errors='replace') if (attempt/name).exists() else ''
    out, err = text('stdout.txt'), text('stderr.txt')
    outcomes = parse_verifyta_outcomes(out, [task['query']])
    parsed = summarize_status(proc.returncode if proc else -1, outcomes, out, err, expected_query_count=1)
    verdict = None
    if reason is None:
        if parsed in ('satisfied','not_satisfied'):
            reason = 'success'; verdict = 'satisfied' if parsed == 'satisfied' else 'violated'
        else:
            reason = 'inconclusive' if parsed == 'inconclusive' else 'error'
    result = {**meta, 'finished_at': now(), 'elapsed_seconds': time.monotonic()-started,
              'status': reason, 'verdict': verdict, 'returncode': proc.returncode if proc else None,
              'peak_rss_bytes': peak, 'cpu_seconds': cpu, 'states_explored': None,
              'tool_version': read(directory/'sessions'/session/'session.json')['tool_version'],
              'stdout_reference': 'stdout.txt', 'stderr_reference': 'stderr.txt', 'trace_paths': [p.name for p in attempt.glob('trace*')]}
    save(attempt/'result.json', result)
    save(attempt/'hashes.json', {p.name: digest(p) for p in attempt.iterdir() if p.is_file()})
    return result


def start(directory, interval=1):
    with lock_queue(directory):
        config = read(directory/'queue.json'); verify_inputs(directory, config)
        # Check orphaned attempts before starting any native process.
        pending = [t for t in config['tasks'] if not completed(directory, t, config)]
        if not pending:
            publish(directory, 'completed', completed=len(config['tasks']), total=len(config['tasks']))
            return 0
        # Reset old requests before preflight, so a new stop/pause is not lost.
        save(directory/'control.json', {'action': 'run'})
        session = uuid4().hex
        sp = directory/'sessions'/session; sp.mkdir(parents=True)
        with (sp/'version.stdout.txt').open('wb') as out, (sp/'version.stderr.txt').open('wb') as err:
            v = subprocess.run([config['executable'],'--version'], cwd=Path(config['executable']).parent,
                               stdout=out, stderr=err, timeout=20)
        version = (sp/'version.stdout.txt').read_text(encoding='utf-8', errors='replace')
        if v.returncode or not version.strip():
            raise RuntimeError(f'Verifier preflight failed; see {sp}')
        hardware = {'platform': platform.platform(), 'processor': platform.processor(), 'logical_cpus': os.cpu_count(),
                    'python': sys.version, 'memory_measurement': 'native working set / Linux RSS, sampled; not a hard allocation cap',
                    'manager_hash': digest(__file__)}
        save(sp/'session.json', {'tool_version': version, 'hardware': hardware, 'started_at': now(),
                                 'queue_hash': digest(directory/'queue.json')})
        try:
            for task in pending:
                while control(directory) == 'pause':
                    publish(directory, 'paused', next_task=task['id']); time.sleep(interval)
                if control(directory) == 'stop': break
                result = run_attempt(directory, config, task, session, interval)
                if result['status'] in ('stopped', 'monitor_error', 'error'): break
            done = sum(completed(directory, t, config) for t in config['tasks'])
            publish(directory, 'completed' if done == len(config['tasks']) else 'incomplete', completed=done, total=len(config['tasks']))
            return 0 if done == len(config['tasks']) else 2
        except KeyboardInterrupt:
            save(directory/'control.json', {'action': 'stop'})
            publish(directory, 'stopped'); return 2


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest='action', required=True)
    p = sub.add_parser('init'); p.add_argument('directory', type=Path)
    p.add_argument('--model', type=Path, required=True); p.add_argument('--queries', type=Path, required=True)
    p.add_argument('--verifyta', required=True); p.add_argument('--timeout', type=float, default=600)
    p.add_argument('--memory-mib', type=float, default=2048)
    for name in ('start','continue','stop','pause','resume','status'):
        p = sub.add_parser(name); p.add_argument('directory', type=Path)
    a = ap.parse_args(argv); directory = a.directory.resolve()
    try:
        if a.action == 'init':
            initialize(directory, a.model, a.queries, a.verifyta, a.timeout, a.memory_mib)
        elif a.action in ('start','continue'):
            return start(directory)
        elif a.action == 'status':
            print(json.dumps(status(directory), ensure_ascii=False, indent=2))
        else:
            if not status(directory)['worker_active']:
                raise ValueError('No active worker; use start/continue')
            save(directory/'control.json', {'action': 'run' if a.action == 'resume' else a.action})
            print('Requested '+a.action+(' after current formula' if a.action == 'pause' else ''))
        return 0
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as exc:
        print(str(exc), file=sys.stderr); return 2


if __name__ == '__main__':
    raise SystemExit(main())
