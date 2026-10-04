"""Reproduce software checks; --output must be new, --full includes the full suite."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
SOURCE_PATHS = ('src/uppaal_mcp/phy/reports.py', 'tests/test_phy_report_status.py')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--full', action='store_true')
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    env = dict(os.environ, PYTHONUTF8='1', PYTHONDONTWRITEBYTECODE='1')
    commands = [('focused', [sys.executable, '-m', 'unittest', 'discover', '-s', 'tests',
                              '-p', 'test_phy_report_status.py', '-v'])]
    if args.full:
        commands.extend([
            ('full-suite', [sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v']),
            ('coordination', [sys.executable, 'scripts/check_coordination.py']),
            ('baseline-hashes', [sys.executable, 'scripts/check_coordination.py', '--audit-hashes',
                                 '--commit', 'HEAD', '--output', str(output / 'baseline-audit.json')]),
            ('pip-check', [sys.executable, '-m', 'pip', 'check']),
            ('mcp-smoke', [sys.executable, '-c', 'from uppaal_mcp.server import build_mcp; print(type(build_mcp()).__name__)']),
            ('cli-smoke', [sys.executable, '-m', 'uppaal_mcp.cli', 'list-examples']),
        ])
    record = {
        'source_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        'working_tree': subprocess.check_output(['git', 'status', '--short'], cwd=ROOT, text=True),
        'source_hashes': {name: sha((ROOT / name).read_bytes()) for name in SOURCE_PATHS},
        'python': sys.version, 'cwd': str(ROOT),
        'environment': {'PYTHONUTF8': '1', 'PYTHONDONTWRITEBYTECODE': '1'},
        'checks': [],
    }
    for label, command in commands:
        started = datetime.now(timezone.utc).isoformat()
        tick = time.monotonic()
        try:
            result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, timeout=180)
            code, stdout, stderr = result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired as exc:
            code, stdout, stderr = 124, exc.stdout or b'', exc.stderr or b''
        logs = {}
        for stream, raw in (('stdout', stdout), ('stderr', stderr)):
            data = raw.replace(b'\r\n', b'\n')
            path = output / (label + '.' + stream + '.txt')
            path.write_bytes(data)
            logs[stream] = {'path': path.name, 'sha256': sha(data), 'original_sha256': sha(raw)}
        check = {'label': label, 'command': command, 'exit_code': code, 'started_at': started,
                 'duration_seconds': round(time.monotonic() - tick, 3), 'timeout_seconds': 180, 'logs': logs}
        record['checks'].append(check)
        (output / 'checks.json').write_bytes((json.dumps(record, indent=2) + '\n').encode())
        print(json.dumps({key: check[key] for key in ('label', 'exit_code', 'duration_seconds')}), flush=True)
    return int(any(check['exit_code'] for check in record['checks']))


if __name__ == '__main__':
    raise SystemExit(main())
