"""Record integration software/static checks; never invokes verifyta."""
import datetime
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent / ('windows' if os.name == 'nt' else 'linux')
OUT.mkdir(exist_ok=True)
env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1')
env['PATH'] = str(Path(sys.executable).parent) + os.pathsep + env.get('PATH', '')
checks = [
    ('environment', [sys.executable, '-c', 'import platform,sys; print(sys.version); print(platform.platform()); print(sys.executable)']),
    ('dependencies', [sys.executable, '-m', 'pip', 'freeze']),
    ('pip-check', [sys.executable, '-m', 'pip', 'check']),
    ('coordination', [sys.executable, 'scripts/check_coordination.py']),
    ('hash-audit', [sys.executable, 'scripts/check_coordination.py', '--audit-hashes', '--commit', 'HEAD', '--output', str(OUT/'baseline-hashes.json')]),
    ('full-suite', [sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v']),
    ('mcp-smoke', [sys.executable, '-c', 'from uppaal_mcp.server import build_mcp; print(type(build_mcp()).__name__)']),
    ('cli-smoke', [sys.executable, '-m', 'uppaal_mcp.cli', 'list-examples']),
    ('completion-premises', [sys.executable, '-B', 'evidence/verification/20261004-completion-safety-proof/check.py', '--check']),
    ('completion-tests', [sys.executable, '-B', 'evidence/verification/20261004-completion-safety-proof/tests.py']),
    ('completion-history', [sys.executable, '-B', 'evidence/verification/20261004-completion-safety-proof/audit_history.py', '--check']),
    ('capacity-premises', [sys.executable, 'evidence/scalability/20261004-r04-compositional-proof/check_proof.py']),
    ('capacity-tests', [sys.executable, '-m', 'unittest', 'discover', '-s', 'evidence/scalability/20261004-r04-compositional-proof', '-p', 'test_proof.py', '-v']),
]
records = []
for name, cmd in checks:
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    t = time.monotonic()
    try:
        result = subprocess.run(cmd, cwd=ROOT, env=env, capture_output=True, timeout=240)
        code, stdout, stderr = result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired as exc:
        code, stdout, stderr = 'timeout', exc.stdout or b'', exc.stderr or b''
    (OUT/(name+'.stdout.txt')).write_bytes(stdout)
    (OUT/(name+'.stderr.txt')).write_bytes(stderr)
    records.append(dict(name=name, command=cmd, started_utc=started, duration_seconds=time.monotonic()-t, exit_code=code))
    (OUT/'checks.json').write_text(json.dumps(dict(source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(), platform=platform.platform(), checks=records), indent=2)+'\n',encoding='utf-8')
    print(name, code, flush=True)
