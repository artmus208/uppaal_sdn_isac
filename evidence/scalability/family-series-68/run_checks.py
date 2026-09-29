#!/usr/bin/env python3
"""Sequential Issue #68 diagnostics, with native Windows memory/time monitoring.

This is not the P4 resource series. No retries, limit escalation or baseline claims.
Stdlib only. PowerShell 5.1 / Windows verifyta is the supported measured platform.
"""
import argparse
import datetime
import gzip
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import time

import generate as g

POWERSHELL = Path('/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe')
MEMORY_BYTES = 2 * 1024 ** 3
SAMPLE_MS = 50
TOTAL_SECONDS = 1200
BEHAVIOR_SECONDS = 30
SETUP_SECONDS = 10
SEARCH = ['-q', '-s', '-u', '-o', '1', '--exploration', '0',
          '--state-representation', '1', '-S', '1', '-n', '0', '-r', '68']


def winpath(path):
    return str(path) if os.name == 'nt' else subprocess.check_output(
        ['wslpath', '-w', str(Path(path).resolve())], text=True).strip()


def write_json(path, data):
    path.write_bytes(g.encoded(data))


def powershell_command(config):
    return [str(POWERSHELL), '-NoProfile', '-NonInteractive', '-ExecutionPolicy',
            'Bypass', '-File', winpath(g.HERE / 'monitor.ps1'), '-ConfigPath', winpath(config)]


def invoke_monitor(config, timeout):
    """The PS monitor owns/kills/reaps the Windows process and drains both pipes."""
    cmd = powershell_command(config)
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                timeout=timeout + 20)
    except subprocess.TimeoutExpired as exc:
        # A hung monitor must not silently leave the child running in Windows.
        result_path = config.parent / (config.stem + '.monitor.json')
        child = (json.loads(result_path.read_text(encoding='utf-8-sig')).get('process_id')
                 if result_path.exists() else None)
        if child:
            cleanup = f'& "$env:SystemRoot\\System32\\taskkill.exe" /PID {int(child)} /T /F'
            subprocess.run([str(POWERSHELL), '-NoProfile', '-NonInteractive', '-Command', cleanup],
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
        raise RuntimeError('Native monitor watchdog failed; diagnostic campaign stopped') from exc
    config.with_suffix('.wrapper.stdout.txt').write_bytes(result.stdout)
    config.with_suffix('.wrapper.stderr.txt').write_bytes(result.stderr)
    if result.returncode != 0:
        # Preserve actual monitor output; callers may record its fail-closed result.
        result_file = config.parent / (config.stem + '.monitor.json')
        if not result_file.exists():
            raise RuntimeError(f'Native Windows monitor failed ({result.returncode}); see {config}')
    return cmd


def monitor_run(folder, name, executable, arguments, timeout, *, compile_only=False,
                memory_bytes=MEMORY_BYTES):
    config_path = folder / f'{name}.config.json'
    config = {'mode': 'run', 'executable': winpath(executable),
              'arguments': arguments, 'arguments_windows': subprocess.list2cmdline(arguments),
              'cwd': winpath(executable.parent), 'compile_only': compile_only,
              'timeout_seconds': timeout, 'memory_limit_bytes': memory_bytes,
              'sample_interval_ms': SAMPLE_MS,
              'stdout': winpath(folder / f'{name}.stdout.txt'),
              'stderr': winpath(folder / f'{name}.stderr.txt'),
              'samples': winpath(folder / f'{name}.memory.csv'),
              'result': winpath(folder / f'{name}.monitor.json')}
    write_json(config_path, config)
    wrapper = invoke_monitor(config_path, timeout)
    record = json.loads((folder / f'{name}.monitor.json').read_text(encoding='utf-8-sig'))
    record['wrapper_command'] = wrapper
    return record


def probe(folder):
    path = folder / 'hardware.config.json'
    write_json(path, {'mode': 'probe', 'result': winpath(folder / 'hardware.json')})
    result = subprocess.run(powershell_command(path), capture_output=True, timeout=15)
    (folder / 'hardware.stdout.txt').write_bytes(result.stdout)
    (folder / 'hardware.stderr.txt').write_bytes(result.stderr)
    if result.returncode != 0:
        raise RuntimeError('Native Windows accounting unavailable: no verifier launched')
    return json.loads((folder / 'hardware.json').read_text(encoding='utf-8-sig'))


def verdict(stdout):
    matches = re.findall(r'-- Formula is (NOT satisfied|satisfied)\.', stdout)
    return ('satisfied' if matches[0] == 'satisfied' else 'violated') if len(matches) == 1 else None


def store_stream(path):
    data = path.read_bytes()
    digest = g.sha(data)
    if len(data) > 100_000:
        # Retain exact bytes losslessly; deterministic gzip removes time variance.
        packed = path.with_suffix(path.suffix + '.gz')
        packed.write_bytes(gzip.compress(data, mtime=0))
        path.unlink()
        path = packed
    return {'reference': str(path.relative_to(g.HERE)), 'sha256': digest,
            'storage_sha256': g.sha(path.read_bytes()), 'encoding': 'gzip' if path.suffix == '.gz' else 'raw'}


def plan():
    items = []
    for n in (1, 2, 3, 4):
        items.extend([(n, 'compile', SETUP_SECONDS), (n, 'parse-load', SETUP_SECONDS)])
    for n in (1, 2, 3, 4):
        ids = ['shared-capacity'] + [f'u{i}-service' for i in range(n)]
        ids += ['joint-backlog', 'u0-queue-safety', 'u0-queue-full']
        items.extend((n, query, BEHAVIOR_SECONDS) for query in ids)
    return items


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--verifyta', type=Path, required=True)
    ap.add_argument('--run-id', required=True)
    a = ap.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]*', a.run_id):
        ap.error('simple unique run-id required')
    exe = a.verifyta.resolve()
    if exe.suffix.lower() != '.exe' or not exe.is_file() or not POWERSHELL.is_file():
        ap.error('this measured runner requires Windows verifyta and native PowerShell via WSL')
    out = g.HERE / 'checks' / a.run_id
    if out.exists():
        ap.error('run directory exists; evidence is immutable')
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=g.ROOT, text=True).strip()
    dirty = subprocess.check_output(['git', 'status', '--porcelain', '--untracked-files=normal'],
                                    cwd=g.ROOT, text=True).strip()
    if dirty:
        ap.error('commit and publish candidate before diagnostics; working tree must be clean')
    pins = g.inputs()
    for n in (1, 2, 3, 4):
        for name, data in g.artifacts(n, pins).items():
            if (g.HERE / 'generated' / f'n{n}' / name).read_bytes() != data:
                ap.error(f'committed generation mismatch N={n}: {name}')
    out.mkdir(parents=True)
    hardware = probe(out)
    if hardware['available_physical_ram_bytes'] < MEMORY_BYTES:
        raise SystemExit('Available native Windows RAM below 2GiB; no verifier launched')
    records = []
    version = None
    used = 0.0
    planned = plan()
    settings = {'campaign_id': a.run_id, 'kind': 'P2 bounded diagnostics, not P4',
                'source_commit': commit, 'memory_limit_bytes': MEMORY_BYTES,
                'sample_interval_ms': SAMPLE_MS, 'total_verifier_budget_seconds': TOTAL_SECONDS,
                'setup_timeout_seconds': SETUP_SECONDS, 'behavior_timeout_seconds': BEHAVIOR_SECONDS,
                'planned_upper_bound_seconds': 2 * SETUP_SECONDS + sum(x[2] for x in planned),
                'search_arguments': SEARCH, 'trace_arguments': ['-t', '0', '-f', '<unique-prefix>'],
                'execution': 'sequential fresh native Windows process, no retries',
                'plan': [{'N': n, 'query_id': q, 'timeout_seconds': t} for n, q, t in planned],
                'monitor_hash': g.sha((g.HERE / 'monitor.ps1').read_bytes()),
                'runner_hash': g.sha(Path(__file__).read_bytes()),
                'stop_condition': 'per-run timeout/memory threshold; stop campaign if monitor fails, tool metadata unavailable, or total budget exhausted',
                'budget_used_seconds': used}
    write_json(out / 'settings.json', settings)
    loaded = {}

    def run(name, args, timeout, *, n=None, query=None, query_id=None, kind='tool_metadata', compile_only=False):
        nonlocal used
        if used + timeout + 5 > TOTAL_SECONDS:
            raise RuntimeError('Total verifier budget exhausted; no retries or escalation')
        raw = monitor_run(out, name, exe, args, timeout, compile_only=compile_only)
        used += raw['runtime_seconds']
        so = out / f'{name}.stdout.txt'
        se = out / f'{name}.stderr.txt'
        stdout = so.read_text(errors='replace')
        stderr = se.read_text(errors='replace')
        model = g.HERE / 'generated' / f'n{n}' / 'model.xml' if n else None
        explicit = verdict(stdout) if kind in ('model_load', 'behavior') else None
        record = {**raw, 'run_id': a.run_id + '-' + name, 'evidence_kind':
                  'direct_model_checking' if kind in ('model_load', 'behavior') else 'static_validation',
                  'run_kind': kind, 'N': n, 'query_id': query_id,
                  'source_commit': commit, 'working_tree_before_campaign': 'clean',
                  'source_hash': pins['source_hash'], 'generator_hash': json.loads((g.HERE / 'generated/n1/metadata.json').read_text())['generator_hash'],
                  'model_path': str(model.relative_to(g.ROOT)) if model else None,
                  'model_hash': g.sha(model.read_bytes()) if model else None,
                  'query_path': str(query.relative_to(g.ROOT)) if query else None,
                  'query_hash': g.sha(query.read_bytes()) if query else None,
                  'tool_version': version,
                  'operating_environment': {'driver': platform.platform(), 'target': 'native Windows process via WSL interop'},
                  'hardware_description': hardware, 'status': raw['status'], 'execution_status': raw['status'],
                  'property_verdict': explicit if raw['status'] == 'success' else None,
                  'raw_stdout_verdict': explicit,
                  'parameter_set': json.loads((model.parent / 'parameters.json').read_text()) if model else None,
                  'instance_vector': json.loads((model.parent / 'instance-vector.json').read_text()) if model else None,
                  'states_explored': 'not_available', 'acceptance_status': 'not_reviewed',
                  'claim_scope': 'initial-state load and query-file parsing only' if kind == 'model_load' else
                                 'candidate N-specific formula only; no accepted baseline or transferred P3 result' if kind == 'behavior' else
                                 'compile-only model acceptance; external queries are not checked' if compile_only else 'tool metadata',
                  'memory_samples_reference': str((out / f'{name}.memory.csv').relative_to(g.HERE)),
                  'monitor_reference': str((out / f'{name}.monitor.json').relative_to(g.HERE))}
        if query and explicit and raw['status'] == 'success':
            record['result_per_query'] = [{'query_id': query_id, 'formula':
                 'E<> true' if kind == 'model_load' else query.read_text().strip(), 'verdict': explicit}]
        else:
            record['result_per_query'] = []
        for stream, path in [('stdout', so), ('stderr', se)]:
            saved = store_stream(path)
            record[f'{stream}_reference'] = saved['reference']
            record[f'{stream}_hash'] = saved['sha256']
            record[f'{stream}_storage_hash'] = saved['storage_sha256']
            record[f'{stream}_encoding'] = saved['encoding']
        traces = sorted(out.glob(name + '-trace*'))
        record['trace'] = {'requested': kind == 'behavior', 'availability': 'present' if traces else 'not_produced' if kind == 'behavior' else 'not_requested',
                           'files': [{'reference': str(p.relative_to(g.HERE)), 'sha256': g.sha(p.read_bytes())} for p in traces]}
        record['evidence_availability'] = {'stdout': True, 'stderr': True, 'memory_samples': raw['samples'] > 0,
                                            'trace': record['trace']['availability'], 'states_explored': 'not_available'}
        # Preserve summary lines without guessing names/units across UPPAAL versions.
        states = re.search(r'(?i)states explored\s*[:=]\s*([0-9]+)', stdout + '\n' + stderr)
        if states:
            record['states_explored'] = int(states[1])
            record['evidence_availability']['states_explored'] = True
        record['tool_resource_summary'] = [line for line in (stdout + '\n' + stderr).splitlines()
                                            if re.search(r'states|memory|resident|elapsed|CPU', line, re.I)][:30]
        records.append(record)
        write_json(out / 'runs.json', records)
        settings['budget_used_seconds'] = used
        write_json(out / 'settings.json', settings)
        print(f'{name}: {record["status"]}; verdict={record["property_verdict"]}; {raw["runtime_seconds"]:.3f}s; '
              f'peak private={raw["peak_private_bytes"]}; peak WS={raw["peak_reported_working_set_bytes"]}', flush=True)
        if raw['status'] == 'monitor_error':
            raise RuntimeError('Native monitor failed: campaign stopped, no property claim')
        return record, stdout, stderr

    rec, stdout, stderr = run('version', ['--version'], SETUP_SECONDS)
    if rec['status'] != 'success' or not stdout.strip():
        raise SystemExit('Tool version unavailable; campaign stopped')
    version = next((line.strip() for line in stdout.splitlines() if 'UPPAAL' in line), None)
    if not version:
        raise SystemExit('No actual UPPAAL version in stdout')
    rec['tool_version'] = version
    write_json(out / 'runs.json', records)
    rec, help_text, stderr = run('help', ['--help'], SETUP_SECONDS)
    if rec['status'] != 'success' or not all(s in help_text for s in ('--query-index', 'Depth first', '--state-representation', '--seed')):
        raise SystemExit('Actual tool help does not support the fixed diagnostic command')
    for n, query_id, timeout in planned:
        folder = g.HERE / 'generated' / f'n{n}'
        model = folder / 'model.xml'
        name = f'n{n}-{query_id}'
        if query_id == 'compile':
            rec, stdout, stderr = run(name, [winpath(model), winpath(folder / 'load.q')], timeout,
                n=n, query=folder / 'load.q', query_id='compile-only', kind='compile', compile_only=True)
            loaded[n] = rec['status'] == 'success' and 'Verifying formula' not in stdout
        elif query_id == 'parse-load':
            if not loaded[n]:
                settings.setdefault('skipped', []).append({'N': n, 'query_id': query_id, 'reason': 'compile did not succeed'})
                write_json(out / 'settings.json', settings)
                continue
            query = out / f'n{n}-parse-all.q'
            p4 = json.loads((folder / 'p4-queries.json').read_text())
            query.write_text('E<> true\n' + (folder / 'queries.q').read_text() + '\n' +
                             '\n'.join(row['query'] for row in p4) + '\n')
            rec, stdout, stderr = run(name, SEARCH + ['--query-index', '0', winpath(model), winpath(query)],
                timeout, n=n, query=query, query_id='initial-load', kind='model_load')
            loaded[n] = rec['status'] == 'success' and rec['property_verdict'] == 'satisfied'
        else:
            if not loaded.get(n):
                settings.setdefault('skipped', []).append({'N': n, 'query_id': query_id, 'reason': 'model compile/load not successful'})
                write_json(out / 'settings.json', settings)
                continue
            query = folder / 'p4' / f'{query_id}.q'
            run(name, SEARCH + ['-t', '0', '-f', winpath(out / (name + '-trace')), winpath(model), winpath(query)],
                timeout, n=n, query=query, query_id=query_id, kind='behavior')
    settings['completed_at_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    settings['all_four_compile_and_load'] = all(loaded.get(n) for n in (1, 2, 3, 4))
    settings['budget_used_seconds'] = used
    write_json(out / 'settings.json', settings)
    if not settings['all_four_compile_and_load']:
        raise SystemExit('Model loading acceptance criterion has a blocker; see raw outcomes')
    print('Diagnostics complete; open verdicts stay open. Gate 1 and P4 acceptance not asserted.')


if __name__ == '__main__':
    main()
