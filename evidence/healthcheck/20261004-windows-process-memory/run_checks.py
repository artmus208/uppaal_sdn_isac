"""Immutable software/static check records; never invokes a licensed verifier."""
import argparse
import datetime
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

root = Path(__file__).resolve().parents[3]
ap = argparse.ArgumentParser()
ap.add_argument('--run-id', required=True)
ap.add_argument('--focused', action='store_true')
args = ap.parse_args()
if not args.run_id or Path(args.run_id).name != args.run_id:
    ap.error('run-id must be one path component')
out = Path(__file__).resolve().parent / args.run_id
out.mkdir(exist_ok=False)
env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1')
env['PATH'] = str(Path(sys.executable).parent) + os.pathsep + env.get('PATH', '')
checks = [('manager-tests', [sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-p', 'test_verification_manager.py', '-v'])]
if not args.focused:
    checks += [
        ('full-suite', [sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v']),
        ('coordination', [sys.executable, 'scripts/check_coordination.py']),
        ('hash-audit', [sys.executable, 'scripts/check_coordination.py', '--audit-hashes', '--commit', 'HEAD', '--output', str(out/'baseline-hashes.json')]),
        ('pip-check', [sys.executable, '-m', 'pip', 'check']),
        ('dependencies', [sys.executable, '-m', 'pip', 'freeze']),
        ('mcp-smoke', [sys.executable, '-c', 'from uppaal_mcp.server import build_mcp; print(type(build_mcp()).__name__)']),
        ('cli-smoke', [sys.executable, '-m', 'uppaal_mcp.cli', 'list-examples']),
    ]
paths = ['src/uppaal_mcp/verification_manager.py', 'src/uppaal_mcp/windows_process.py', 'tests/test_verification_manager.py']
record = dict(source_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip(),
              source_hashes={p: hashlib.sha256((root/p).read_bytes()).hexdigest() for p in paths},
              python=sys.version, executable=sys.executable, platform=platform.platform(), checks=[])
for name, command in checks:
    start = datetime.datetime.now(datetime.timezone.utc).isoformat()
    t = time.monotonic()
    try:
        r = subprocess.run(command, cwd=root, env=env, capture_output=True, timeout=600)
        code, stdout, stderr = r.returncode, r.stdout, r.stderr
    except subprocess.TimeoutExpired as exc:
        code, stdout, stderr = 'timeout', exc.stdout or b'', exc.stderr or b''
    (out/(name+'.stdout.txt')).write_bytes(stdout)
    (out/(name+'.stderr.txt')).write_bytes(stderr)
    record['checks'].append(dict(name=name, command=command, started_utc=start, elapsed_seconds=time.monotonic()-t, exit_code=code))
    (out/'checks.json').write_text(json.dumps(record, indent=2)+'\n', encoding='utf-8')
    print(name, code, flush=True)
sys.exit(0 if all(c['exit_code']==0 for c in record['checks']) else 1)
