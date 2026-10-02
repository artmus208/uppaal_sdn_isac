"""Preserve exact static/software-check commands and logs; no native execution."""
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PACKET = HERE.relative_to(ROOT).as_posix()
C = 'evidence/instantiation/uav-service-completion-candidate'
PYTHON = sys.executable
commands = [
    ('candidate-generate', [PYTHON, '-B', C + '/generate.py', '--check']),
    ('candidate-audit', [PYTHON, '-B', C + '/audit.py']),
    ('baseline-audit', [PYTHON, '-B', PACKET + '/check.py', '--source-history']),
    ('negative-controls', [PYTHON, '-B', '-m', 'unittest', 'discover', '-s', PACKET, '-p', 'test_*.py', '-v']),
    ('candidate-controls', [PYTHON, '-B', '-m', 'unittest', 'discover', '-s', C, '-p', 'test_*.py', '-v']),
    ('repository-tests', [PYTHON, '-B', '-m', 'unittest', 'discover', '-s', 'tests', '-v']),
    ('coordination', [PYTHON, '-B', 'scripts/check_coordination.py']),
    ('historical-family', [PYTHON, '-B', 'scripts/check_family_baseline.py']),
    ('mcp-smoke', [PYTHON, '-B', '-c', 'from uppaal_mcp.server import build_mcp; print(type(build_mcp()).__name__)']),
    ('cli-examples', [PYTHON, '-B', '-m', 'uppaal_mcp.cli', 'list-examples']),
    ('patch-applicability', ['git', 'apply', '--check', PACKET + '/proposed-operational.patch']),
    ('whitespace', ['git', 'diff', '--check', '61386aa358805082b705dcd00c8cbfde5fb98248']),
]


def main():
    out = HERE / 'checks'
    out.mkdir(exist_ok=True)
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONPATH=str(ROOT / 'src'))
    records = []
    for name, command in commands:
        stdout = out / (name + '.stdout.txt')
        stderr = out / (name + '.stderr.txt')
        with stdout.open('wb') as o, stderr.open('wb') as e:
            try:
                result = subprocess.run(command, cwd=ROOT, env=env, stdout=o, stderr=e, timeout=90)
                code = result.returncode
            except subprocess.TimeoutExpired:
                e.write(b'\nStatic/software check exceeded 90s wrapper cap; result incomplete.\n')
                code = 124
        record = {'check': name, 'command': command, 'cwd': str(ROOT), 'exit_code': code,
            'stdout': stdout.relative_to(ROOT).as_posix(), 'stderr': stderr.relative_to(ROOT).as_posix(),
            'stdout_sha256': hashlib.sha256(stdout.read_bytes()).hexdigest(), 'stderr_sha256': hashlib.sha256(stderr.read_bytes()).hexdigest()}
        records.append(record)
        print(name, code, flush=True)
    report = {'evidence_class': 'static_validation_and_software_tests', 'python': sys.version, 'platform': platform.platform(),
        'environment': {'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONPATH': env['PYTHONPATH']}, 'commands': records,
        'native_uppaal_runs': 0, 'tool_version_probe': 'not_run; exact historical engine responses audited',
        'setup': 'Separate /tmp/uppaal-baseline-84-venv; offline dependencies via read-only site-packages from /tmp/uppaal-r07-80/.venv. Current checkout src explicitly precedes dependencies. No fresh network installation.'}
    (HERE / 'check-results.json').write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    return int(any(r['exit_code'] != 0 for r in records))


if __name__ == '__main__':
    raise SystemExit(main())
