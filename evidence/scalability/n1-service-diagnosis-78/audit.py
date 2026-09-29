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


def load_module(name):
    spec = importlib.util.spec_from_file_location(name, HERE / (name + '.py'))
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
    excludes = {'artifact-hashes.json', 'checks/package-audit.json'}
    hashes = {str(p.relative_to(HERE)): digest(p) for p in sorted(HERE.rglob('*'))
              if p.is_file() and str(p.relative_to(HERE)) not in excludes and '__pycache__' not in p.parts}
    report = {'evidence_kind': 'static_validation', 'model_checking_performed': False,
        'base_commit': BASE, 'n1_baseline_pins_match': True, 'model_templates': len(model['templates']),
        'historical_audit': history['summary'], 'proposed_queries_exact_and_location_refs_exist': True,
        'query_compilation_performed_by_this_audit': False,
        'current_campaign_audit': load_module('inspect_execution').inspect(), 'changed_paths': paths,
        'artifact_index_exclusions': sorted(excludes), 'hashed_artifacts': len(hashes)}
    if write:
        (HERE / 'artifact-hashes.json').write_text(json.dumps(hashes, indent=2, sort_keys=True) + '\n')
        # Include index and report themselves in the declared scope count.
        report['changed_paths'] = sorted(set(paths + [prefix + e for e in excludes]))
        (HERE / 'checks/package-audit.json').write_text(json.dumps(report, indent=2) + '\n')
    else:
        assert hashes == json.loads((HERE / 'artifact-hashes.json').read_text()), 'Artifact hash drift'
        assert report == json.loads((HERE / 'checks/package-audit.json').read_text()), 'Package audit drift'
    print(json.dumps({'static_audit': 'matched', 'model_checking_performed': False,
        'historical_service_attempts': history['summary']['service_attempts'],
        'hashed_artifacts': len(hashes), 'scoped_paths': len(report['changed_paths'])}))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true', help='Write only the derived package index/report')
    run(parser.parse_args().write)
