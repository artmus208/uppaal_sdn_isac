"""Audit report-source provenance, captured logs, baseline failures and scope."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[3]
PACKET = Path(__file__).parent
BASE = 'f0fcd770e3e6b93f99868b9116e4f0929f60d0fa'
IMPLEMENTATION = '805e4dc5c23cf2f24beb64b139afe1249429600f'
SOURCE = ('src/uppaal_mcp/phy/reports.py', 'tests/test_phy_report_status.py')
UNCHANGED = ('tests/test_coordination.py', 'tests/test_family_baseline.py',
             'tests/test_sdn_layer.py', 'tests/test_verification_manager.py',
             'src/uppaal_mcp/verification_manager.py')


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    changed = set(git('diff', '--name-only', BASE).decode().splitlines())
    changed.update(git('ls-files', '--others', '--exclude-standard').decode().splitlines())
    prefix = PACKET.relative_to(ROOT).as_posix() + '/'
    outside = sorted(p for p in changed if p not in SOURCE and not p.startswith(prefix))
    if outside:
        raise ValueError('Outside scope: ' + repr(outside))
    current = {name: sha(git('show', IMPLEMENTATION + ':' + name)) for name in SOURCE}
    for name, expected in current.items():
        if sha((ROOT / name).read_bytes()) != expected:
            raise ValueError('Implementation drift: ' + name)
    logs_checked = 0
    for path in sorted(PACKET.glob('*/checks.json')):
        record = json.loads(path.read_bytes())
        expected = dict(current)
        if path.parent.name == 'before':
            expected[SOURCE[0]] = sha(git('show', BASE + ':' + SOURCE[0]))
        if record['source_hashes'] != expected:
            raise ValueError('Execution source mismatch: ' + str(path))
        for check in record['checks']:
            for log in check['logs'].values():
                if sha((path.parent / log['path']).read_bytes()) != log['sha256']:
                    raise ValueError('Log changed: ' + str(path.parent / log['path']))
                logs_checked += 1
    unchanged = {}
    for name in UNCHANGED:
        data = (ROOT / name).read_bytes()
        if data != git('show', BASE + ':' + name):
            raise ValueError('Base-failure input changed: ' + name)
        unchanged[name] = sha(data)
    print(json.dumps({'base': BASE, 'implementation': IMPLEMENTATION,
                      'head': git('rev-parse', 'HEAD').decode().strip(),
                      'changed_paths': sorted(changed), 'implementation_hashes': current,
                      'log_hashes_checked': logs_checked, 'unchanged_base_failure_inputs': unchanged}, indent=2))


if __name__ == '__main__':
    main()
