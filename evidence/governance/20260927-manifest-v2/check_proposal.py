"""Read-only integrity audit of the Issue #62 proposal, not scientific verification."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

import yaml

ROOT = Path(__file__).resolve().parents[3]
BASE = 'fef5e9f71d58803727a63efc36ab944e08655a31'
DOCS = ('manifests/v2.md', 'manifests/v2-migration.md')
EVIDENCE = 'evidence/governance/20260927-manifest-v2/'
errors = []

def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args])

changed = set(git('diff', '--name-only', BASE).decode().splitlines())
changed.update(git('ls-files', '--others', '--exclude-standard').decode().splitlines())
outside = sorted(p for p in changed if p not in DOCS and not p.startswith(EVIDENCE))
if outside:
    errors.append({'outside_scope': outside})

contract = yaml.safe_load((ROOT / 'manifests/collaboration-v1.yaml').read_text())
expected = {}
for owner, spec in contract['workstreams'].items():
    for ident in spec.get('atomic_comment_ids', []):
        if re.fullmatch(r'[CRVI]\d{2}', ident):
            expected[ident] = owner
expected['D01'] = 'P9b (условно)'
rows = re.findall(r'^\| ([CRVID]\d{2}) \| ([^|]+) \|', (ROOT / DOCS[1]).read_text(), re.M)
actual = {ident: owner.strip() for ident, owner in rows}
if len(rows) != 25 or len(actual) != 25 or actual != expected:
    errors.append({'ownership_mismatch': {'actual': actual, 'expected': expected}})

local_links = 0
for rel in DOCS:
    path = ROOT / rel
    text = path.read_text()
    if 'proposal / not active' not in text:
        errors.append({'missing_proposal_marker': rel})
    for target in re.findall(r'\]\(([^)]+)\)', text):
        if re.match(r'\w+://', target) or target.startswith('#'):
            continue
        local_links += 1
        if not (path.parent / target.split('#')[0]).exists():
            errors.append({'missing_local_link': [rel, target]})

pins = {}
for rel in ('manifests/v1.md', 'manifests/collaboration-v1.yaml',
            'manifests/baselines/reviewer-r1.yaml', 'AGENTS.md', 'CONTRIBUTING.md',
            'src/uppaal_mcp/integrated/inputs.py', 'scripts/check_coordination.py',
            'tests/test_coordination.py'):
    current = (ROOT / rel).read_bytes()
    if current != git('show', f'{BASE}:{rel}'):
        errors.append({'historical_input_changed': rel})
    pins[rel] = hashlib.sha256(current).hexdigest()

print(json.dumps({'kind': 'proposal_integrity_audit_not_verification',
                  'base_commit': BASE, 'checked_head': git('rev-parse', 'HEAD').decode().strip(),
                  'changed_paths': sorted(changed), 'atomic_ids': len(rows),
                  'local_links_checked': local_links, 'preserved_inputs_sha256': pins,
                  'errors': errors, 'result': 'pass' if not errors else 'fail'},
                 ensure_ascii=False, indent=2))
sys.exit(bool(errors))
