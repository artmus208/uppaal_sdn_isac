"""Read-only integrity/scope checks for the readiness report, not model checking."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = 'bb5741b45480944630e1116fb7435effb2026655'
SCOPE = HERE.relative_to(ROOT).as_posix() + '/'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def references(value):
    if isinstance(value, dict):
        if 'path' in value and 'sha256' in value:
            assert digest(ROOT / value['path']) == value['sha256'], value['path']
        for v in value.values():
            references(v)
    elif isinstance(value, list):
        for v in value:
            references(v)


def main():
    matrix = json.loads((HERE / 'readiness-matrix.json').read_bytes())
    assert len(matrix['rows']) == 14 and matrix['overall_readiness'] == 'blocked'
    assert not matrix['gate_1_accepted']
    for row in matrix['rows']:
        assert row['evidence'] and row['required_role'] and row['next_action']
    for name in ('readiness-matrix.json', 'proposed-baseline.json', 'scope-audit.json'):
        references(json.loads((HERE / name).read_bytes()))
    for path in HERE.glob('*.md'):
        for link in re.findall(r'\]\(([^)]+)\)', path.read_text()):
            if '://' not in link:
                assert (path.parent / link.split('#')[0]).exists(), (path, link)
    changed = subprocess.check_output(['git', 'diff', '--name-only', BASE, 'HEAD'], cwd=ROOT).decode().splitlines()
    assert all(p.startswith(SCOPE) for p in changed), changed
    subprocess.run(['git', 'diff', '--check', BASE + '...HEAD'], cwd=ROOT, check=True)
    run = HERE / 'gate1-readiness-001-20260909'
    checks = json.loads((run / 'checks.json').read_bytes())
    for command in checks['commands']:
        assert command['exit_code'] == 0
        for stream in ('stdout', 'stderr'):
            assert digest(run / command[stream + '_path']) == command[stream + '_sha256']
    comparison = json.loads((run / 'comparison.json').read_bytes())
    for record in comparison['source_records']:
        assert digest(ROOT / record['path']) == record['sha256']
        raw = subprocess.check_output(['git', 'show', f"{BASE}:{record['path']}"], cwd=ROOT)
        assert hashlib.sha256(raw).hexdigest() == record['sha256']
    # Final PR candidate and merged input have equal trees; independently read Git objects.
    tree = lambda c: subprocess.check_output(['git', 'rev-parse', c + '^{tree}'], cwd=ROOT).decode().strip()
    assert tree(BASE) == tree('4399fd6c25c10ef8f488bc0dca408fc191e34c5c')
    if (HERE / 'SHA256SUMS').exists():
        for line in (HERE / 'SHA256SUMS').read_text().splitlines():
            expected, path = line.split('  ', 1)
            assert digest(HERE / path) == expected, path
    print(json.dumps({'status': 'success', 'evidence_class': 'report_integrity_only',
                      'base_commit': BASE, 'inspected_head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip(),
                      'matrix_rows': 14, 'recorded_commands': len(checks['commands']),
                      'source_files': len(comparison['source_records']),
                      'changed_paths': len(changed), 'merged_base_tree': tree(BASE),
                      'command': [sys.executable, '-B', str(Path(__file__).resolve())],
                      'verification_status': 'not_run'}, indent=2))


if __name__ == '__main__':
    main()
