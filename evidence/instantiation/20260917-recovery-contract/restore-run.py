"""Restore a losslessly archived run into a new directory and check every hash.

python restore-run.py runs/recovery-35-20260919-003.tar.xz /tmp/recovery-review
Then unpack.py /tmp/recovery-review/recovery-35-20260919-003 restores XML/log/trace paths.
"""
import gzip
import hashlib
import io
import json
from pathlib import Path
import sys
import tarfile

archive, destination = Path(sys.argv[1]), Path(sys.argv[2])
destination.mkdir(parents=True, exist_ok=False)
with tarfile.open(archive, 'r:xz') as t:
    for member in t.getmembers():
        path = destination / member.name
        if not member.isfile() or not path.resolve().is_relative_to(destination.resolve()):
            raise ValueError('Unexpected archive entry: ' + member.name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(t.extractfile(member).read())
for manifest in destination.glob('*/compressed-artifacts.json'):
    directory = manifest.parent
    for r in json.loads(manifest.read_text()):
        raw = (directory / r['path']).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == r['sha256']
        packed = gzip.compress(raw, mtime=0)
        assert hashlib.sha256(packed).hexdigest() == r['gzip_sha256']
        (directory / r['gzip_path']).write_bytes(packed)
        (directory / r['path']).unlink()
    for line in (directory / 'SHA256SUMS').read_text().splitlines():
        h, name = line.split('  ', 1)
        assert hashlib.sha256((directory / name).read_bytes()).hexdigest() == h, name
    print('Restored every recorded byte/hash:', directory)
