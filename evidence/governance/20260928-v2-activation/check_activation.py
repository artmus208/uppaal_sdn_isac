"""Reproduce the activation scope and frozen generation identity; not verification."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

import yaml
from uppaal_mcp.integrated.generator import generate

ROOT = Path(__file__).resolve().parents[3]
BASE = '09d5eac96128e9f90a428584dd661addb5488931'
EVIDENCE = 'evidence/governance/20260928-v2-activation/'
ALLOWED = {'AGENTS.md', 'CONTRIBUTING-v2.md', '.github/ISSUE_TEMPLATE/workstream.yml',
           '.github/PULL_REQUEST_TEMPLATE.md', 'manifests/current.json',
           'manifests/collaboration-v2.yaml', 'manifests/v2.md', 'manifests/v2-migration.md',
           'scripts/check_coordination.py', 'tests/test_coordination.py',
           'tests/test_coordination_activation.py'}


def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args])


def sha(data):
    return hashlib.sha256(data).hexdigest()


errors = []
changed = set(git('diff', '--name-only', BASE).decode().splitlines())
changed.update(git('ls-files', '--others', '--exclude-standard').decode().splitlines())
for path in changed:
    if path not in ALLOWED and not path.startswith(EVIDENCE):
        errors.append(f'outside issue scope: {path}')

preserved = {}
for path in ('CONTRIBUTING.md', 'manifests/v1.md', 'manifests/collaboration-v1.yaml',
             'manifests/baselines/reviewer-r1.yaml'):
    current = (ROOT / path).read_bytes()
    preserved[path] = sha(current)
    if current != git('show', f'{BASE}:{path}'):
        errors.append(f'historical input changed: {path}')

parsed = []
for path in ('manifests/collaboration-v2.yaml', 'manifests/collaboration-v1.yaml',
             'manifests/baselines/reviewer-r1.yaml', '.github/ISSUE_TEMPLATE/workstream.yml'):
    assert isinstance(yaml.safe_load((ROOT / path).read_text()), dict), path
    parsed.append(path)
config = json.loads((ROOT / 'manifests/current.json').read_text())
links = 0
for path in ('AGENTS.md', 'CONTRIBUTING-v2.md', 'manifests/v2.md', 'manifests/v2-migration.md',
             EVIDENCE + 'README.md'):
    for target in re.findall(r'\]\(([^)]+)\)', (ROOT / path).read_text()):
        if re.match(r'\w+://', target) or target.startswith('#'):
            continue
        links += 1
        if not (ROOT / path).parent.joinpath(target.split('#')[0]).exists():
            errors.append(f'missing link: {path}: {target}')

result = generate(ROOT)
frozen = ROOT / 'evidence/governance/20260906-baseline/gate1-20260923'
model_hash = sha(result.model_xml.encode())
query_hash = sha(result.queries.encode())
if result.model_xml.encode() != (frozen / 'model.xml').read_bytes():
    errors.append('regenerated model differs from frozen bytes')
if result.queries.encode() != (frozen / 'candidate-queries.q').read_bytes():
    errors.append('regenerated candidate queries differ from frozen bytes')
report = {'kind': 'activation_integrity_and_generation_identity_not_verification',
          'base_commit': BASE, 'checked_commit': git('rev-parse', 'HEAD').decode().strip(),
          'configured': config, 'activation_accepted_by_this_check': False,
          'changed_paths': sorted(changed), 'preserved_inputs_sha256': preserved,
          'yaml_parsed': parsed, 'local_links_checked': links,
          'reproduction': {'model_hash': model_hash, 'candidate_query_hash': query_hash,
                           'frozen_reference': str(frozen.relative_to(ROOT)),
                           'generator_hash': result.metadata['generator_hash'],
                           'operational_context': result.metadata['context_document_hashes']['AGENTS.md'],
                           'model_checking': 'not_run'},
          'errors': errors, 'result': 'pass' if not errors else 'fail'}
print(json.dumps(report, ensure_ascii=False, indent=2))
sys.exit(bool(errors))
