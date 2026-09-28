#!/usr/bin/env python3
"""Reproduce generated artifacts from a committed Git archive, with no local inputs."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SCOPE = HERE.relative_to(ROOT)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to(HERE) or output.exists():
        parser.error('a new output inside the Issue write scope is required')
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    dirty = subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT, text=True).strip()
    if dirty:
        parser.error('commit source/artifacts first; clean tree required')
    # Full archive, not a copy of a working tree or a subset of guessed inputs.
    archive = subprocess.check_output(['git', 'archive', commit], cwd=ROOT)
    runtime = HERE / '.venv'
    runtime.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='reproduction-', dir=runtime) as folder:
        checkout = Path(folder)
        with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
            tar.extractall(checkout, filter='data') if sys.version_info >= (3, 12) else tar.extractall(checkout)
        package = checkout / SCOPE
        start = time.monotonic()
        generation = subprocess.run([sys.executable, '-B', str(package/'generate.py')], cwd=checkout, capture_output=True, text=True)
        seconds = time.monotonic() - start
        check = subprocess.run([sys.executable, '-B', str(package/'generate.py'), '--check'], cwd=checkout, capture_output=True, text=True)
        structural = subprocess.run([sys.executable, '-B', str(package/'check.py')], cwd=checkout, capture_output=True, text=True)
        hashes = {}
        for path in sorted((package/'generated').rglob('*')):
            if path.is_file():
                relative = path.relative_to(package)
                content = path.read_bytes()
                if content != (HERE/relative).read_bytes():
                    raise SystemExit(f'archive differs from checkout: {relative}')
                hashes[str(relative)] = hashlib.sha256(content).hexdigest()
        result = {'source_commit': commit, 'source_tree': 'clean Git archive; no untracked input',
                  'evidence_kind': 'static_validation', 'property_verdict': 'not_applicable',
                  'generation_wall_seconds': seconds, 'generated_hashes': hashes,
                  'commands': []}
        for label, run in [('generate', generation), ('generate --check', check), ('check', structural)]:
            result['commands'].append({'command': label, 'exit_code': run.returncode, 'stdout': run.stdout, 'stderr': run.stderr})
        result['status'] = 'success' if all(r.returncode == 0 for r in (generation, check, structural)) else 'error'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + '\n')
    print(result['status'], len(hashes), 'generated files reproduced; generation wall seconds:', seconds)
    if result['status'] != 'success':
        raise SystemExit(1)


if __name__ == '__main__':
    main()
