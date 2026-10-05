"""Build a fail-closed summary from completed Issue #116 native attempts."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent

def read(path):
    return json.loads(path.read_text(encoding='utf-8'))

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def summarize():
    records = []
    for query in ('completion-safety', 'success'):
        queue = HERE/'native'/('observer-erasure-116-20261005-'+query+'-01')
        paths = list(queue.glob('attempts/*/result.json'))
        if len(paths) != 1:
            raise ValueError('Expected exactly one completed attempt: '+query)
        path = paths[0]
        result = read(path)
        reservation = read(queue/'reservation.json')
        config = read(queue/'queue.json')
        if result['model_hash'] != config['model_hash'] or result['query_hash'] != config['tasks'][0]['query_hash']:
            raise ValueError('Result inputs mismatch')
        for name, expected in read(path.parent/'hashes.json').items():
            if digest(path.parent/name) != expected:
                raise ValueError('Attempt evidence changed: '+name)
        if result['status'] != 'success' and result['verdict'] is not None:
            raise ValueError('Inconclusive attempt has a verdict')
        records.append({
            'run_id': queue.name, 'attempt_id': result['run_id'],
            'status': result['status'], 'verdict': result['verdict'],
            'query_name': query, 'model_hash': result['model_hash'],
            'query_hash': result['query_hash'], 'tool_version': result['tool_version'],
            'execution_commit': reservation['execution_commit'],
            'elapsed_seconds': result['elapsed_seconds'], 'peak_rss_bytes': result['peak_rss_bytes'],
            'cpu_seconds': result['cpu_seconds'], 'trace_paths': result['trace_paths'],
            'manager_error': result.get('manager_error'),
            'result_path': path.relative_to(HERE).as_posix(),
            'result_hash': digest(path), 'command': result['command'],
            'direct_scope': '29-process diagnostic XML; full-model transfer requires independent proof acceptance'})
    if records[0]['tool_version'] != records[1]['tool_version']:
        raise ValueError('Native version mismatch')
    (HERE/'native-results.json').write_text(json.dumps(records,indent=2)+'\n',encoding='utf-8')
    text = '# Native experiment for Issue #116\n\n'
    text += 'Native tool: '+records[0]['tool_version'].splitlines()[0]+'.\n'
    text += 'Both runs use the exact 29-process diagnostic XML, BFS options `-o 0 -t 0`,\n'
    text += '600-second time limit and 2048-MiB sampled memory stop. No retries.\n\n'
    text += '| Query | Status | Verdict | Seconds | Peak MiB |\n|---|---|---|---:|---:|\n'
    for r in records:
        text += f"| {r['query_name']} | {r['status']} | {r['verdict'] or 'none'} | {r['elapsed_seconds']:.3f} | {r['peak_rss_bytes']/1024**2:.2f} |\n"
    text += '\nExact run IDs, execution commits, full commands, model/query hashes, verbatim\n'
    text += 'native version, result paths/hashes and trace inventories are in native-results.json.\n'
    text += 'Raw stdout/stderr, resource telemetry and version probes are retained under native/.\n\n'
    for r in records:
        if r['manager_error']:
            text += f"Run `{r['run_id']}` ended on a manager error, not a native property verdict.\n"
            text += 'Windows denied atomic replacement of status.json (WinError 5). A concurrent\n'
            text += 'file reader or another transient sharing/access conflict can cause this; the\n'
            text += 'specific holder was not identified. The owned native process was terminated.\n'
            text += 'No retry is allowed by this campaign. Runner repair is outside Issue #116 scope.\n\n'
    text += 'Only a complete explicit native verdict settles a query. Timeout or a resource\n'
    text += 'stop does not establish either the property or its negation. This experiment\n'
    text += 'does not measure speedup relative to a controlled full-model run. Direct results\n'
    text += 'apply to the diagnostic model; independent scientific acceptance of the\n'
    text += 'observer-erasure proof is still required for transfer to the 51-process input.\n'
    (HERE/'native-summary.md').write_text(text,encoding='utf-8',newline='\n')

if __name__ == '__main__':
    summarize()
