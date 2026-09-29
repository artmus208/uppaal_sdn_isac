#!/usr/bin/env python3
"""Audit exact artifacts and recorded outcomes; does not execute model checking."""
import argparse
import csv
import functools
import gzip
import io
import json
import os
from pathlib import Path
import subprocess
import generate as g
from run_checks import verdict


def require(value, message):
    if not value:
        raise ValueError(message)


@functools.lru_cache(maxsize=None)
def committed(commit, path):
    return subprocess.check_output(['git', 'show', commit+':'+path], cwd=g.ROOT)


def package_files():
    for root, directories, files in os.walk(g.HERE):
        directories[:] = sorted(d for d in directories if d not in ('.venv', 'handoff', '__pycache__'))
        for name in sorted(files):
            path = Path(root)/name
            if name != 'artifacts-sha256.json':
                yield path


def audit():
    pins = g.inputs()
    for n in g.SIZES:
        for name, data in g.artifacts(n, pins).items():
            require((g.HERE/'generated'/f'n{n}'/name).read_bytes() == data,
                    f'generated artifact mismatch n{n}/{name}')
    run_count = 0
    for index in sorted((g.HERE/'checks').glob('diagnostic-*/runs.json')):
        records = json.loads(index.read_text())
        settings = json.loads(index.with_name('settings.json').read_text())
        source = settings['source_commit']
        scope = str(g.HERE.relative_to(g.ROOT))
        for name, key in (('run_checks.py', 'runner_hash'), ('monitor.ps1', 'monitor_hash')):
            require(g.sha(committed(source, scope+'/'+name)) == settings[key], 'committed '+key)
        actual_version = None
        total = 0
        for record in records:
            run_count += 1
            label = record['run_id']
            require(record['source_commit'] == source, label + ': campaign source')
            raw_monitor = json.loads((g.HERE/record['monitor_reference']).read_text(encoding='utf-8-sig'))
            for key, value in raw_monitor.items():
                require(record[key] == value, label + ': differs from raw monitor: '+key)
            require(record['execution_status'] == raw_monitor['status'], label + ': execution status')
            total += record['runtime_seconds']
            require(record['timeout_seconds'] <= 60, label + ': time setting')
            require(record['memory_limit_bytes'] <= 2147483648, label + ': memory setting')
            require(record['process_reaped'] and record['samples'] > 0, label + ': monitoring/reaping')
            require(record['maximum_sample_gap_seconds'] > 0, label + ': sample timing')
            require(record['working_tree_before_campaign'] == 'clean', label + ': source cleanliness')
            require(record['source_hash'] == pins['source_hash'], label + ': pinned input hash')
            outputs = {}
            for stream in ('stdout', 'stderr'):
                stored = (g.HERE/record[stream+'_reference']).read_bytes()
                raw = gzip.decompress(stored) if record[stream+'_encoding'] == 'gzip' else stored
                require(g.sha(stored) == record[stream+'_storage_hash'], label + ': storage hash')
                require(g.sha(raw) == record[stream+'_hash'], label + ': raw hash')
                outputs[stream] = raw.decode(errors='replace')
            if label.endswith('-version'):
                actual_version = next(line.strip() for line in outputs['stdout'].splitlines() if 'UPPAAL' in line)
            require(actual_version and record['tool_version'] == actual_version, label + ': actual version')
            model = record['model_path']
            query = record['query_path']
            for kind, path in (('model', model), ('query', query)):
                if path:
                    require(g.sha((g.ROOT/path).read_bytes()) == record[kind+'_hash'], label + ': ' + kind)
            if model:
                require(g.sha(committed(source, model)) == record['model_hash'], label + ': committed model')
                meta = json.loads((g.ROOT/model).with_name('metadata.json').read_text())
                for name, digest in meta['generator_source_files'].items():
                    require(g.sha(committed(source, scope+'/'+name)) == digest, label + ': committed generator source')
                require(record['generator_hash'] == meta['generator_hash'], label + ': generator hash')
                require(record['parameter_set'] == json.loads((g.ROOT/model).with_name('parameters.json').read_text()), label + ': parameters')
                require(record['instance_vector'] == json.loads((g.ROOT/model).with_name('instance-vector.json').read_text()), label + ': vector')
                if record['run_kind'] == 'model_load':
                    folder = str(Path(model).parent)
                    legacy = committed(source, folder+'/queries.q').decode()
                    compact = json.loads(committed(source, folder+'/p4-queries.json'))
                    expected_query = ('E<> true\n'+legacy+'\n'+'\n'.join(row['query'] for row in compact)+'\n').encode()
                else:
                    expected_query = committed(source, query)
                require(g.sha(expected_query) == record['query_hash'], label + ': committed/derived query')
            raw_verdict = verdict(outputs['stdout']) if record['run_kind'] in ('behavior', 'model_load') else None
            expected = raw_verdict if record['status'] == 'success' else None
            require(record['property_verdict'] == expected, label + ': unsupported verdict')
            if record['property_verdict']:
                formula = 'E<> true' if record['run_kind'] == 'model_load' else (g.ROOT/query).read_text().strip()
                require(record['result_per_query'] == [{'query_id': record['query_id'], 'formula': formula,
                                                        'verdict': expected}], label + ': mismatched explicit result')
            else:
                require(not record['result_per_query'], label + ': claim without verdict')
            for trace in record['trace']['files']:
                require(g.sha((g.HERE/trace['reference']).read_bytes()) == trace['sha256'], label + ': trace hash')
            samples = list(csv.DictReader(io.StringIO((g.HERE/record['memory_samples_reference']).read_text())))
            require(len(samples) == record['samples'], label + ': sample count')
            require(max(int(x['private_bytes']) for x in samples) == record['peak_private_bytes'], label + ': private peak')
            require(max(int(x['peak_working_set_bytes']) for x in samples) == record['peak_reported_working_set_bytes'], label + ': working-set peak')
            if record['status'] == 'memory_limit':
                require(max(record['peak_private_bytes'], record['peak_reported_working_set_bytes']) >= record['memory_limit_bytes'], label + ': unmeasured memory stop')
        require(total <= settings['total_verifier_budget_seconds'] <= 1200, 'diagnostic campaign budget')
        require(abs(total-settings['budget_used_seconds']) < 1e-6, 'recorded total differs')
    return run_count


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write-index', action='store_true')
    args = parser.parse_args()
    count = audit()
    index = g.HERE/'artifacts-sha256.json'
    current = {str(p.relative_to(g.HERE)): g.sha(p.read_bytes()) for p in package_files()}
    if args.write_index:
        index.write_bytes(g.encoded(current))
    else:
        require(json.loads(index.read_text()) == current, 'package artifact index mismatch')
    print(f'{len(current)} exact artifact hashes; {count} recorded tool runs audited; no model checking executed')


if __name__ == '__main__':
    main()
