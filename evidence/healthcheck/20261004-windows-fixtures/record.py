"""Record a bounded software check: python record.py LABEL COMMAND [ARG ...]."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[3]
CHECKS = Path(__file__).parent / 'checks'


def main():
    label, *command = sys.argv[1:]
    if not command or Path(label).name != label:
        raise ValueError('Expected a simple label and a command')
    CHECKS.mkdir(exist_ok=True)
    destination = CHECKS / (label + '.json')
    if any(CHECKS.glob(label + '.*')):
        raise FileExistsError(label)
    env = dict(os.environ, PYTHONUTF8='1', PYTHONDONTWRITEBYTECODE='1')
    started = datetime.now(timezone.utc).isoformat()
    tick = time.monotonic()
    timed_out = False
    try:
        result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, timeout=180)
        code, stdout, stderr = result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        code, stdout, stderr = 124, exc.stdout or b'', exc.stderr or b''
    logs = {}
    for stream, raw in (('stdout', stdout), ('stderr', stderr)):
        # Store readable LF logs, with original and stored byte hashes recorded.
        data = raw.replace(b'\r\n', b'\n')
        path = CHECKS / (label + '.' + stream + '.txt')
        path.write_bytes(data)
        logs[stream] = {'path': path.name, 'bytes': len(data),
                        'sha256': hashlib.sha256(data).hexdigest(),
                        'original_sha256': hashlib.sha256(raw).hexdigest()}
    record = {
        'command': command, 'cwd': str(ROOT), 'started_at': started,
        'duration_seconds': round(time.monotonic() - tick, 3),
        'exit_code': code, 'timeout': timed_out, 'timeout_seconds': 180,
        'source_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        'working_tree': subprocess.check_output(['git', 'status', '--short'], cwd=ROOT, text=True),
        'python': sys.version, 'environment': {'PYTHONUTF8': '1', 'PYTHONDONTWRITEBYTECODE': '1'},
        'logs': logs,
    }
    destination.write_bytes((json.dumps(record, indent=2) + '\n').encode('utf-8'))
    print(json.dumps({'check': label, 'exit_code': code, 'duration_seconds': record['duration_seconds']}))
    return code


if __name__ == '__main__':
    raise SystemExit(main())
