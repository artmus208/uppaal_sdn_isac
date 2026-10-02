#!/usr/bin/env python3
"""Read preserved N=1 artifacts; never launches verifyta or changes source evidence.

--output writes derived JSON. --check recomputes and compares an existing JSON.
The XTR audit decodes discrete vectors against stored compiled layouts, not timed
trace replay or a new verification verdict. All source run statuses are retained.
"""
import argparse
import collections
import gzip
import hashlib
import json
from pathlib import Path
import re

SOURCES = (
    (68, 'evidence/scalability/family-series-68', 'checks/diagnostic-001/runs.json'),
    (70, 'evidence/scalability/service-reachability-20260929', 'runs/service-002/runs.json'),
    (76, 'evidence/scalability/runs/uav-family-p4-20260929', 'campaign-002/runs.json'),
)
KEEP = '''run_id status execution_status source_commit candidate_commit baseline_id baseline_manifest_sha256 source_hash generator_hash model_hash query_hash model_path query_path query_id formula N entity repeat phase run_kind evidence_kind command wrapper_command cwd timeout_seconds memory_limit_bytes memory_stop_bytes sample_interval_ms maximum_sample_gap_seconds samples enforcement memory_measure operating_environment hardware_description runtime_seconds cpu_seconds peak_private_bytes peak_working_set_bytes peak_reported_working_set_bytes states_explored tool_resource_summary property_verdict raw_stdout_verdict result_per_query tool_version started_at_utc finished_at_utc process_reaped kill_tree_requested exit_code error budget_charged_seconds parallelism'''.split()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def data(path):
    raw = path.read_bytes()
    return gzip.decompress(raw) if path.suffix == '.gz' else raw


def artifact(root, base, info):
    path = base / info['reference']
    raw = (root / path).read_bytes()
    content = gzip.decompress(raw) if info.get('encoding') == 'gzip' or path.suffix == '.gz' else raw
    result = {'path': str(path), 'storage_sha256': sha(raw), 'content_sha256': sha(content), 'bytes': len(raw)}
    for key, actual in [('sha256', result['content_sha256']), ('storage_sha256', result['storage_sha256'])]:
        if info.get(key) is not None and info[key] != actual:
            raise ValueError(f'{path}: {key} mismatch')
    return result, content


def stream_info(row, kind):
    if isinstance(row.get(kind), dict):
        return row[kind]
    return {
        'reference': row[f'{kind}_reference'],
        'encoding': row.get(f'{kind}_encoding', 'raw'),
        'sha256': row.get(f'{kind}_sha256', row.get(f'{kind}_hash')),
        'storage_sha256': row.get(f'{kind}_storage_sha256', row.get(f'{kind}_storage_hash')),
    }


def layout(content):
    text = content.decode().replace('\r', '')
    variables = {}
    for ln in text.splitlines():
        parts = ln.split(':')
        if len(parts) == 7 and parts[0].isdigit() and parts[1] == 'var':
            variables[int(parts[5])] = {'name': parts[6], 'min': int(parts[2]), 'max': int(parts[3]), 'init': int(parts[4])}
    assert sorted(variables) == list(range(255)), 'Unexpected N=1 discrete layout'
    edges = next(s for s in text.split('\n\n') if s.startswith('edges\n'))
    edge_lines = [line for line in edges.splitlines() if re.fullmatch(r'\d+(?::\d+){5}', line)]
    shared = collections.Counter(':'.join(line.split(':')[:3]) for line in edge_lines if line.startswith('21:'))
    assert shared['21:1176:1179'] == 2592
    return variables, {'discrete_variables': len(variables), 'compiled_edges': len(edge_lines), 'shared_load_edge_groups': dict(shared)}


def trace_audit(content, variables):
    lines = content.decode().splitlines()
    vectors = [list(map(int, ln.split())) for ln in lines if re.fullmatch(r'[-\d ]+', ln) and len(ln.split()) == len(variables)]
    locations = [ln for ln in lines if re.fullmatch(r'[-\d ]+', ln) and len(ln.split()) == 50]
    assert vectors and len(vectors) == len(locations), 'Mismatch of location/discrete-vector counts'
    assert vectors[0] == [variables[i]['init'] for i in range(len(variables))], 'Initial vector mismatch'
    for row in vectors:
        assert all(variables[i]['min'] <= value <= variables[i]['max'] for i, value in enumerate(row)), 'Out-of-domain discrete value'
    selected = {i: spec for i, spec in variables.items() if i in (0, 1, 29, 30, 38, 71, 72, 128, 132, 133, 137, 143, 144, 145) or spec['name'].startswith('shared_load.')}
    audit = {'discrete_vectors': len(vectors), 'matching_location_vectors': len(locations), 'initial_vector_matches_layout': True, 'all_discrete_values_in_declared_domains': True, 'variables': {spec['name']: {'index': i, 'values': sorted({row[i] for row in vectors}), 'final': vectors[-1][i]} for i, spec in selected.items()}}
    audit['service_grant_present'] = any(row[1] for row in vectors)
    # Constants are frozen in this model: SCH_COMM=1, SCH_JOINT=3.
    audit['positive_queue_and_service_mode_present'] = any(row[71] > 0 and row[137] in (1, 3) for row in vectors)
    return audit


def extract(root):
    result = {'schema_version': 1, 'kind': 'historical_read_only_audit_no_verifier_execution', 'selection': 'All rows whose N is integer 1 in three scientific run indexes; generation/metadata failures are campaign context, not N=1 scientific attempts.', 'sources': [], 'runs': [], 'trace_decodings': [], 'metadata_gaps': []}
    compiler_path = 'evidence/scalability/family-series-68/checks/diagnostic-001/n1-compile.stdout.txt.gz'
    compiler = data(root / compiler_path)
    variables, structure = layout(compiler)
    result['trace_layout'] = {'path': compiler_path, 'content_sha256': sha(compiler), **structure}
    result['trace_decode_method'] = 'Decode 255-integer discrete state vectors using exact compiled layout var nr; assert initial values and all declared domains, and count matching 50-process location vectors. No DBM interpretation or timed trace replay.'
    unique_traces = {}
    for issue, directory, index in SOURCES:
        base = Path(directory)
        index_path = base / index
        raw_index = (root / index_path).read_bytes()
        rows = json.loads(raw_index)
        result['sources'].append({'issue': issue, 'path': str(index_path), 'sha256': sha(raw_index), 'n1_rows': sum(row.get('N') == 1 for row in rows)})
        for position, row in enumerate(rows):
            if row.get('N') != 1:
                continue
            entry = {k: row[k] for k in KEEP if k in row}
            entry['source_issue'] = issue
            entry['source_record'] = {'path': str(index_path), 'array_index_zero_based': position, 'canonical_record_sha256': sha(json.dumps(row, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode())}
            entry['parameter_and_instance_provenance'] = {'parameters': 'evidence/scalability/family-series-68/generated/n1/parameters.json', 'instance_vector': 'evidence/scalability/family-series-68/generated/n1/instance-vector.json', 'full_embedded_values': 'source_record.parameter_set and source_record.instance_vector'}
            entry['query_text'] = (root / row['query_path']).read_text() if row.get('query_path') else None
            for key in ('model', 'query'):
                if row.get(key + '_path') and row.get(key + '_hash'):
                    assert sha((root / row[key + '_path']).read_bytes()) == row[key + '_hash'], f'{row["run_id"]}: {key} mismatch'
            stdout, stdout_raw = artifact(root, base, stream_info(row, 'stdout'))
            stderr, stderr_raw = artifact(root, base, stream_info(row, 'stderr'))
            entry['stdout'] = stdout
            entry['stderr'] = stderr
            entry['stdout_text'] = stdout_raw.decode(errors='replace') if len(stdout_raw) < 4096 else 'see artifact (compiled layout)'
            entry['stderr_text'] = stderr_raw.decode(errors='replace')
            for kind in ('monitor_reference', 'memory_samples_reference'):
                path = base / row[kind]
                entry[kind] = str(path)
                entry[kind.replace('_reference', '_sha256')] = sha((root / path).read_bytes())
            entry['native_peak_bytes'] = max(row.get(k, 0) for k in ('peak_private_bytes', 'peak_working_set_bytes', 'peak_reported_working_set_bytes'))
            entry['trace'] = {'requested': row['trace']['requested'], 'availability': 'present' if row['trace']['files'] else ('not_produced' if row['trace']['requested'] else 'not_requested'), 'files': []}
            for info in row['trace']['files']:
                trace, trace_content = artifact(root, base, info)
                entry['trace']['files'].append(trace)
                digest = sha(trace_content)
                if digest not in unique_traces:
                    unique_traces[digest] = {'sha256': digest, 'paths': [], 'run_ids': [], **trace_audit(trace_content, variables)}
                unique_traces[digest]['paths'].append(trace['path'])
                unique_traces[digest]['run_ids'].append(row['run_id'])
            text = stdout_raw.decode(errors='replace')
            for key, label in [('states_explored', 'States explored'), ('states_stored', 'States stored')]:
                match = re.search(re.escape(label) + r'\s*:\s*(\d+) states', text)
                entry[key + '_from_raw_stdout'] = int(match[1]) if match else 'not_available'
                if key == 'states_explored' and match and row.get(key) == 'not_available':
                    result['metadata_gaps'].append({'run_id': row['run_id'], 'field': key, 'recorded': 'not_available', 'raw_stdout_value': int(match[1]), 'raw_stdout': stdout['path']})
            if row.get('phase') == 'compile' or row.get('run_kind') == 'compile':
                assert sha(stdout_raw) == sha(compiler), 'Compiled N=1 layouts differ'
            result['runs'].append(entry)
    result['trace_decodings'] = list(unique_traces.values())
    service = [r for r in result['runs'] if r['run_id'].endswith('n1-u0-service')]
    result['summary'] = {'n1_rows': len(result['runs']), 'service_attempts': len(service), 'service_status_counts': dict(collections.Counter(r['status'] for r in service)), 'service_model_hashes': sorted({r['model_hash'] for r in service}), 'service_query_hashes': sorted({r['query_hash'] for r in service}), 'unique_saved_n1_traces': len(unique_traces), 'saved_trace_files': sum(len(r['trace']['files']) for r in result['runs']), 'service_verdicts': [r['property_verdict'] for r in service], 'service_trace_files': sum(len(r['trace']['files']) for r in service), 'raw_state_metadata_gap_count': len(result['metadata_gaps'])}
    assert result['summary']['n1_rows'] == 32 and len(service) == 5
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path.cwd())
    parser.add_argument('--output', type=Path, help='write derived JSON to this exact path')
    parser.add_argument('--check', type=Path, help='recompute and compare this existing derived JSON')
    args = parser.parse_args()
    result = extract(args.root)
    rendered = json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True) + '\n'
    if args.check:
        assert json.loads(args.check.read_text()) == result, 'Derived JSON differs from read-only recomputation'
    if args.output:
        args.output.write_text(rendered)
    print(json.dumps(result['summary'], ensure_ascii=False, sort_keys=True))


if __name__ == '__main__':
    main()
