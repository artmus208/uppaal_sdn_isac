"""Check this packet's log hashes, write scope and unchanged read-only inputs."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[3]
PACKET = Path(__file__).parent
BASE = 'f0fcd770e3e6b93f99868b9116e4f0929f60d0fa'
SCOPE = {'tests/test_family_baseline.py', 'tests/test_sdn_layer.py'}


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)


def main():
    changed = set(git('diff', '--name-only', BASE).decode().splitlines())
    changed.update(git('ls-files', '--others', '--exclude-standard').decode().splitlines())
    prefix = PACKET.relative_to(ROOT).as_posix() + '/'
    outside = sorted(p for p in changed if p not in SCOPE and not p.startswith(prefix))
    if outside:
        raise ValueError('Outside scope: ' + repr(outside))
    checked = 0
    for path in sorted((PACKET / 'checks').glob('*.json')):
        for log in json.loads(path.read_bytes()).get('logs', {}).values():
            data = (path.parent / log['path']).read_bytes()
            if len(data) != log['bytes'] or hashlib.sha256(data).hexdigest() != log['sha256']:
                raise ValueError('Log integrity mismatch: ' + log['path'])
            checked += 1
    unchanged = {}
    for name in ('tests/test_coordination.py', 'src/uppaal_mcp/verification_manager.py',
                 'tests/test_verification_manager.py'):
        data = (ROOT / name).read_bytes()
        if data != git('show', BASE + ':' + name):
            raise ValueError('Read-only input changed: ' + name)
        unchanged[name] = hashlib.sha256(data).hexdigest()
    print(json.dumps({'base': BASE, 'head': git('rev-parse', 'HEAD').decode().strip(),
                      'changed_paths': sorted(changed), 'log_hashes_checked': checked,
                      'read_only_files_identical_to_base': unchanged}, indent=2))


if __name__ == '__main__':
    main()
