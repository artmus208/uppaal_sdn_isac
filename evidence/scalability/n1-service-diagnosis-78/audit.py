#!/usr/bin/env python3
"""Audit this diagnostic package without running UPPAAL or altering its inputs."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = '8237e8c2bec41aa1bb943cc33be1ac9586d03759'
HISTORICAL = 'b403fd3903b1d9f925cb51382ba5433810612f99'


def load_module(name):
    spec = importlib.util.spec_from_file_location(Path(name).name, HERE / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(write=False):
    model = load_module('inspect_model').extract(ROOT)
    assert model == json.loads((HERE / 'model-inventory.json').read_text())
    history = load_module('inspect_history').extract(ROOT)
    assert history == json.loads((HERE / 'history.json').read_text())
    protocol = json.loads((HERE / 'protocol.json').read_text())
    assert protocol['executed'] is False
    assert protocol['authorization'] == 'pending_explicit_user_confirmation'
    assert protocol['model_hash'] == model['model_hash']
    assert digest(ROOT / protocol['monitor']) == protocol['monitor_hash']
    assert len(protocol['queries']) == protocol['maximum_scientific_invocations'] == 3
    expected = [
        'E<> u0_mac_A_SCH_0.SelectMode',
        'E<> (shared_load.Sample_1 && u0_mac_queue_q > 0 && u0_mac_queue_q <= u0_mac_queue_K && (u0_mac_scheduleMode == u0_mac_SCH_COMM || u0_mac_scheduleMode == u0_mac_SCH_JOINT))',
        'E<> (shared_load.Publish_0 && family_grant_0 && !u0_mac_queue_overflow_seen)',
    ]
    bindings = dict(re.findall(r'(\w+)\s*=\s*(\w+)\(\);', model['system']))
    templates = {t['name']: {l['name'] for l in t['locations']} for t in model['templates']}
    for row, formula in zip(protocol['queries'], expected):
        assert row['query'] == formula
        path = ROOT / row['path']
        assert path.read_bytes() == (formula + '\n').encode()
        assert digest(path) == row['sha256']
        for proc, loc in re.findall(r'(\w+)\.(\w+)', formula):
            assert loc in templates[bindings[proc]], (proc, loc)
    prefix = str(HERE.relative_to(ROOT)) + '/'
    changed = subprocess.check_output(['git', 'diff', '--name-only', BASE], cwd=ROOT, text=True).splitlines()
    untracked = subprocess.check_output(['git', 'ls-files', '--others', '--exclude-standard'], cwd=ROOT, text=True).splitlines()
    paths = sorted(set(changed + untracked))
    assert paths and all(p.startswith(prefix) for p in paths), 'Out-of-scope change'
    # Historical indexes remain immutable. Only the entry-point documentation and
    # this script changed; audit their old bytes against the pinned Git snapshot.
    historical = json.loads((HERE / 'artifact-hashes.json').read_text())
    for name, expected_hash in historical.items():
        if name in {'README.md', 'audit.py'}:
            raw = subprocess.check_output(
                ['git', 'show', HISTORICAL + ':' + prefix + name], cwd=ROOT)
            actual_hash = hashlib.sha256(raw).hexdigest()
        else:
            actual_hash = digest(HERE / name)
        assert actual_hash == expected_hash, 'Historical artifact hash drift: ' + name
    replay = load_module('replay-001/inspect_replay').audit()
    excludes = {'current-artifact-hashes.json', 'checks/current-package-audit.json'}
    hashes = {str(p.relative_to(HERE)): digest(p) for p in sorted(HERE.rglob('*'))
              if p.is_file() and str(p.relative_to(HERE)) not in excludes and '__pycache__' not in p.parts}
    report = {'evidence_kind': 'static_validation', 'model_checking_performed': False,
        'base_commit': BASE, 'n1_baseline_pins_match': True, 'model_templates': len(model['templates']),
        'historical_audit': history['summary'], 'proposed_queries_exact_and_location_refs_exist': True,
        'query_compilation_performed_by_this_audit': False,
        'current_campaign_audit': load_module('inspect_execution').inspect(),
        'replay_audit': replay, 'historical_package_commit': HISTORICAL,
        'changed_paths': sorted(set(paths + [prefix + e for e in excludes])),
        'artifact_index_exclusions': sorted(excludes), 'hashed_artifacts': len(hashes)}
    if write:
        (HERE / 'current-artifact-hashes.json').write_text(json.dumps(hashes, indent=2, sort_keys=True) + '\n')
        (HERE / 'checks/current-package-audit.json').write_text(json.dumps(report, indent=2) + '\n')
    else:
        assert hashes == json.loads((HERE / 'current-artifact-hashes.json').read_text()), 'Artifact hash drift'
        assert report == json.loads((HERE / 'checks/current-package-audit.json').read_text()), 'Package audit drift'
    print(json.dumps({'static_audit': 'matched', 'model_checking_performed': False,
        'historical_service_attempts': history['summary']['service_attempts'],
        'hashed_artifacts': len(hashes), 'scoped_paths': len(report['changed_paths']),
        'replay_status': replay['status'], 'property_verdict': None}))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true', help='Write only current-artifact-hashes.json and checks/current-package-audit.json')
    run(parser.parse_args().write)
