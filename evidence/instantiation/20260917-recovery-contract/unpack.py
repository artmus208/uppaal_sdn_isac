"""Restore exact verifier inputs/traces in a COPY of a run directory."""
import gzip
import hashlib
import json
from pathlib import Path
import sys
p = Path(sys.argv[1])
for r in json.loads((p / 'compressed-artifacts.json').read_text()):
    compressed = (p / r['gzip_path']).read_bytes()
    assert hashlib.sha256(compressed).hexdigest() == r['gzip_sha256']
    raw = gzip.decompress(compressed)
    assert hashlib.sha256(raw).hexdigest() == r['sha256']
    dest = p / r['path']
    if dest.exists():
        assert dest.read_bytes() == raw
    else:
        dest.write_bytes(raw)
print('Restored and hash-checked exact XML/trace bytes.')
