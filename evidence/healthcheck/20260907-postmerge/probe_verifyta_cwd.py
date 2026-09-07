"""Probe the same verifier with a Windows-backed working directory."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import time
import sys

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--cwd', type=Path)
parser.add_argument('--cli', action='store_true')
args = parser.parse_args()
args.output.mkdir(parents=True, exist_ok=False)
exe = Path('/mnt/c/Program Files (x86)/UPPAAL-5.0.0/bin/verifyta.exe')
command = [str(Path(sys.executable).parent / 'uppaal-verifyta'), 'version'] if args.cli else [str(exe), '--version']
probe_cwd = args.cwd or exe.parent
start = time.monotonic()
try:
    result = subprocess.run(command, cwd=probe_cwd, capture_output=True, timeout=20)
    code, stdout, stderr = result.returncode, result.stdout, result.stderr
except subprocess.TimeoutExpired as error:
    code, stdout, stderr = 'timeout', error.stdout or b'', error.stderr or b''
logs = {}
for name, data in [('stdout', stdout), ('stderr', stderr)]:
    (args.output / f'{name}.txt').write_bytes(data)
    logs[name] = {'path': f'{name}.txt', 'sha256': hashlib.sha256(data).hexdigest()}
metadata = {'command': command, 'cwd': str(probe_cwd), 'timeout_sec': 20,
            'exit_code': code, 'executable_sha256': hashlib.sha256(exe.read_bytes()).hexdigest(),
            'runtime_seconds': time.monotonic() - start,
            'recorded_at_utc': datetime.now(timezone.utc).isoformat(),
            'environment_label': 'wsl-unrestricted', **logs}
(args.output / 'results.json').write_text(json.dumps(metadata, indent=2) + '\n')
print(json.dumps(metadata, indent=2))
