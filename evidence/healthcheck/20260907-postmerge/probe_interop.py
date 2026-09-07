"""Read-only Windows interop probe, independent of UPPAAL licensing."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import time

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
args.output.mkdir(parents=True, exist_ok=False)
command = ['/mnt/c/Windows/System32/cmd.exe', '/d', '/c', 'ver']
start = time.monotonic()
try:
    result = subprocess.run(command, capture_output=True, timeout=15)
    code, stdout, stderr = result.returncode, result.stdout, result.stderr
except subprocess.TimeoutExpired as error:
    code, stdout, stderr = 'timeout', error.stdout or b'', error.stderr or b''
logs = {}
for name, data in [('stdout', stdout), ('stderr', stderr)]:
    (args.output / f'{name}.txt').write_bytes(data)
    logs[name] = {'path': f'{name}.txt', 'sha256': hashlib.sha256(data).hexdigest()}
metadata = {'command': command, 'timeout_sec': 15, 'exit_code': code,
            'runtime_seconds': time.monotonic() - start,
            'recorded_at_utc': datetime.now(timezone.utc).isoformat(),
            'environment_label': 'wsl-unrestricted', **logs}
(args.output / 'results.json').write_text(json.dumps(metadata, indent=2) + '\n')
print(json.dumps(metadata, indent=2))
