#!/usr/bin/env python3
"""Issue #70: one fixed symbolic random-DFS campaign; no automatic retries."""
import argparse
import base64
import hashlib
import json
import platform
import re
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
INPUT = ROOT / 'evidence/scalability/family-series-68'
BASE = 'a51a77e7852aee514bb0217a17d970fcf94cb704'
SEARCH = ['-s', '-u', '-o', '2', '--exploration', '0', '--state-representation', '1',
          '-S', '1', '-n', '0', '-r', '20260929']
# Reuse the pinned native Windows driver; only its output/monitor directory changes.
sys.path.insert(0, str(INPUT))
import run_checks as driver

driver.g.HERE = HERE


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, obj):
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + '\n')


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()


def pins():
    data = json.loads((HERE / 'inputs.json').read_text())
    for name, digest in data['files'].items():
        if sha(ROOT / name) != digest:
            raise RuntimeError('Input drift: ' + name)
        original = subprocess.check_output(['git', 'show', BASE + ':' + name], cwd=ROOT)
        if hashlib.sha256(original).hexdigest() != digest:
            raise RuntimeError('Input differs from candidate commit: ' + name)
    if (HERE / 'monitor.ps1').read_bytes() != (INPUT / 'monitor.ps1').read_bytes():
        raise RuntimeError('Monitor differs from pinned tested implementation')
    return data


def hardware(folder):
    h = driver.probe(folder)
    if h['available_physical_ram_bytes'] < 3 * 1024**3:
        raise RuntimeError('Less than 3 GiB native RAM available; no process launched')
    return h


def controls():
    pins()
    folder = HERE / 'controls'
    folder.mkdir()  # Immutable; cannot repeat over an existing result.
    report = {'source_commit': git('rev-parse', 'HEAD'), 'hardware': hardware(folder),
              'evidence_kind': 'monitor_controls_not_model_checking', 'cases': []}
    cases = [
        ('normal', "[Console]::Out.Write('out'); [Console]::Error.Write('err'); Start-Sleep -Seconds 1", 5, 2*1024**3, 'success'),
        ('timeout', 'Start-Sleep -Seconds 10', 1, 2*1024**3, 'timeout'),
        ('memory', 'Start-Sleep -Seconds 10', 5, 1024**2, 'memory_limit'),
    ]
    for name, script, seconds, memory, expected in cases:
        encoded = base64.b64encode(("$ProgressPreference='SilentlyContinue'; " + script).encode('utf-16-le')).decode()
        rec = driver.monitor_run(folder, name, driver.POWERSHELL,
            ['-NoProfile', '-NonInteractive', '-EncodedCommand', encoded], seconds, memory_bytes=memory)
        checks = [rec['status'] == expected, rec['process_reaped'], rec['samples'] > 0,
                  rec['peak_private_bytes'] > 0, rec['peak_reported_working_set_bytes'] > 0]
        if name == 'normal':
            checks += [(folder/'normal.stdout.txt').read_bytes() == b'out',
                       (folder/'normal.stderr.txt').read_bytes() == b'err']
        if name == 'memory':
            checks += [max(rec['peak_private_bytes'], rec['peak_reported_working_set_bytes']) >= memory]
        report['cases'].append({'name': name, 'expected': expected, 'actual': rec['status'], 'passed': all(checks)})
        save(folder/'report.json', report)
        if not all(checks):
            raise RuntimeError('Monitor control failed: ' + name)
        print(name + ': control passed', flush=True)
    report['all_passed'] = True
    save(folder/'report.json', report)


def campaign(exe):
    inputs = pins()
    if git('status', '--porcelain'):
        raise RuntimeError('Commit and durably save source/controls before verification')
    if not json.loads((HERE/'controls/report.json').read_text()).get('all_passed'):
        raise RuntimeError('Monitor controls required')
    source = git('rev-parse', 'HEAD')
    previous = HERE/'runs'/'service-001'
    previous_settings = json.loads((previous/'settings.json').read_text())
    previous_monitor = json.loads((previous/'version/tool.monitor.json').read_text())
    if previous_settings['status'] != 'stopped' or list(previous.glob('n*-*')):
        raise RuntimeError('Only the retained preflight with zero scientific attempts may continue')
    if previous_monitor['command'][-1:] != ['--version'] or previous_monitor['exit_code'] != 0 or not previous_monitor['process_reaped']:
        raise RuntimeError('Cannot reuse incomplete tool metadata')
    prior_stdout = (previous/'version/tool.stdout.txt').read_text()
    folder = HERE/'runs'/'service-002'
    folder.mkdir(parents=True)
    records = []
    version = next((line.strip() for line in prior_stdout.splitlines() if line.startswith('UPPAAL ')), None)
    if not version:
        raise RuntimeError('Captured tool version missing')
    used = previous_monitor['runtime_seconds']
    settings = {'source_commit': source, 'base_commit': BASE, 'search': SEARCH,
                'seed': 20260929, 'per_behavior_seconds': 30, 'memory_limit_bytes': 2*1024**3,
                'total_verifier_seconds': 420, 'attempts_per_query': 1,
                'plan': [{'N': n, 'entity': i} for n in range(1,5) for i in range(n)],
                'working_tree_before_campaign': 'clean', 'status': 'running',
                'continuation': 'service-001 stopped during metadata only; no command or query is retried',
                'version_reference': str((previous/'version/tool.stdout.txt').relative_to(HERE)),
                'version_sha256': sha(previous/'version/tool.stdout.txt'),
                'version_source_commit': previous_settings['source_commit'],
                'version_monitor_status': previous_monitor['status'],
                'version_metadata_valid': True, 'version_memory': 'not_available',
                'prior_metadata_seconds': used}
    save(folder/'settings.json', settings)

    def run(name, args, seconds, n=None, i=None):
        nonlocal used, version
        cell = folder/name
        cell.mkdir()
        h = hardware(cell)
        if used + seconds + 5 > 420:
            raise RuntimeError('Total verifier budget exhausted')
        rec = driver.monitor_run(cell, 'tool', exe, args, seconds)
        used += rec['runtime_seconds']
        stdout = (cell/'tool.stdout.txt').read_text(errors='replace')
        explicit = driver.verdict(stdout) if n else None
        if name == 'version' and rec['status'] == 'success':
            version = next((s.strip() for s in stdout.splitlines() if s.startswith('UPPAAL ')), None)
        rec.update(run_id='service-002-'+name, source_commit=source, candidate_commit=BASE,
                   tool_version=version, N=n, entity=i, hardware_description=h,
                   operating_environment={'driver': platform.platform(), 'target': 'native Windows via WSL'},
                   execution_status=rec['status'], evidence_kind='direct_model_checking' if n else 'tool_metadata',
                   property_verdict=explicit if rec['status']=='success' else None,
                   raw_stdout_verdict=explicit, acceptance_status='not_reviewed',
                   monitor_reference=str((cell/'tool.monitor.json').relative_to(HERE)),
                   memory_samples_reference=str((cell/'tool.memory.csv').relative_to(HERE)),
                   model_hash=None, query_hash=None, result_per_query=[], states_explored='not_available')
        if n:
            model=INPUT/f'generated/n{n}/model.xml'
            query=INPUT/f'generated/n{n}/p4/u{i}-service.q'
            meta=json.loads(model.with_name('metadata.json').read_text())
            rec.update(model_path=str(model.relative_to(ROOT)), model_hash=sha(model),
                       query_path=str(query.relative_to(ROOT)), query_hash=sha(query),
                       generator_hash=meta['generator_hash'], source_hash=meta['source_hash'],
                       parameter_set=json.loads(model.with_name('parameters.json').read_text()),
                       instance_vector=json.loads(model.with_name('instance-vector.json').read_text()),
                       claim_scope=f'Existential service opportunity for entity {i} in full N={n}; not fairness or useful departure')
            if rec['property_verdict']:
                rec['result_per_query']=[{'formula':query.read_text().strip(), 'verdict':explicit}]
        for stream in ('stdout','stderr'):
            info=driver.store_stream(cell/f'tool.{stream}.txt')
            rec.update({stream+'_'+k:v for k,v in info.items()})
        rec['trace']={'requested':bool(n), 'files':[]}
        for path in sorted(cell.glob('witness*')):
            rec['trace']['files'].append(driver.store_stream(path))
        rec['trace']['availability']='present' if rec['trace']['files'] else 'not_produced' if n else 'not_requested'
        records.append(rec)
        save(folder/'runs.json', records)
        settings['used_seconds']=used
        save(folder/'settings.json', settings)
        print(f'{name}: {rec["status"]}, verdict={rec["property_verdict"]}, {rec["runtime_seconds"]:.3f}s', flush=True)
        if rec['status'] not in ('success','timeout','memory_limit') or not rec['process_reaped'] or not rec['samples']:
            raise RuntimeError('Tool/monitor error; stop campaign')
        if n and rec['status']=='success' and explicit is None:
            raise RuntimeError('Missing/ambiguous verdict; stop campaign')
        return rec, stdout

    try:
        # Help/version are metadata, not model checks. The emitted version is
        # reused verbatim; no retry of the fast process that escaped sampling.
        help_dir = folder/'help'
        help_dir.mkdir()
        help_hw = hardware(help_dir)
        command = [str(exe), '--help']
        begin = time.monotonic()
        result = subprocess.run(command, capture_output=True, timeout=10)
        elapsed = time.monotonic()-begin
        used += elapsed
        (help_dir/'stdout.txt').write_bytes(result.stdout)
        (help_dir/'stderr.txt').write_bytes(result.stderr)
        save(help_dir/'metadata.json', {'source_commit':source, 'kind':'tool_metadata_not_model_checking',
             'command':command, 'exit_code':result.returncode, 'runtime_seconds':elapsed,
             'hardware':help_hw, 'memory':'not_available; short metadata process',
             'stdout_sha256':sha(help_dir/'stdout.txt'), 'stderr_sha256':sha(help_dir/'stderr.txt')})
        help_text = result.stdout.decode(errors='replace')
        if result.returncode or '2:Random depth first' not in help_text:
            raise RuntimeError('Required search order unavailable')
        for n in range(1,5):
            for i in range(n):
                name=f'n{n}-u{i}-service'
                model=INPUT/f'generated/n{n}/model.xml'
                query=INPUT/f'generated/n{n}/p4/u{i}-service.q'
                args=SEARCH+['-t','0','-f',driver.winpath(folder/name/'witness'),driver.winpath(model),driver.winpath(query)]
                run(name, args, 30, n, i)
        settings['status']='completed'
    except BaseException as exc:
        settings['status']='stopped'
        settings['error']=str(exc)
        raise
    finally:
        settings['used_seconds']=used
        save(folder/'settings.json', settings)


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('action', choices=['controls','run','pins'])
    ap.add_argument('--verifyta', type=Path, default=Path('/mnt/d/UPPAAL/app/bin/verifyta.exe'))
    a=ap.parse_args()
    if a.action=='controls': controls()
    elif a.action=='run': campaign(a.verifyta.resolve())
    else: print('Pinned input files:',len(pins()['files']))
