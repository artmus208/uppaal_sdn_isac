"""Summarize actual 30-minute native results without changing historical runs."""
import json
from pathlib import Path
import native_campaign as base

HERE, vm = base.HERE, base.vm
ROOT = HERE/'native-30min'

def summarize():
    records = []
    for queue in sorted(ROOT.glob('observer-erasure-*')):
        paths = list(queue.glob('attempts/*/result.json'))
        if not paths:
            continue
        if len(paths) != 1:
            raise ValueError('Multiple attempts in reserved run')
        path = paths[0]
        r = vm.read(path)
        cfg = vm.read(queue/'queue.json')
        reservation = vm.read(queue/'reservation.json')
        vm.verify_inputs(queue, cfg)
        for name, expected in vm.read(path.parent/'hashes.json').items():
            if vm.digest(path.parent/name) != expected:
                raise ValueError('Changed evidence: '+str(path.parent/name))
        if r['model_hash'] != cfg['model_hash'] or r['query_hash'] != cfg['tasks'][0]['query_hash']:
            raise ValueError('Result hash mismatch')
        if r['status'] != 'success' and r['verdict'] is not None:
            raise ValueError('Inconclusive attempt has verdict')
        records.append({
            'run_id':queue.name, 'attempt_id':r['run_id'],
            'status':r['status'], 'verdict':r['verdict'],
            'model_hash':r['model_hash'], 'query_hash':r['query_hash'],
            'tool_version':r['tool_version'], 'execution_commit':reservation['execution_commit'],
            'timeout_seconds':r['timeout_seconds'], 'memory_stop_bytes':r['memory_stop_bytes'],
            'elapsed_seconds':r['elapsed_seconds'], 'peak_rss_bytes':r['peak_rss_bytes'],
            'cpu_seconds':r['cpu_seconds'], 'manager_error':r.get('manager_error'),
            'result_path':path.relative_to(HERE).as_posix(), 'result_hash':vm.digest(path),
            'command':r['command'], 'trace_paths':r['trace_paths']})
    if not records:
        raise ValueError('No completed results')
    for query in base.QUERIES:
        if not any('-'+query+'-' in r['run_id'] for r in records):
            raise ValueError('Missing completed query '+query)
    vm.save(ROOT/'results.json',records)
    text = '# User-authorized 30-minute experiment\n\n'
    text += 'Native version: '+records[0]['tool_version'].splitlines()[0]+'.\n'
    text += 'Exact diagnostic XML and accepted queries unchanged. Sequential BFS runs,\n'
    text += '1800-second timeout per attempt, 2048-MiB sampled memory stop.\n\n'
    text += '| Run | Status | Verdict | Seconds | Peak MiB |\n|---|---|---|---:|---:|\n'
    for r in records:
        text += f"| {r['run_id']} | {r['status']} | {r['verdict'] or 'none'} | {r['elapsed_seconds']:.3f} | {r['peak_rss_bytes']/1024**2:.2f} |\n"
    text += '\nResults.json supplies exact result bindings, commands, execution commits,\n'
    text += 'native versions and trace inventories. Raw logs, telemetry and version probes\n'
    text += 'are preserved per run. A memory stop can occur before the time limit; it\n'
    text += 'does not prove or refute a property. Direct scope is the 29-process diagnostic\n'
    text += 'composition; full-model transfer needs independent proof acceptance.\n'
    errors = [r for r in records if r['manager_error']]
    for r in errors:
        text += '\nManager failure for '+r['run_id']+':\n\n```text\n'+r['manager_error']+'\n```\n'
    if not errors:
        text += '\nThe previous status-file write error did not recur; no repair was activated.\n'
    (ROOT/'summary.md').write_text(text,encoding='utf-8',newline='\n')
    return records

if __name__ == '__main__':
    summarize()
