"""Record local software/static checks without native verifier calls."""
import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--repo', required=True, type=Path)
    p.add_argument('--git', required=True, type=Path)
    args = p.parse_args()
    here = Path(__file__).resolve().parent
    logs = here / 'checks'
    logs.mkdir(exist_ok=True)
    env = os.environ.copy()
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    env['PATH'] = str(args.git.parent) + os.pathsep + str(Path(sys.executable).parent) + os.pathsep + env['PATH']
    commands = [
        ('environment', [sys.executable, '-c', 'import sys,platform,importlib.metadata as m; print(sys.version); print(platform.platform()); print("mcp",m.version("mcp")); print("PyYAML",m.version("PyYAML")); import uppaal_mcp; print(uppaal_mcp.__file__)']),
        ('dependencies', [sys.executable, '-m', 'pip', 'check']),
        ('scope-status', [str(args.git), 'status', '--short', '--branch']),
        ('premises', [sys.executable, str(here/'check.py'), '--repo', str(args.repo), '--output', str(logs/'reproduced-certificate.json'), '--reduced', str(logs/'reproduced-model.xml')]),
        ('scoped-tests', [sys.executable, str(here/'tests.py'), '--repo', str(args.repo), '-v']),
        ('coordination', [sys.executable, 'scripts/check_coordination.py']),
        ('baseline-hashes', [sys.executable, 'scripts/check_coordination.py', '--audit-hashes', '--commit', 'HEAD', '--output', str(logs/'baseline-hashes.json')]),
        ('mcp-smoke', [sys.executable, '-c', 'from uppaal_mcp.server import build_mcp; print(type(build_mcp()).__name__)']),
        ('cli-smoke', [sys.executable, '-m', 'uppaal_mcp.cli', 'list-examples']),
        ('repository-tests', [sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v']),
        ('whitespace', [str(args.git), 'diff', '--check']),
    ]
    results = {'evidence_kind': 'software_and_static_validation', 'licensed_execution': 'not_performed',
               'source_commit': subprocess.check_output([str(args.git), 'rev-parse', 'HEAD'], cwd=args.repo, env=env).decode().strip(),
               'environment': {'os': platform.platform(), 'python': sys.version}, 'commands': []}
    for name, argv in commands:
        print('Running ' + name, flush=True)
        started = time.monotonic()
        try:
            r = subprocess.run(argv, cwd=args.repo, env=env, capture_output=True, timeout=600)
            stdout, stderr, code = r.stdout, r.stderr, r.returncode
        except subprocess.TimeoutExpired as e:
            stdout, stderr, code = e.stdout or b'', (e.stderr or b'') + b'\nSOFTWARE CHECK TIMEOUT\n', 124
        paths = []
        for suffix, data in [('stdout', stdout), ('stderr', stderr)]:
            path = logs / (name + '.' + suffix + '.txt')
            path.write_bytes(data)
            paths.append({'path': str(path.relative_to(here)), 'sha256': hashlib.sha256(data).hexdigest()})
        results['commands'].append({'name': name, 'argv': argv, 'cwd': str(args.repo),
                                    'exit_code': code, 'elapsed_seconds': time.monotonic()-started, 'logs': paths})
        (logs/'results.json').write_text(json.dumps(results, indent=2)+'\n', encoding='utf-8')
        print(name + ': exit ' + str(code), flush=True)
    for original, reproduced in [('certificate.json', 'reproduced-certificate.json'), ('observer-erased.xml', 'reproduced-model.xml')]:
        match = (here/original).read_bytes() == (logs/reproduced).read_bytes()
        results.setdefault('reproduction', {})[original] = match
    (logs/'results.json').write_text(json.dumps(results, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'exit_codes': {r['name']:r['exit_code'] for r in results['commands']},
                      'reproduction':results['reproduction']}), flush=True)
    return int(any(r['exit_code'] for r in results['commands']) or not all(results['reproduction'].values()))


if __name__ == '__main__':
    raise SystemExit(main())
