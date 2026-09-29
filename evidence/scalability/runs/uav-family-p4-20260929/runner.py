"""Authorized Issue #76 campaign. Immutable cells, sequential, no retries."""
import argparse
import base64
import datetime
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import runpy
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SOURCE = ROOT / 'evidence/scalability/family-series-68'
BASE = 'c6b07b252f7d25e4879d49b9cb32bf381e9555fb'
MANIFEST = 'manifests/baselines/uav-family-r1.yaml'
MANIFEST_HASH = '5480bef5b00020735259f10eb43bdd9bc79ebc364a3bbcacad34c78fd0552cbf'
BINARY_HASH = '4c8af2716ff61f3cf35c6d1dc408ccf306d44bb22478e104548a8f0f7a3febe5'
PLAN_HASH = '73870650bd4025aacb6b20d3df133ead35332c60b1af90af8ba89a4637225460'
DURABLE = Path('/mnt/d/uppaal_mcp/evidence/scalability/runs/uav-family-p4-20260929/handoff')
sys.path.insert(0, str(SOURCE))
import run_checks as driver
# The reused driver only relocates logs/monitor, never any source/generated artifact.
driver.g.HERE = HERE


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')
    tmp.replace(path)


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()


def pins():
    audit = runpy.run_path(str(ROOT / 'scripts/check_family_baseline.py'))['audit'](ROOT)
    if sha(ROOT / MANIFEST) != MANIFEST_HASH or sha(SOURCE / 'p4-plan.json') != PLAN_HASH:
        raise RuntimeError('Manifest/plan changed')
    if (HERE / 'monitor.ps1').read_bytes() != (SOURCE / 'monitor.ps1').read_bytes():
        raise RuntimeError('Monitor differs from approved implementation')
    return audit


def checkpoint(label):
    git('add', str(HERE.relative_to(ROOT)))
    if git('diff', '--cached', '--name-only'):
        git('commit', '-m', 'P4: checkpoint ' + label + ' (#76)')
    # Required durable handoff checks. Do not infer the remote is GitHub.
    status = git('status', '--short', '--branch')
    head = git('log', '-1', '--oneline', '--decorate')
    remotes = git('remote', '-v')
    if git('status', '--porcelain'):
        raise RuntimeError('Unexpected dirty state at checkpoint')
    DURABLE.mkdir(parents=True, exist_ok=True)
    bundle = DURABLE / 'campaign-next.bundle'
    subprocess.run(['git', 'bundle', 'create', str(bundle), '--all'], cwd=ROOT, check=True,
                   stdout=subprocess.DEVNULL)
    subprocess.run(['git', 'bundle', 'verify', str(bundle)], cwd=ROOT, check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    bundle.replace(DURABLE / 'campaign.bundle')
    (DURABLE / 'checkpoint.txt').write_text(status+'\n'+head+'\n'+remotes+'\n')


def hardware(folder):
    h = driver.probe(folder)
    if h['available_physical_ram_bytes'] < 3 * 1024**3:
        raise RuntimeError('Less than 3 GiB native RAM: defer, no launch')
    if str(h['os_build']) != '26200' or not any('Ryzen 5 1400' in x for x in h['cpu_models']):
        raise RuntimeError('Host differs from approved Windows 11/Ryzen configuration')
    return h


def controls():
    pins()
    folder = HERE / 'controls'
    folder.mkdir()
    report = {'source_commit': git('rev-parse', 'HEAD'), 'kind': 'monitor_controls_not_verification', 'cases': []}
    cases = [('normal', "[Console]::Out.Write('out'); [Console]::Error.Write('err'); Start-Sleep -Seconds 1", 5, 2*1024**3, 'success'),
             ('timeout', 'Start-Sleep -Seconds 10', 1, 2*1024**3, 'timeout'),
             ('memory', 'Start-Sleep -Seconds 10', 5, 1024**2, 'memory_limit')]
    for name, script, limit, memory, expected in cases:
        cell = folder / name
        cell.mkdir()
        h = hardware(cell)
        code = base64.b64encode(("$ProgressPreference='SilentlyContinue'; " + script).encode('utf-16-le')).decode()
        rec = driver.monitor_run(cell, 'tool', driver.POWERSHELL,
                                ['-NoProfile', '-NonInteractive', '-EncodedCommand', code], limit, memory_bytes=memory)
        ok = rec['status'] == expected and rec['process_reaped'] and rec['samples'] > 0
        if name == 'normal':
            ok = ok and (cell/'tool.stdout.txt').read_bytes() == b'out' and (cell/'tool.stderr.txt').read_bytes() == b'err'
        if name == 'memory':
            ok = ok and max(rec['peak_private_bytes'], rec['peak_reported_working_set_bytes']) >= memory
        report['cases'].append({'name': name, 'passed': bool(ok), 'monitor': rec, 'hardware': h})
        save(folder/'report.json', report)
        print(name, 'control', bool(ok), flush=True)
        if not ok:
            raise RuntimeError('Monitor control failed')
    report['all_passed'] = True
    save(folder/'report.json', report)
    checkpoint('native monitor controls')


def plan():
    steps = json.loads((SOURCE/'p4-plan.json').read_text())['steps']
    for index, step in enumerate(steps):
        step['cell_id'] = f'{index:03d}-r{step["repeat"]}-' + (
            'generation' if step['phase'] == 'generation' else f'n{step["N"]}-' + step.get('query_id', step['phase']))
    return steps


def classify(rec, stdout, phase):
    explicit = driver.verdict(stdout) if phase in ('model-checking', 'load-and-parse') else None
    if rec['status'] == 'success' and phase != 'compile' and explicit is None:
        return 'verdict_error', None
    return rec['status'], explicit if rec['status'] == 'success' else None


def campaign(exe):
    pins()
    if git('status', '--porcelain'):
        raise RuntimeError('Clean committed and published source required')
    if sha(exe) != BINARY_HASH:
        raise RuntimeError('Verifier executable changed')
    if not json.loads((HERE/'controls/report.json').read_text()).get('all_passed'):
        raise RuntimeError('Monitor controls not passed')
    source_commit = git('rev-parse', 'HEAD')
    folder = HERE/'campaign-001'
    folder.mkdir()
    manifest = json.loads((ROOT/MANIFEST).read_text())
    steps = plan()
    records = [{**s, 'status': 'not_started', 'reason': 'pending', 'run_id': 'uav-p4-76-'+s['cell_id']} for s in steps]
    settings = {'source_commit': source_commit, 'base_commit': BASE,
                'baseline_id': manifest['metadata']['id'], 'baseline_manifest_sha256': MANIFEST_HASH,
                'authorization_reference': 'https://github.com/artmus208/uppaal_sdn_isac/issues/76',
                'activation_reference': 'https://github.com/artmus208/uppaal_sdn_isac/pull/75#issuecomment-5891123461',
                'status': 'running', 'budget_seconds': 7200, 'used_seconds': 0.0,
                'budget_measure': 'conservative Python elapsed around each verifier/monitor invocation, including monitor overhead; metadata included',
                'prelaunch_reserve_seconds': 90, 'working_tree_at_start': 'clean',
                'runner_sha256': sha(Path(__file__)), 'monitor_sha256': sha(HERE/'monitor.ps1'),
                'binary_sha256': sha(exe), 'metadata': [], 'operating_environment': platform.platform()}
    used = 0.0
    blocked = set()
    version = None

    def persist():
        settings['used_seconds'] = used
        save(folder/'settings.json', settings)
        save(folder/'runs.json', records)

    persist()
    try:
        for option in ('--version', '--help'):
            cell = folder / option[2:]
            cell.mkdir()
            h = hardware(cell)
            start = time.monotonic()
            env = {k: v for k, v in os.environ.items() if not k.startswith('UPPAAL_')}
            try:
                result = subprocess.run([str(exe), option], cwd=exe.parent, capture_output=True, timeout=15, env=env)
            except subprocess.TimeoutExpired as exc:
                used += time.monotonic()-start
                (cell/'stdout.txt').write_bytes(exc.stdout or b'')
                (cell/'stderr.txt').write_bytes(exc.stderr or b'')
                settings['metadata'].append({'command': [str(exe), option], 'status': 'timeout', 'hardware': h})
                raise
            elapsed = time.monotonic()-start
            used += elapsed
            (cell/'stdout.txt').write_bytes(result.stdout)
            (cell/'stderr.txt').write_bytes(result.stderr)
            text = result.stdout.decode(errors='replace')
            settings['metadata'].append({'command': [str(exe), option], 'exit_code': result.returncode,
                'runtime_seconds': elapsed, 'hardware': h, 'stdout_sha256': sha(cell/'stdout.txt'),
                'stderr_sha256': sha(cell/'stderr.txt'), 'kind': 'metadata_not_model_checking', 'memory': 'not_available_short_metadata_process'})
            persist()
            if result.returncode:
                raise RuntimeError('Metadata failed')
            if option == '--version':
                version = next((s.strip() for s in text.splitlines() if s.startswith('UPPAAL ')), None)
                if version != manifest['tool_version']:
                    raise RuntimeError('Tool version differs from baseline')
                settings['tool_version'] = version
            elif not all(token in text for token in ('--exploration', '--state-representation', 'Depth first')):
                raise RuntimeError('Expected tool search settings absent from help')
        persist()
        checkpoint('tool metadata before series')
        for s, rec in zip(steps, records):
            if used + 90 > 7200:
                raise RuntimeError('Total budget reserve exhausted')
            key = (s['repeat'], s.get('N')) if s['phase'] != 'generation' else None
            if key in blocked:
                rec.update(status='not_started', reason='compile/load prerequisite failed')
                persist()
                continue
            cell = folder / s['cell_id']
            cell.mkdir()
            rec.update(source_commit=source_commit, baseline_id=manifest['metadata']['id'],
                       baseline_manifest_sha256=MANIFEST_HASH, tool_version=version,
                       acceptance_status='not_reviewed', property_verdict=None)
            if s['phase'] == 'generation':
                cmd = [sys.executable, '-B', str(HERE/'generate_phase.py'), str(cell/'generated')]
                start = time.monotonic()
                try:
                    result = subprocess.run(cmd, capture_output=True, timeout=30)
                except subprocess.TimeoutExpired as exc:
                    (cell/'stdout.txt').write_bytes(exc.stdout or b'')
                    (cell/'stderr.txt').write_bytes(exc.stderr or b'')
                    rec.update(status='timeout', reason='generation timeout', command=cmd,
                               runtime_seconds=time.monotonic()-start, evidence_kind='static_generation_not_model_checking')
                    raise
                rec.update(status='success' if result.returncode == 0 else 'error', reason=None,
                           runtime_seconds=time.monotonic()-start, exit_code=result.returncode,
                           command=cmd, evidence_kind='static_generation_not_model_checking',
                           operating_environment=platform.platform())
                (cell/'stdout.txt').write_bytes(result.stdout)
                (cell/'stderr.txt').write_bytes(result.stderr)
                rec.update(stdout_sha256=sha(cell/'stdout.txt'), stderr_sha256=sha(cell/'stderr.txt'))
                persist()
                if result.returncode:
                    raise RuntimeError('Generation failed')
                checkpoint(s['cell_id'])
                print(s['cell_id'], 'generated exact family', flush=True)
                continue
            h = hardware(cell)
            n = s['N']
            model = SOURCE/s['model']
            query = SOURCE/s['query'] if s.get('query') else SOURCE/f'generated/n{n}/parse-all.q' if s['phase']=='load-and-parse' else None
            meta = manifest['models'][n-1]
            if sha(model) != meta['files']['model.xml']['sha256'] or (query and sha(query) != meta['files'][str(query.relative_to(model.parent))]['sha256']):
                raise RuntimeError('Model/query hash changed before launch')
            args = [driver.winpath(model) if arg == s['model'] else
                    driver.winpath(query) if query and arg in (s.get('query'), f'generated/n{n}/parse-all.q') else
                    driver.winpath(cell/'trace') if arg.startswith('<run-directory>') else arg for arg in s['arguments']]
            rec.update(status='running', command=[driver.winpath(exe)]+args, hardware_description=h)
            persist()
            start = time.monotonic()
            try:
                raw = driver.monitor_run(cell, 'tool', exe, args, 60, compile_only=s['phase']=='compile')
            finally:
                charged = time.monotonic()-start
                used += charged
                settings['used_seconds'] = used
                persist()
            stdout = (cell/'tool.stdout.txt').read_text(errors='replace')
            stderr = (cell/'tool.stderr.txt').read_text(errors='replace')
            status, explicit = classify(raw, stdout, s['phase'])
            rec.update(raw)
            rec.update(status=status, reason=None, budget_charged_seconds=charged,
                       property_verdict=explicit if s['phase']=='model-checking' else None,
                       load_verdict=explicit if s['phase']=='load-and-parse' else None,
                       hardware_description=h, model_path=str(model.relative_to(ROOT)), model_hash=sha(model),
                       query_path=str(query.relative_to(ROOT)) if query else None, query_hash=sha(query) if query else None,
                       generator_hash=meta['generator_hash'], source_hash=meta['source_hash'],
                       parameter_set=json.loads((model.parent/'parameters.json').read_text()),
                       instance_vector=json.loads((model.parent/'instance-vector.json').read_text()),
                       operating_environment={'driver': platform.platform(), 'target': 'native Windows via WSL'},
                       environment_overrides={'UPPAAL_COMPILE_ONLY': '1'} if s['phase']=='compile' else {},
                       inherited_UPPAAL_variables_removed=True,
                       evidence_kind='direct_model_checking' if s['phase']=='model-checking' else 'compile_or_load_only',
                       states_explored='not_available',
                       monitor_reference=str((cell/'tool.monitor.json').relative_to(HERE)),
                       memory_samples_reference=str((cell/'tool.memory.csv').relative_to(HERE)),
                       result_per_query=[{'formula':s['formula'],'verdict':explicit}] if s['phase']=='model-checking' and explicit else [])
            rec['tool_resource_summary'] = [line for line in (stdout+'\n'+stderr).splitlines() if re.search(r'states|memory|resident|elapsed|CPU', line, re.I)][:30]
            for stream in ('stdout', 'stderr'):
                rec[stream] = driver.store_stream(cell/f'tool.{stream}.txt')
            rec['trace'] = {'requested': s['phase']=='model-checking', 'files': [driver.store_stream(p) for p in sorted(cell.glob('trace*')) if p.is_file()]}
            persist()
            print(s['cell_id'], status, explicit, f'{raw["runtime_seconds"]:.3f}s', f'budget={used:.1f}', flush=True)
            checkpoint(s['cell_id'])
            if status not in ('success', 'timeout', 'memory_limit') or not raw['process_reaped'] or not raw['samples']:
                raise RuntimeError('Tool/monitor/verdict failure; no automatic retry')
            if s['phase'] in ('compile', 'load-and-parse') and (status != 'success' or (s['phase']=='load-and-parse' and explicit!='satisfied')):
                blocked.add(key)
        settings['status'] = 'completed'
    except BaseException as exc:
        settings.update(status='stopped', error=type(exc).__name__+': '+str(exc))
        for rec in records:
            if rec['status']=='running':
                rec.update(status='monitor_error', reason=str(exc), property_verdict=None)
            if rec['status']=='not_started' and rec.get('reason')=='pending':
                rec['reason']='campaign stopped: '+str(exc)
        persist()
        checkpoint('stopped campaign evidence')
        raise
    finally:
        persist()
    checkpoint('completed campaign')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['pins', 'controls', 'run'])
    parser.add_argument('--verifyta', type=Path, default=Path('/mnt/d/UPPAAL/app/bin/verifyta.exe'))
    args = parser.parse_args()
    if args.action=='pins':
        print(json.dumps({'audit': pins(), 'scheduled_cells': len(plan())}, indent=2))
    elif args.action=='controls':
        controls()
    else:
        campaign(args.verifyta.resolve())
