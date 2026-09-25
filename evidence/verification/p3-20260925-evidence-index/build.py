"""Consolidate retained full-model evidence; never invoke the verifier."""
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
SOURCE = ROOT / 'evidence/verification/p3-20260923'
BASE = ROOT / 'evidence/governance/20260906-baseline/gate1-20260923'
MODEL_HASH = '592678ed678ce8f70cf278f542e48bd2bb739969b53a962423d3e63f91e3e1e2'
sha = lambda data: hashlib.sha256(data).hexdigest()
spec = importlib.util.spec_from_file_location('raw_audit', SOURCE / 'audit.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def build():
    assert sha((BASE / 'model.xml').read_bytes()) == MODEL_HASH
    queries = json.loads((BASE / 'selected-queries.json').read_text())
    properties = {q['id']: {'property_id': q['id'], 'formal_query': q['query'], 'role': q['role'], 'query_hash': sha((q['query']+'\n').encode()), 'machine_verdict': None, 'runs': []} for q in queries}
    archives = []
    all_ids = set()
    for manifest in sorted(SOURCE.glob('*/archive.json')):
        entry = json.loads(manifest.read_text())
        archive = ROOT / entry['archive']
        assert sha(archive.read_bytes()) == entry['sha256'], archive
        with tempfile.TemporaryDirectory() as tmp:
            with tarfile.open(archive) as tar:
                tar.extractall(tmp, filter='data')
            raw = Path(tmp) / manifest.parent.name
            audit.audit(raw)
            for name in ['run.json', 'run.yaml', 'results.json']:
                assert (raw/name).read_bytes() == (manifest.parent/name).read_bytes(), name
            run = json.loads((raw/'run.json').read_text())
            results = json.loads((raw/'results.json').read_text())
            assert run['model_hash'] == MODEL_HASH
            for key in ['parameter_set', 'instance_vector', 'native_hardware', 'operating_environment', 'source_hash', 'generator_hash', 'tool_version']:
                assert run[key], key
            archive_record = {'run_group': run['run_id'], 'archive': entry['archive'], 'archive_sha256': entry['sha256'], 'metadata': str((manifest.parent/'run.yaml').relative_to(ROOT)), 'record_count': len(results)}
            archives.append(archive_record)
            for result in results:
                assert result['run_id'] not in all_ids
                all_ids.add(result['run_id'])
                p = properties[result['property_id']]
                assert result['query_hash'] == p['query_hash'] and result['formal_query'] == p['formal_query']
                keys = ['run_id', 'status', 'verdict', 'model_hash', 'query_hash', 'source_commit', 'tool_version', 'runtime_seconds', 'peak_working_set_bytes', 'states_explored', 'trace_paths']
                row = {k: result[k] for k in keys}
                row['record_path'] = str((manifest.parent/'results.json').relative_to(ROOT))
                row['archive'] = entry['archive']
                row['metadata_path'] = archive_record['metadata']
                row['stdout_path_in_archive'] = raw.name+'/'+result['stdout_path']
                row['stderr_path_in_archive'] = raw.name+'/'+result['stderr_path']
                p['runs'].append(row)
                if result['status'] == 'success' and result['verdict'] in ['satisfied', 'violated']:
                    assert p['machine_verdict'] in [None, result['verdict']], 'conflicting verdicts'
                    p['machine_verdict'] = result['verdict']
    assert len(archives) == 9 and len(all_ids) == 38
    for p in properties.values():
        assert p['runs'], p['property_id']
        p['work_disposition'] = 'machine_evidence_available' if p['machine_verdict'] else 'inconclusive'
    properties['C01-deadlock']['work_disposition'] = 'temporarily_deferred_by_user; unresolved; no further deadlock work'
    for key in ['C01-attempts', 'attempt-protocol']:
        properties[key]['proof_acceptance'] = {'decision': 'accepted separate concrete-XML inductive argument; machine verdict unchanged', 'pr': 55}
    properties['C02-ack-elapsed']['proof_acceptance'] = {'decision': 'accepted pinned safety-transfer and time-divergent ACK-or-timeout completion scope; machine verdict unchanged', 'pr': 53}
    all_runs = [r for p in properties.values() for r in p['runs']]
    return {'issue': 39, 'baseline_id': 'reviewer-r1-gate1-20260923', 'model_hash': MODEL_HASH, 'base_commit': '7a4ac3c47329548612b0a563bf9cae20e3835384', 'kind': 'retained full-model evidence index, not acceptance or new verification', 'counts': {'archives': len(archives), 'executions': len(all_runs), 'properties': len(properties), 'execution_statuses': dict(Counter(r['status'] for r in all_runs)), 'unique_machine_verdicts': dict(Counter(p['machine_verdict'] or 'inconclusive' for p in properties.values()))}, 'excluded': ['intermediate progress archives: duplicate partial checkpoints, not extra executions', 'p3-20260923-001: incomplete preflight, no formula execution', '001-29c3409912fe43029fa925b140dbf40a: lost raw archive, excluded from accepted quantitative evidence', 'reduced C02 model and negative control: separate model identities; see separate package, not full-model results'], 'archives': archives, 'properties': list(properties.values())}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    result = build()
    text = json.dumps(result, indent=2) + '\n'
    path = HERE/'results-index.json'
    if args.write:
        path.write_text(text)
    else:
        assert path.read_text() == text, 'index does not reproduce'
    print(json.dumps(result['counts'], indent=2))
