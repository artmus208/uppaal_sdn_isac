"""Derive the review proposal from immutable accepted Git inputs; no engine."""
import difflib
import hashlib
import json
from pathlib import Path
import re
import subprocess
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CANDIDATE = 'evidence/instantiation/uav-service-completion-candidate'
PACKET = HERE.relative_to(ROOT).as_posix()
BASE = '61386aa358805082b705dcd00c8cbfde5fb98248'
PUBLICATION = 'fdbfd5619385eae31101dcfc285010b96cc85b45'
BASELINE = 'uav-service-completion-r1-20261002'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def dump(name, obj):
    (HERE / name).write_text(json.dumps(obj, indent=2, sort_keys=True) + '\n')


def ref(path):
    return {'path': path, 'sha256': sha((ROOT / path).read_bytes())}


def main():
    candidate = ROOT / CANDIDATE
    inv = json.loads((candidate / 'inventory.json').read_bytes())
    parameters = json.loads((candidate / 'parameters.json').read_bytes())
    vector = json.loads((candidate / 'instance-vector.json').read_bytes())
    root = ET.fromstring((candidate / 'model.xml').read_bytes())
    constants = []
    for owner, text in [('global', root.findtext('declaration'))] + [(t.findtext('name'), t.findtext('declaration') or '') for t in root.findall('template')]:
        text = re.sub(r'//[^\n]*|/\*[\s\S]*?\*/', '', text)
        constants.extend({'owner': owner, 'declaration': ' '.join(m.split())} for m in re.findall(r'\bconst\s+[^;]+;', text))
    dump('parameter-inventory.json', {
        'candidate': parameters,
        'inherited': json.loads((ROOT / parameters['frozen_parameters_path']).read_bytes()),
        'emitted_constant_declarations': constants,
        'source': ref(CANDIDATE + '/parameters.json'),
        'note': 'Inherited T_complete=40 is inactive for completion; new relative c82_D_service=40 controls receipt. All units abstract.'})
    bindings = re.findall(r'(\w+)\s*=\s*(\w+)\(([^;]*)\);', root.findtext('system'))
    dump('instance-inventory.json', {'source': ref(CANDIDATE + '/instance-vector.json'), 'vector': vector,
        'ordered_bindings': [{'instance': i, 'template': t, 'arguments': a} for i, t, a in bindings],
        'note': 'candidate_not_accepted is preserved historical generation metadata, not current PR acceptance or a Gate decision.'})
    roles = {'completion-safety': 'universal completion safety obligation', 'deadlock': 'universal global deadlock obligation',
        'success': 'existential success / non-vacuity', 'deadline-equality': 'boundary reachability diagnostic'}
    queries = [{'id': name, 'path': CANDIDATE + '/queries/' + name + '.q', 'formula': q['formula'], 'sha256': q['hash'],
        'role': roles.get(name, 'existential causal or failure non-vacuity diagnostic'), 'selected_proposal': True,
        'disposition': 'proposed_input_awaiting_independent_selection', 'query_hash_in_executed_runs': None,
        'verdict': None, 'execution_status': 'not_executed'} for name, q in sorted(inv['queries'].items())]
    query_hash = sha(json.dumps({q['path']: q['sha256'] for q in queries}, sort_keys=True).encode())
    dump('query-inventory.json', {'queries': queries, 'selected_query_set_hash': query_hash,
        'hash_rule': 'SHA256 of default json.dumps(path-to-exact-file-SHA256 dictionary, sort_keys=True).encode(UTF-8)',
        'selection_disposition': 'All eleven proposed for independent input acceptance; none has an exhaustive verdict.',
        'coverage_limit': 'No fairness or universal SLA/liveness formula in this pack; no such claim follows from selection.'})
    results = json.loads((candidate / 'results.json').read_bytes())
    runs = []
    for r in results['runs']:
        cell = r['result'].split('/')[1]
        provenance = json.loads((candidate / r['provenance']).read_bytes())
        runs.append(dict(r, cell=cell, method=provenance['method'],
            applicability='exact_candidate_model' if r['model_hash'] == inv['model_hash'] else 'earlier_diagnostic_model_only',
            execution_baseline_id=provenance['baseline_id'], execution_candidate_id=provenance['candidate_id'],
            publication_commit=PUBLICATION))
    dump('machine-evidence-inventory.json', {'runs': runs, 'accepted_verification_runs': [],
        'historical_trace_transfer': False, 'all_query_verdicts': {q['id']: None for q in queries},
        'archives': [ref(CANDIDATE + '/' + n) for n in ['raw-traces.zip', 'source-snapshots.zip', 'raw-index.json', 'source-index.json']],
        'note': 'Publication commit never replaces an execution checkpoint. Diagnostic runs on earlier models stay indexed but are not results of this baseline.'})
    paths = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', BASE, '--', CANDIDATE], cwd=ROOT).decode().splitlines()
    historical = ['evidence/scalability/family-series-68/generated/n1/' + n for n in ['model.xml', 'parameters.json', 'instance-vector.json']]
    protected = ['manifests/current.json', 'manifests/collaboration-v2.yaml', 'manifests/baselines/reviewer-r1.yaml',
        'manifests/baselines/uav-family-r1.yaml', 'manifests/v1.md', 'manifests/collaboration-v1.yaml', 'CONTRIBUTING.md',
        'CONTRIBUTING-v2.md', 'manifests/v2.md', 'src/uppaal_mcp/integrated/inputs.py', 'levels_tex/samplepaper.tex']
    lineage = ['evidence/scalability/family-series-68/generate.py', 'src/uppaal_mcp/integrated/generator.py',
        'src/uppaal_mcp/integrated/adapt.py', 'src/uppaal_mcp/integrated/boundary.py']
    all_paths = sorted(set(paths + historical + protected + lineage))
    hashes = {p: sha(subprocess.check_output(['git', 'show', BASE + ':' + p], cwd=ROOT)) for p in all_paths}
    dump('input-hashes.json', {'input_commit': BASE, 'accepted_publication_commit': PUBLICATION,
        'hash_rule': 'SHA256 exact Git blob bytes', 'files': hashes, 'protected_paths': protected,
        'generation_reads': [CANDIDATE + '/generate.py', historical[0], historical[2]],
        'lineage_only_not_live_compiler_inputs': lineage})
    manifest = {'schema_version': '1.0', 'kind': 'single-model-baseline-proposal',
        'metadata': {'id': BASELINE, 'status': 'proposed', 'maturity': 'awaiting_independent_decision', 'frozen': False, 'activated': False},
        'repository': {'url': 'https://github.com/artmus208/uppaal_sdn_isac', 'branch': 'read', 'input_commit': BASE,
            'accepted_publication_commit': PUBLICATION, 'candidate_merge_commit': '07e45268bbfbb4c1293e4e4f4227792794583509',
            'execution_checkpoints': ref(CANDIDATE + '/source-index.json')},
        'scope': {'N': 1, 'processes': 51, 'requests': 1, 'results': 1, 'composition': 'PHY || MAC || SDN || APP || ENV || OBS || ResultJob', 'other_N_included': []},
        'hashing': {'algorithm': 'sha256', 'rule': 'exact_file_bytes', 'input_inventory': ref(PACKET + '/input-hashes.json'),
            'generation_source_hash': sha(json.dumps({p: hashes[p] for p in [CANDIDATE + '/generate.py', historical[0], historical[2]]}, sort_keys=True).encode()),
            'generation_source_hash_rule': 'SHA256 of default json.dumps(sorted-key dictionary of the three live generation read paths to SHA256).encode(UTF-8)'},
        'model': ref(CANDIDATE + '/model.xml'), 'generator': ref(CANDIDATE + '/generate.py'),
        'generation_inputs': [ref(p) for p in [historical[0], historical[2]]],
        'parameters': {'candidate': ref(CANDIDATE + '/parameters.json'), 'inherited': ref(historical[1]), 'inventory': ref(PACKET + '/parameter-inventory.json')},
        'instance_vector': ref(CANDIDATE + '/instance-vector.json'), 'instance_inventory': ref(PACKET + '/instance-inventory.json'),
        'query_set': {'inventory': ref(PACKET + '/query-inventory.json'), 'selected_query_set_hash': query_hash,
            'selection_disposition': 'proposed_all_11_awaiting_independent_acceptance', 'files': queries, 'verdicts': {q['id']: None for q in queries}},
        'tool_evidence': {'version': runs[6]['tool_version'], 'source': ref(CANDIDATE + '/runs/replay-001/result.json'),
            'capture_method': 'Engine.getVersion saved by CausalReplay', 'future_run_version_required': True,
            'license_scope': 'Observed historical candidate executions only; no current native probe or new execution authorization.'},
        'machine_evidence': ref(PACKET + '/machine-evidence-inventory.json'), 'accepted_verification_runs': [],
        'reproduction_commands': ['python3 -B ' + CANDIDATE + '/generate.py --check', 'python3 -B ' + CANDIDATE + '/audit.py',
            'python3 -B ' + PACKET + '/check.py', 'python3 -B -m unittest discover -s ' + PACKET + " -p 'test_*.py' -v"],
        'assumptions': ['one request/result with bounded identities, no ID reuse', 'fixed five-unit acquisition after sensing readiness',
            'sample age classes [0,5), [5,10), [10,infinity); update class also age-based', 'FIFO rank for one result in abstract queue K=4 with absorbing overflow',
            'optional one eligible COMM/JOINT service per five-unit epoch; no fairness', 'lossy one-attempt transport bounded by one unit; no retry',
            'abstract units and classes; no physical calibration'],
        'boundaries': {'service': 'request age <=40; receipt and timeout alternatives at equality', 'freshness': 'sample age <5; age=5 stale'},
        'limitations': ['No universal completion, SLA, fairness, deadlock or whole-system equivalence established.',
            'Historical P1/P2 component decisions need an explicit disposition for the changed composition.',
            'Prior model results and PR81 old-model rejection trace do not transfer.'],
        'gate_1': {'status': 'pending_independent_decision', 'passed': False, 'P1_applicability': 'proposed', 'P2_applicability': 'proposed',
            'decision_record': None, 'reviewer_proposed': 'artmus208'},
        'operational_activation': {'status': 'pending', 'issue': 'https://github.com/artmus208/uppaal_sdn_isac/issues/84',
            'merge_commit': None, 'decision_time_utc': None, 'decision_record': None},
        'decisions': {'candidate_acceptance': 'https://github.com/artmus208/uppaal_sdn_isac/pull/83#pullrequestreview-5388261528',
            'historical_P1_P2': 'https://github.com/artmus208/uppaal_sdn_isac/pull/73#issuecomment-5890790922',
            'historical_P4_activation': 'https://github.com/artmus208/uppaal_sdn_isac/pull/75#issuecomment-5891123461',
            'v2_activation': 'https://github.com/artmus208/uppaal_sdn_isac/issues/64#issuecomment-5878071165',
            'new_decision': None},
        'selection': {'eligible_workstreams': ['P3', 'P5'], 'explicit_issue_selection_required': True, 'execution_authorized_by_selection': False,
            'automatic_verdict_transfer': False, 'historical_current_pointer_preserved': True, 'historical_P4_policy_preserved': True}}
    dump('proposed-baseline.yaml', manifest)
    policy = '''\nuav_completion_baseline_selection:
  manifest: manifests/baselines/uav-service-completion-r1.yaml
  baseline_id: uav-service-completion-r1-20261002
  eligible_workstreams: [P3, P5]
  scope: Full UAV N=1 only, 51 processes, one request and one result.
  historical_default: manifests/baselines/reviewer-r1.yaml
  activation_issue: https://github.com/artmus208/uppaal_sdn_isac/issues/84
  activation_rule: Independent applicability and Gate 1 decisions, approved operational scope, merge into read, then explicit activation with actual merge SHA and UTC time.
  selection_rule: P3/P5 Issue explicitly pins baseline ID, manifest SHA256, input commit and activation decision; current.json and historical P4 selection are preserved.
  gate_rule: Use the exact changed-model Gate 1 and post-merge activation decision; candidate acceptance and old-family decisions alone are insufficient.
  audit_command: python3 -B evidence/governance/uav-service-completion-baseline-20261002/check.py --operational
  automatic_verdict_transfer: false
  execution_authorized_by_selection: false
  P3_core_evidence_accepted_by_selection: false
  R07_closed_by_selection: false
'''
    (HERE / 'proposed-selection.yaml').write_text(policy.lstrip('\n'))
    target = 'manifests/baselines/uav-service-completion-r1.yaml'
    patch = 'diff --git a/' + target + ' b/' + target + '\nnew file mode 100644\n'
    patch += ''.join(difflib.unified_diff([], (HERE / 'proposed-baseline.yaml').read_text().splitlines(True), fromfile='/dev/null', tofile='b/' + target))
    contract = 'manifests/collaboration-v2.yaml'
    before = (ROOT / contract).read_text()
    patch += 'diff --git a/' + contract + ' b/' + contract + '\n'
    patch += ''.join(difflib.unified_diff(before.splitlines(True), (before + policy).splitlines(True), fromfile='a/' + contract, tofile='b/' + contract))
    (HERE / 'proposed-operational.patch').write_text(patch)
    dump('decision-pins.json', {'baseline_id': BASELINE, 'input_commit': BASE, 'publication_commit': PUBLICATION,
        'model': manifest['model'], 'generator': manifest['generator'], 'generation_source_hash': manifest['hashing']['generation_source_hash'],
        'parameter_set': manifest['parameters'], 'instance_vector': manifest['instance_vector'], 'instance_inventory': manifest['instance_inventory'],
        'selected_query_set_hash': query_hash, 'query_inventory': manifest['query_set']['inventory'],
        'manuscript': ref('levels_tex/samplepaper.tex'), 'input_inventory': ref(PACKET + '/input-hashes.json'),
        'proposal_manifest': ref(PACKET + '/proposed-baseline.yaml'), 'operational_patch': ref(PACKET + '/proposed-operational.patch'),
        'tool_evidence': manifest['tool_evidence'], 'gate_1_status': 'pending_independent_decision', 'activation_status': 'pending'})
    print('Derived proposal only:', len(hashes), 'input hashes;', len(queries), 'unexecuted queries')


if __name__ == '__main__':
    main()
