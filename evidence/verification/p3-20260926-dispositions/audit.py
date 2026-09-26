"""Reconcile saved P3 evidence. Never invokes UPPAAL or changes earlier results."""
import argparse
from collections import Counter
import csv
import hashlib
import io
import json
from pathlib import Path
import re
import tarfile
import tempfile
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = ROOT / 'evidence/governance/20260906-baseline/gate1-20260923'
SOURCE = ROOT / 'evidence/verification/p3-20260923'
MODEL = '592678ed678ce8f70cf278f542e48bd2bb739969b53a962423d3e63f91e3e1e2'
sha = lambda b: hashlib.sha256(b).hexdigest()
read = lambda p: json.loads(p.read_text())


def relative(p):
    return str(p.relative_to(ROOT))


def validate_group(raw, metadata, run, results):
    for name in ['run.json', 'run.yaml', 'results.json']:
        assert (raw / name).read_bytes() == (metadata / name).read_bytes(), name
    hashes = {}
    for line in (raw / 'SHA256SUMS').read_text().splitlines():
        digest, name = line.split('  ', 1)
        assert Path(name).name == name and '\\' not in name
        assert sha((raw / name).read_bytes()) == digest, name
        hashes[name] = digest
    assert run['status'] == 'completed' and run['result_count'] == len(results)
    assert run['source_tree_clean_at_start'] is True
    assert run['source_hash'] == 'e3594a008ea0d04fb426465767860b9e74e8ec924b48743d1b8a4df721354b5a'
    assert run['generator_hash'] == '8ca2ed569467540c98b2f1446b4a428f6602326c4f2cb513c837b3f9b0942a60'
    assert run['parameter_set'] == read(BASE / 'parameters.json')
    assert run['instance_vector'] == read(BASE / 'instance-vector.json')
    assert (raw / 'version.stdout.txt').read_bytes().decode() == run['tool_version']
    assert run['baseline_manifest_sha256'] == sha((ROOT / 'manifests/baselines/reviewer-r1.yaml').read_bytes())
    assert run['frozen_query_set_hash'] == sha((BASE / 'selected-queries.q').read_bytes())
    for key in ['source_hash', 'generator_hash', 'parameter_set', 'instance_vector',
                'native_hardware', 'operating_environment', 'tool_version']:
        assert run[key], key
    for r in results:
        assert r['model_hash'] == run['model_hash'] == MODEL
        assert r['source_commit'] == run['source_commit']
        assert r['tool_version'] == run['tool_version']
        q = (r['formal_query'] + '\n').encode()
        assert (raw / r['query_path']).read_bytes() == q
        assert sha(q) == r['query_hash']
        for name in [r['query_path'], r['stdout_path'], r['stderr_path'], *r['trace_paths']]:
            assert name in hashes, ('not covered by raw manifest', name)
        output = (raw / r['stdout_path']).read_text() + '\n' + (raw / r['stderr_path']).read_text()
        verdicts = re.findall(r'Formula is (NOT satisfied|satisfied|MAYBE satisfied)', output)
        if r['status'] == 'success':
            assert r['exit_code'] == 0 and r['termination'] == 'completed' and len(verdicts) == 1
            assert r['verdict'] == {'satisfied': 'satisfied', 'NOT satisfied': 'violated', 'MAYBE satisfied': 'inconclusive'}[verdicts[0]]
            if r['verdict'] == 'violated' or r['formal_query'].startswith('E<>'):
                assert r['trace_paths']
        else:
            assert r['verdict'] is None
    return len(hashes)


def queue_diagnosis(raw, result):
    trace = ET.parse(raw / result['trace_paths'][0]).getroot()
    nodes = {n.get('id'): n for n in trace.findall('node')}
    vectors = {v.get('id'): {x.get('variable'): x.get('value') for x in v}
               for v in trace.findall('variable_vector')}
    edges = {e.get('id'): e for e in trace.findall('system/process/edge')}
    values = lambda node: vectors[nodes[node].get('variable_vector')]
    current = trace.get('initial_node')
    changes, acks = [], []
    for t in trace.findall('transition'):
        assert t.get('from') == current
        after = t.get('to')
        before_q, after_q = int(values(current)['sys.mac_queue_q']), int(values(after)['sys.mac_queue_q'])
        for ident in t.get('edges').split():
            e = edges[ident]
            if e.get('from', '').endswith('.WaitPHYAck') and e.get('to', '').endswith('.Idle') and e.findtext('sync') == 'mac_phy_ack?':
                assert before_q == after_q
                acks.append({'from': current, 'to': after, 'edge': ident})
        if before_q != after_q:
            updates = [edges[x].findtext('update') for x in t.get('edges').split()]
            assert any('mac_queue_q - 0 + 1' in u for u in updates)
            assert after_q == before_q + 1
            changes.append({'from': current, 'to': after, 'before': before_q, 'after': after_q,
                            'overflow': int(values(after)['sys.mac_queue_overflow_seen']), 'service': 0, 'arrival': 1})
        current = after
    assert [x['after'] for x in changes] == [1, 2, 3, 4, 5]
    assert [x['overflow'] for x in changes] == [0, 0, 0, 0, 1] and len(acks) == 4
    model = ET.parse(BASE / 'model.xml').getroot()
    declaration = model.findtext('declaration')
    assert 'const int mac_queue_K=4;' in declaration
    load = next(t for t in model.findall('template') if t.findtext('name') == 'Boundary_E_MAC_LOAD')
    step = next(t for t in load.findall('transition') if 'mac_queue_q=' in (t.findtext("label[@kind='assignment']") or ''))
    labels = {x.get('kind'): x.text for x in step.findall('label')}
    assert 'service == 0 ||' in labels['guard'] and 'service <= mac_queue_q' in labels['guard']
    assert 'arrival:int[0,1]' in labels['select'] and 'service:int[0,1]' in labels['select']
    assert 'mac_queue_q-service+arrival' in labels['assignment']
    keys = ['run_id', 'status', 'verdict', 'model_hash', 'query_hash', 'tool_version', 'formal_query']
    return {**{k: result[k] for k in keys}, 'capacity': 4, 'trace': result['trace_paths'][0],
            'queue_changes': changes, 'matching_acks_without_dequeue': acks,
            'source_transition': labels, 'interpretation': 'A real negative full-model result consistent with optional service and unrestricted arrivals. No evidence of an implementation mismatch in this trace; no universal capacity guarantee.',
            'scope': 'Saved symbolic witness and frozen source audit; no new timed replay or verifier execution.'}


def recover_c02():
    provenance = read(HERE / 'recovery-provenance.json')
    assert sha((HERE / provenance['archive']).read_bytes()) == provenance['archive_sha256']
    assert sha((HERE / provenance['manager_file']).read_bytes()) == provenance['manager_sha256']
    with tempfile.TemporaryDirectory() as tmp:
        with tarfile.open(HERE / provenance['archive']) as tar:
            tar.extractall(tmp, filter='data')
        package = Path(tmp) / provenance['source_path']
        queue = package / 'queue'
        report = read(package / 'memory-limit-report.json')
        result = read(queue / 'attempts/001-29c3409912fe43029fa925b140dbf40a/result.json')
        attempt = queue / 'attempts' / result['run_id']
        hashes = read(attempt / 'hashes.json')
        assert set(hashes) == {'attempt.json', 'result.json', 'stdout.txt', 'stderr.txt', 'telemetry.csv'}
        for name, digest in hashes.items():
            assert sha((attempt / name).read_bytes()) == digest, name
        assert result == report['attempt']
        # Earlier PR #53 supplied summary must identify precisely the recovered attempt.
        assert (attempt / 'result.json').read_bytes() == (ROOT / 'evidence/verification/p3-20260925-c02-audit/full-run-result.json').read_bytes()
        assert result['status'] == 'memory_limit' and result['verdict'] is None and not result['trace_paths']
        assert sha((queue / 'model.xml').read_bytes()) == result['model_hash'] == MODEL
        assert sha((queue / 'query-001.q').read_bytes()) == result['query_hash']
        session = queue / 'sessions' / result['session']
        assert (session / 'version.stdout.txt').read_text() == result['tool_version']
        session_data = read(session / 'session.json')
        assert session_data['hardware']['manager_hash'] == report['manager_hash'] == provenance['manager_sha256']
        assert sha((queue / 'queue.json').read_bytes()) == session_data['queue_hash']
        old_provenance = read(package / 'provenance.json')
        assert old_provenance['parameter_set'] == read(BASE / 'parameters.json')
        assert old_provenance['instance_vector'] == read(BASE / 'instance-vector.json')
        assert old_provenance['baseline_manifest_sha256'] == sha((ROOT / 'manifests/baselines/reviewer-r1.yaml').read_bytes())
        rows = list(csv.DictReader(io.StringIO((attempt / 'telemetry.csv').read_text())))
        assert len(rows) > 1
        assert max(int(r['peak_rss_bytes']) for r in rows) == result['peak_rss_bytes']
        assert result['peak_rss_bytes'] > result['memory_stop_bytes']
        assert all(float(a['elapsed_seconds']) < float(b['elapsed_seconds']) for a, b in zip(rows, rows[1:]))
        return {'classification': 'recovered raw diagnostic; not reinstated as accepted quantitative evidence',
                'run_id': result['run_id'], 'package_run_id': report['package_run_id'],
                'status': result['status'], 'verdict': result['verdict'], 'model_hash': result['model_hash'],
                'query_hash': result['query_hash'], 'tool_version': result['tool_version'],
                'runtime_seconds': result['elapsed_seconds'], 'peak_rss_bytes': result['peak_rss_bytes'],
                'telemetry_samples': len(rows), 'artifact_hashes': hashes,
                'summary_byte_identical_to_pr53': True, 'manager_hash': report['manager_hash'],
                'archive': relative(HERE / provenance['archive']), 'archive_sha256': provenance['archive_sha256'],
                'provenance': relative(HERE / 'recovery-provenance.json'),
                'caveat': 'Original preparation provenance says not_started/old manager; terminal result and memory-limit-report supersede it. Restoration does not amend the historical exclusion or supply a C02 verdict/P4 benchmark.'}


def build():
    assert sha((BASE / 'model.xml').read_bytes()) == MODEL
    specs = {x['id']: x for x in read(BASE / 'selected-queries.json')}
    records, archives, missing, queue = [], [], [], None
    for manifest in sorted(SOURCE.glob('*/archive.json')):
        entry = read(manifest)
        metadata = manifest.parent
        run, results = read(metadata / 'run.json'), read(metadata / 'results.json')
        assert run['model_hash'] == MODEL
        archive = ROOT / entry['archive']
        if not archive.exists():
            missing.append({'run_group': run['run_id'], **entry, 'metadata': relative(metadata),
                            'record_count': len(results), 'interpretation': 'metadata only; raw audit unavailable, existing acceptance decision not revoked'})
        else:
            assert sha(archive.read_bytes()) == entry['sha256'], archive
            with tempfile.TemporaryDirectory() as tmp:
                with tarfile.open(archive) as tar:
                    tar.extractall(tmp, filter='data')
                raw = Path(tmp) / metadata.name
                checked = validate_group(raw, metadata, run, results)
                for r in results:
                    if r['run_id'] == 'p3-20260923-003-02-C01-queue':
                        queue = queue_diagnosis(raw, r)
            archives.append({'run_group': run['run_id'], **entry, 'checked_files': checked, 'records': len(results)})
        for result in results:
            assert result['model_hash'] == MODEL
            assert sha((result['formal_query'] + '\n').encode()) == result['query_hash']
            if result['property_id'] in specs:
                assert result['formal_query'] == specs[result['property_id']]['query']
            records.append({**result, 'raw_audited': archive.exists(), 'archive': entry['archive'],
                            'metadata': relative(metadata / 'run.yaml'), 'record_path': relative(metadata / 'results.json')})
    assert len({r['run_id'] for r in records}) == len(records)
    assert queue is not None
    selected = [r for r in records if r['raw_audited'] and r['property_id'] in specs]
    properties = []
    for ident, spec in specs.items():
        rows = [r for r in selected if r['property_id'] == ident]
        verdicts = {r['verdict'] for r in rows if r['status'] == 'success'}
        assert len(verdicts) <= 1
        properties.append({'property_id': ident, 'formula': spec['query'],
                           'machine_verdict': next(iter(verdicts), None), 'runs': [r['run_id'] for r in rows]})
    counts = {'audited_archives': len(archives), 'audited_selected_executions': len(selected),
              'selected_execution_statuses': dict(Counter(r['status'] for r in selected)),
              'selected_formula_verdicts': dict(Counter(p['machine_verdict'] or 'inconclusive' for p in properties)),
              'metadata_only_executions': sum(x['record_count'] for x in missing)}
    return {'base_commit': '6304dd83da71bb2b22fe829f60c32d1832d40aaf', 'issue': 39,
            'baseline_id': 'reviewer-r1-gate1-20260923', 'model_hash': MODEL,
            'classification': 'evidence audit, not new verification or P3 acceptance', 'counts': counts,
            'archives': archives, 'missing_archives': missing, 'properties': properties, 'records': records,
            'queue_diagnosis': queue, 'recovered_c02': recover_c02()}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    output = build()
    rendered = json.dumps(output, ensure_ascii=False, indent=2) + '\n'
    if args.write:
        (HERE / 'audit.json').write_text(rendered)
    else:
        assert (HERE / 'audit.json').read_text() == rendered, 'audit output changed'
    print(json.dumps(output['counts'], indent=2))
    print('Queue witness and recovered C02 hashes/metadata/telemetry checked; no new UPPAAL run.')
