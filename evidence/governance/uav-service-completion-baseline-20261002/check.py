"""Standalone static proposal/provenance audit. Never runs UPPAAL or grants Gate 1."""
import argparse
import difflib
import hashlib
import importlib.util
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PACKET = HERE.relative_to(ROOT).as_posix()
CANDIDATE = 'evidence/instantiation/uav-service-completion-candidate'
BASE = '61386aa358805082b705dcd00c8cbfde5fb98248'
PUBLICATION = 'fdbfd5619385eae31101dcfc285010b96cc85b45'
MODEL = 'b8ab50e112b71491f8242789cc7906497baf8440c473d7a5a4d5214840187e02'


def require(value, message):
    if not value:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path):
    p = PurePosixPath(path)
    require(not p.is_absolute() and '..' not in p.parts and '\\' not in path, 'invalid path')
    target = (ROOT / path).resolve()
    require(target.is_relative_to(ROOT), 'path escapes repository')
    return target.read_bytes()


def git_blob(commit, path):
    return subprocess.check_output(['git', 'show', commit + ':' + path], cwd=ROOT)


def module(name):
    spec = importlib.util.spec_from_file_location('baseline84_' + name, ROOT / CANDIDATE / (name + '.py'))
    obj = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj


def no_false_acceptance(m):
    require(m['metadata'] == {'id': 'uav-service-completion-r1-20261002', 'status': 'proposed',
        'maturity': 'awaiting_independent_decision', 'frozen': False, 'activated': False}, 'unsupported accepted/frozen/activated claim')
    require(m['gate_1']['status'] == 'pending_independent_decision' and m['gate_1']['passed'] is False
        and m['gate_1']['decision_record'] is None and m['gate_1']['P1_applicability'] == 'proposed'
        and m['gate_1']['P2_applicability'] == 'proposed', 'unsupported Gate 1 claim')
    require(m['operational_activation'] == {'status': 'pending', 'issue': 'https://github.com/artmus208/uppaal_sdn_isac/issues/84',
        'merge_commit': None, 'decision_time_utc': None, 'decision_record': None}, 'unsupported activation claim')
    require(m['accepted_verification_runs'] == [] and m['decisions']['new_decision'] is None, 'unsupported accepted verification/decision')
    require(m['selection'] == {'eligible_workstreams': ['P3', 'P5'], 'explicit_issue_selection_required': True,
        'execution_authorized_by_selection': False, 'automatic_verdict_transfer': False,
        'historical_current_pointer_preserved': True, 'historical_P4_policy_preserved': True}, 'selection claims changed')


def validate_run(row, expected):
    for key in expected:
        require(row.get(key) == expected[key], 'cross-baseline or run provenance mismatch: ' + key)
    require(row['execution_baseline_id'] is None, 'retroactive baseline attribution')
    require(row['execution_candidate_id'] == 'uav-service-completion-candidate-82-n1', 'wrong execution candidate')
    require(row['publication_commit'] == PUBLICATION and row['source_commit'] != PUBLICATION, 'execution checkpoint relabelled')
    require(row['applicability'] == ('exact_candidate_model' if row['model_hash'] == MODEL else 'earlier_diagnostic_model_only'), 'incorrect model applicability')
    require(row['property_verdict'] is None and row['query_hash'] is None, 'unexecuted query verdict')


def check(manifest=None, reader=read, expensive=True, source_history=False):
    load = lambda p: json.loads(reader(p))
    m = manifest if manifest is not None else load(PACKET + '/proposed-baseline.yaml')
    no_false_acceptance(m)
    require(m['repository']['input_commit'] == BASE and m['repository']['accepted_publication_commit'] == PUBLICATION, 'input commit changed')
    require(m['scope'] == {'N': 1, 'processes': 51, 'requests': 1, 'results': 1,
        'composition': 'PHY || MAC || SDN || APP || ENV || OBS || ResultJob', 'other_N_included': []}, 'wrong scope')
    require(m['model'] == {'path': CANDIDATE + '/model.xml', 'sha256': MODEL}, 'model hash substitution')
    hashes = load(PACKET + '/input-hashes.json')
    require(hashes['input_commit'] == BASE and hashes['accepted_publication_commit'] == PUBLICATION, 'hash source changed')
    required_paths = set(subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', BASE, '--', CANDIDATE], cwd=ROOT).decode().splitlines())
    require(required_paths <= set(hashes['files']), 'candidate hash inventory incomplete')
    for p, digest in hashes['files'].items():
        require(sha(reader(p)) == digest, 'input hash drift: ' + p)
        if expensive:
            require(sha(git_blob(BASE, p)) == digest, 'hash pin disagrees with input commit: ' + p)
            if p.startswith(CANDIDATE + '/'):
                require(git_blob(PUBLICATION, p) == reader(p), 'accepted candidate changed: ' + p)
    expected_source = sha(json.dumps({p: hashes['files'][p] for p in hashes['generation_reads']}, sort_keys=True).encode())
    require(m['hashing']['generation_source_hash'] == expected_source, 'generation source aggregate mismatch')
    pins = load(PACKET + '/decision-pins.json')
    require(pins['proposal_manifest']['sha256'] == sha(reader(PACKET + '/proposed-baseline.yaml'))
        and pins['operational_patch']['sha256'] == sha(reader(PACKET + '/proposed-operational.patch')), 'decision pins drift')
    for section in ['model', 'generator', 'instance_vector', 'instance_inventory', 'machine_evidence']:
        r = m[section]
        require(sha(reader(r['path'])) == r['sha256'], 'manifest reference hash: ' + section)
    refs = m['generation_inputs'] + list(m['parameters'].values()) + [m['hashing']['input_inventory'], m['query_set']['inventory'], m['tool_evidence']['source'], m['repository']['execution_checkpoints']]
    for r in refs:
        require(sha(reader(r['path'])) == r['sha256'], 'manifest reference hash: ' + r['path'])
    params = load(PACKET + '/parameter-inventory.json')
    require(params['candidate'] == load(CANDIDATE + '/parameters.json'), 'parameter inventory mismatch')
    require(params['inherited'] == load(params['candidate']['frozen_parameters_path']), 'inherited parameter mismatch')
    root = ET.fromstring(reader(CANDIDATE + '/model.xml'))
    constants = []
    for owner, text in [('global', root.findtext('declaration'))] + [(t.findtext('name'), t.findtext('declaration') or '') for t in root.findall('template')]:
        text = re.sub(r'//[^\n]*|/\*[\s\S]*?\*/', '', text)
        constants.extend({'owner': owner, 'declaration': ' '.join(s.split())} for s in re.findall(r'\bconst\s+[^;]+;', text))
    require(constants == params['emitted_constant_declarations'], 'constant inventory mismatch')
    inst = load(PACKET + '/instance-inventory.json')
    vector = load(CANDIDATE + '/instance-vector.json')
    require(inst['vector'] == vector, 'instance vector mismatch')
    bindings = [{'instance': i, 'template': t, 'arguments': a} for i, t, a in re.findall(r'(\w+)\s*=\s*(\w+)\(([^;]*)\);', root.findtext('system'))]
    order = re.search(r'\bsystem\s+([^;]+);', root.findtext('system')).group(1)
    require([p.strip() for p in order.split(',')] == vector['system_order'], 'system order mismatch')
    require(bindings == inst['ordered_bindings'] and len(bindings) == 51, 'binding mismatch')
    query_inv = load(PACKET + '/query-inventory.json')
    queries = query_inv['queries']
    original = load(CANDIDATE + '/inventory.json')['queries']
    require(len(queries) == 11 and {q['id'] for q in queries} == set(original), 'query selection mismatch')
    require(m['query_set']['files'] == queries and m['query_set']['selection_disposition'] == 'proposed_all_11_awaiting_independent_acceptance', 'query disposition mismatch')
    for q in queries:
        require(q['formula'] == original[q['id']]['formula'] and q['sha256'] == original[q['id']]['hash'], 'query formula/hash mismatch')
        require(reader(q['path']) == (q['formula'] + '\n').encode() and sha(reader(q['path'])) == q['sha256'], 'query file mismatch')
        require(q['verdict'] is None and q['execution_status'] == 'not_executed' and q['selected_proposal'] is True
            and q['query_hash_in_executed_runs'] is None and q['disposition'] == 'proposed_input_awaiting_independent_selection', 'unsupported query verdict/selection')
    query_hash = sha(json.dumps({q['path']: q['sha256'] for q in queries}, sort_keys=True).encode())
    require(query_hash == query_inv['selected_query_set_hash'] == m['query_set']['selected_query_set_hash'], 'query set hash')
    require(m['query_set']['verdicts'] == {q['id']: None for q in queries}, 'manifest query verdict')
    evidence = load(PACKET + '/machine-evidence-inventory.json')
    expected_runs = load(CANDIDATE + '/results.json')['runs']
    require(len(evidence['runs']) == len(expected_runs) == 9 and evidence['accepted_verification_runs'] == []
        and evidence['historical_trace_transfer'] is False and evidence['all_query_verdicts'] == {q['id']: None for q in queries}, 'evidence registry mismatch')
    source = load(CANDIDATE + '/source-index.json')
    with zipfile.ZipFile(ROOT / CANDIDATE / 'source-snapshots.zip') as archive, zipfile.ZipFile(ROOT / CANDIDATE / 'raw-traces.zip') as raw:
        for row, expected in zip(evidence['runs'], expected_runs):
            validate_run(row, expected)
            cell = row['cell']
            prov = load(CANDIDATE + '/' + row['provenance'])
            result = load(CANDIDATE + '/' + row['result'])
            item = source[cell]
            require(item['commit'] == row['source_commit'] == prov['source_commit'], 'source commit mismatch')
            source_hash = sha(json.dumps({f['path']: f['hash'] for f in item['files']}, sort_keys=True).encode())
            require(source_hash == item['source_hash'] == row['source_hash'], 'source aggregate mismatch')
            for f in item['files']:
                content = archive.read(f['entry'])
                require(sha(content) == f['hash'], 'source object hash')
                if source_history:
                    require(git_blob(item['commit'], f['path']) == content, 'archived input not in execution checkpoint tree')
                require(prov['hashes'].get('/tmp/uppaal-service-82/' + f['path']) == f['hash'], 'provenance input hash mismatch')
            lookup = {f['path']: f for f in item['files']}
            require(lookup[CANDIDATE + '/model.xml']['hash'] == result['model_hash'] == row['model_hash'] == prov['model_hash'], 'per-run model mismatch')
            require(lookup[CANDIDATE + '/generate.py']['hash'] == row['generator_hash'] == prov['generator_hash'], 'per-run generator mismatch')
            require(lookup[CANDIDATE + '/inventory.json']['hash'] == prov['query_pack_hash'], 'per-run inventory hash mismatch')
            # query_pack_hash in old provenance names the whole inventory, not the selected query aggregate.
            require(result['tool_version'] == row['tool_version'], 'tool version mismatch')
            stdout = [json.loads(line) for line in raw.read('runs/' + cell + '/stdout.txt').decode().splitlines() if line.startswith('{')]
            require(any(s.get('tool_version') == row['tool_version'] for s in stdout), 'version absent from raw engine response')
            require(prov['method'] == row['method'] and prov['command'] == row['command'], 'method/command mismatch')
        for r in evidence['archives']:
            require(sha(reader(r['path'])) == r['sha256'], 'archive hash mismatch')
    require(m['tool_evidence']['version'] == evidence['runs'][6]['tool_version'], 'manifest tool version mismatch')
    target = 'manifests/baselines/uav-service-completion-r1.yaml'
    patch = 'diff --git a/' + target + ' b/' + target + '\nnew file mode 100644\n'
    patch += ''.join(difflib.unified_diff([], reader(PACKET + '/proposed-baseline.yaml').decode().splitlines(True), fromfile='/dev/null', tofile='b/' + target))
    contract = 'manifests/collaboration-v2.yaml'
    before = reader(contract).decode()
    after = before + '\n' + reader(PACKET + '/proposed-selection.yaml').decode()
    patch += 'diff --git a/' + contract + ' b/' + contract + '\n'
    patch += ''.join(difflib.unified_diff(before.splitlines(True), after.splitlines(True), fromfile='a/' + contract, tofile='b/' + contract))
    require(reader(PACKET + '/proposed-operational.patch').decode() == patch, 'operational patch mismatch')
    require(json.loads(reader('manifests/current.json'))['baseline_manifest'] == 'manifests/baselines/reviewer-r1.yaml', 'baseline pointer substituted')
    if (ROOT / PACKET / 'check-results.json').exists():
        report = load(PACKET + '/check-results.json')
        for record in report['commands']:
            for stream in ['stdout', 'stderr']:
                require(sha(reader(record[stream])) == record[stream + '_sha256'], 'check log hash drift')
    if expensive and (ROOT / PACKET / 'artifact-hashes.json').exists():
        seal = load(PACKET + '/artifact-hashes.json')
        for name, digest in seal['files'].items():
            require(sha(reader(PACKET + '/' + name)) == digest, 'proposal artifact hash drift: ' + name)
    if expensive:
        require(not (ROOT / target).exists(), 'operational manifest installed without phase-two disposition')
        subprocess.run(['git', 'apply', '--check', str(HERE / 'proposed-operational.patch')], cwd=ROOT, check=True)
        generate = module('generate')
        for name, content in generate.outputs().items():
            require(reader(CANDIDATE + '/' + name) == content, 'generation drift: ' + name)
        saved = sys.modules.get('generate')
        sys.modules['generate'] = generate
        try:
            audited = module('audit').audit()
        finally:
            if saved is None:
                sys.modules.pop('generate', None)
            else:
                sys.modules['generate'] = saved
        require(audited['healthy_replay_states'] == 101, 'causal replay audit')
    return {'check': 'static_audit_ok', 'inputs': len(hashes['files']), 'processes': 51,
        'queries_without_verdict': 11, 'retained_native_cells': 9, 'new_native_runs': 0,
        'gate_1': 'pending_independent_decision', 'activation': 'pending',
        'source_tree_membership': 'checked_git_execution_history' if source_history else 'archive_identity_only_use_source_history_for_git_membership'}


def operational_reader():
    # Check installed patch exactly, then audit the immutable preparation snapshot.
    target = 'manifests/baselines/uav-service-completion-r1.yaml'
    require(read(target) == read(PACKET + '/proposed-baseline.yaml'), 'installed manifest differs from reviewed proposal')
    contract = 'manifests/collaboration-v2.yaml'
    original = git_blob(BASE, contract)
    require(read(contract) == original + b'\n' + read(PACKET + '/proposed-selection.yaml'), 'installed selection changes historical contract')
    return lambda p: original if p == contract else read(p)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-history', action='store_true', help='require original execution Git objects and validate archive tree membership')
    parser.add_argument('--operational', action='store_true', help='audit exact installed patch snapshot; does not validate or grant external activation')
    args = parser.parse_args()
    reader = operational_reader() if args.operational else read
    result = check(reader=reader, expensive=not args.operational, source_history=args.source_history)
    if args.operational:
        # Generation/archive audit remains read-only after installation.
        gen = module('generate')
        sys.modules['generate'] = gen
        module('audit').audit()
        result['activation'] = 'external_independent_decision_required_not_granted_by_static_check'
    print(json.dumps(result, sort_keys=True))
