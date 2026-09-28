"""Build/check the explicit P3 core whitelist from audited saved evidence; no UPPAAL."""
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PREVIOUS = ROOT / 'evidence/verification/p3-20260926-dispositions'
REDUCED = ROOT / 'evidence/verification/p3-20260924-c02-reduced'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_text())
relative = lambda p: str(p.relative_to(ROOT))


def execute(script, *args):
    result = subprocess.run([sys.executable, '-B', str(script), *map(str, args)],
                            cwd=ROOT, capture_output=True, text=True, check=True)
    return result.stdout


def build():
    spec = importlib.util.spec_from_file_location('prior_p3_audit', PREVIOUS / 'audit.py')
    audit = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(audit)
    previous = audit.build()
    assert previous == read(PREVIOUS / 'audit.json'), 'PR #60 audit changed'
    execute(REDUCED / 'audit.py', REDUCED / 'runs/p3-20260924-c02-reduced-001')
    proof_scripts = {
        'C02': ROOT / 'evidence/verification/p3-20260925-c02-audit/check_premises.py',
        'C01-attempts-protocol': ROOT / 'evidence/verification/p3-20260925-c01-structure/check.py',
    }
    proofs = {name: {'script': relative(script), 'script_sha256': sha(script),
                     'kind': 'static proof support; no model-checking run_id',
                     'result': json.loads(execute(script))}
              for name, script in proof_scripts.items()}
    accepted, excluded = [], []
    identity = ['run_id', 'status', 'verdict', 'model_hash', 'query_hash', 'tool_version']
    for r in previous['records']:
        row = {k: r[k] for k in identity}
        row.update(property_id=r['property_id'], formal_query=r['formal_query'],
                   model_scope='full_frozen', source_commit=r['source_commit'],
                   record_path=r['record_path'], metadata_path=r['metadata'],
                   archive=r['archive'], trace_paths=r['trace_paths'],
                   runtime_seconds=r['runtime_seconds'],
                   citable_peak_memory_bytes=r['peak_working_set_bytes'],
                   states_explored=r['states_explored'])
        if not r['raw_audited']:
            row.update(acceptance='excluded_from_current_core_evidence', p5_use='none',
                       reason='Raw archive absent; historical scoped review decision retained without a new reproducibility claim.')
            excluded.append(row)
            continue
        positive = r['status'] == 'success' and r['verdict'] == 'satisfied'
        negative = r['status'] == 'success' and r['verdict'] == 'violated'
        row.update(acceptance='accepted_as_recorded',
                   evidence_class='positive_existential_witness' if positive else 'negative_counterexample' if negative else 'inconclusive_diagnostic',
                   p5_use='witness_fragment_only' if positive else 'failure_scenario_only' if negative else 'none',
                   allowed_claim='Exact existential formula and retained trace only' if positive else 'Exact violated formula and retained counterexample only' if negative else 'Recorded termination/resource observations only; no property truth or falsity')
        accepted.append(row)
    reduced_dir = REDUCED / 'runs/p3-20260924-c02-reduced-001'
    reduced_run = read(reduced_dir / 'run.json')
    assert reduced_run['source_tree_clean_at_start'] is True
    for r in read(reduced_dir / 'results.json'):
        row = {k: r[k] for k in identity}
        row.update(property_id=r['run_id'].removeprefix('p3-20260924-c02-reduced-001-'),
                   formal_query=r['query'], model_scope='negative_control' if r['verdict'] == 'violated' else 'C02_abstraction',
                   source_commit=r['source_commit'], record_path=relative(reduced_dir / 'results.json'),
                   metadata_path=relative(reduced_dir / 'run.json'), raw_directory=relative(reduced_dir),
                   trace_paths=r['trace_paths'], runtime_seconds=r['runtime_seconds'],
                   reported_peak_memory_bytes=r['peak_working_set_bytes'], citable_peak_memory_bytes=None,
                   memory_disposition='No sample before exit; raw zero is NOT zero memory usage.',
                   states_explored=r['states_explored'], acceptance='accepted_as_recorded',
                   evidence_class='abstraction_validation', p5_use='none',
                   allowed_claim='Reduced-model result only; C02 transfer requires the separate accepted pinned proof and its restrictions.')
        accepted.append(row)
    recovered = previous['recovered_c02']
    row = {k: recovered[k] for k in identity}
    row.update(property_id='C02-ack-elapsed', model_scope='full_frozen',
               package_run_id=recovered['package_run_id'],
               runtime_seconds=recovered['runtime_seconds'],
               citable_peak_memory_bytes=recovered['peak_rss_bytes'], states_explored=None,
               archive=recovered['archive'], archive_sha256=recovered['archive_sha256'],
               record_path_in_archive='evidence/verification/p3-20260925-c02-24h-001/queue/attempts/' + recovered['run_id'] + '/result.json',
               provenance_path=recovered['provenance'], audit_path=relative(PREVIOUS / 'audit.json'),
               acceptance='accepted_as_recovered_diagnostic', evidence_class='inconclusive_resource_diagnostic', p5_use='none',
               allowed_claim='This sampled working-set stop and recorded runtime/peak on this host/configuration only; no C02 verdict, controlled performance comparison or P4 scalability boundary.')
    accepted.append(row)
    assert len(accepted) == 48 and len(excluded) == 3
    assert len({r['run_id'] for r in accepted + excluded}) == 51
    assert all(r['status'] == 'success' and r['model_scope'] == 'full_frozen'
               for r in accepted if r['p5_use'] != 'none')
    assert {r['property_id'] for r in excluded} == {'joint-prerequisites', 'standby-receiver', 'alternative-receiver'}
    source_paths = [PREVIOUS / 'audit.py', PREVIOUS / 'audit.json', PREVIOUS / 'recovery-provenance.json',
                    reduced_dir / 'run.json', reduced_dir / 'results.json',
                    ROOT / 'manifests/baselines/reviewer-r1.yaml', ROOT / 'manifests/collaboration-v1.yaml']
    return {'schema_version': 1, 'issue': 39, 'baseline_id': 'reviewer-r1-gate1-20260923',
            'base_commit': '1bf6c51c73e0f6a2dc1e785104dadd7dcc8ff46b',
            'authority': 'PROPOSED whitelist only; requires explicit user acceptance recorded in decision.json and Issue #39. No machine verdict is created.',
            'sources': {relative(p): sha(p) for p in source_paths},
            'counts': {'accepted_records': len(accepted), 'audited_full_selected': 43,
                       'reduced_control_records': 4, 'recovered_diagnostic_records': 1,
                       'excluded_metadata_only': len(excluded),
                       'evidence_classes': dict(Counter(r['evidence_class'] for r in accepted)),
                       'p5_eligible_fragments': sum(r['p5_use'] != 'none' for r in accepted)},
            'p5_rule': 'Eligible fragments do not constitute an accepted end-to-end scenario. P5 must audit the actual PHY-MAC-SDN-SLA causal chain and preserve each formula scope.',
            'accepted_runs': accepted, 'excluded_runs': excluded, 'proof_checks': proofs}


def validate_decision(registry):
    d = read(HERE / 'decision.json')
    assert d['milestone'] == 'P3_core_evidence_accepted'
    assert d['status'] == 'proposed_for_user_acceptance'
    assert d['P3_core_evidence_accepted'] is False
    assert d['independent_review'] is False
    assert d['P3_complete'] is False and d['Gate_2_passed'] is False
    assert d['C06_status'] == 'pending_P4'
    assert d['run_registry_sha256'] == sha(HERE / 'accepted-runs.json')
    assert set(d['covered_comment_ids']) == {'C01', 'C02', 'C03', 'C04', 'C05'}
    assert d['requirement_outcomes']['C01']['queue_safety'] == 'violated'
    assert d['requirement_outcomes']['C01']['global_deadlock'] == 'deferred_unproved'
    assert d['requirement_outcomes']['C02']['direct_full_model'] == 'inconclusive'
    assert d['accepted_run_ids'] == [r['run_id'] for r in registry['accepted_runs']]
    assert d['excluded_run_ids'] == [r['run_id'] for r in registry['excluded_runs']]


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    registry = build()
    rendered = json.dumps(registry, ensure_ascii=False, indent=2) + '\n'
    path = HERE / 'accepted-runs.json'
    if args.write:
        path.write_text(rendered)
    else:
        assert path.read_text() == rendered, 'Registry does not reproduce'
        validate_decision(registry)
    print(json.dumps(registry['counts'], indent=2))
    print('Raw evidence, proof inputs and scoped registry checked; no verifier invoked.')
