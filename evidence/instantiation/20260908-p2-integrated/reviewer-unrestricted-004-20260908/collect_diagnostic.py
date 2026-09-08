"""Record checkpoint drift and historical log integrity without changing pins."""
import hashlib
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
OLD = HERE.parent / 'reviewer-run-003'

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)

inventory = json.loads((ROOT / 'evidence/instantiation/20260907-p2-scope/inventory.json').read_bytes())
drift = []
for name, record in inventory['sources'].items():
    actual = sha((ROOT / name).read_bytes())
    if actual != record['sha256']:
        drift.append({'path': name, 'expected': record['sha256'], 'actual': actual})
old = json.loads((OLD / 'checks.json').read_bytes())
log_checks = []
for command in old['commands']:
    for stream in ('stdout', 'stderr'):
        name = command[stream + '_path']
        log_checks.append({'path': name, 'matches': sha((OLD / name).read_bytes()) == command[stream + '_sha256']})
for record_name in ('focused', 'audit'):
    record = json.loads((OLD / (record_name + '.json')).read_bytes())
    for stream in ('stdout', 'stderr'):
        name = record_name + '.' + stream + '.log'
        log_checks.append({'path': name, 'matches': sha((OLD / name).read_bytes()) == record[stream + '_sha256']})
paths = git('diff', '--name-only', 'origin/read...HEAD').decode().splitlines()
outside = [p for p in paths if not (p.startswith('src/uppaal_mcp/integrated/') or p == 'tests/test_sdn_layer.py' or p.startswith('evidence/instantiation/20260908-p2-integrated/'))]
report = {
    'source_commit': git('rev-parse', 'HEAD').decode().strip(),
    'comparison_source_commit': old['source_commit'],
    'implementation_and_tests_unchanged': not git('diff', old['source_commit'], 'HEAD', '--', 'src/uppaal_mcp/integrated', 'tests/test_sdn_layer.py'),
    'pinned_source_drift': drift,
    'historical_raw_log_checks': log_checks,
    'read_commit': git('rev-parse', 'origin/read').decode().strip(),
    'out_of_scope_paths': outside,
    'model_checking': 'not_run',
}
(HERE / 'provenance-audit.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({k: v for k, v in report.items() if k != 'historical_raw_log_checks'}, indent=2))
assert all(item['matches'] for item in log_checks)
