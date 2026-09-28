#!/usr/bin/env python3
"""Validate the published artifact index and lossless raw-log storage."""
import gzip
import json
from pathlib import Path
import generate as g


def main():
    index=json.loads((g.HERE/'artifacts-sha256.json').read_text())
    for name,digest in index['files'].items():
        if g.sha((g.HERE/name).read_bytes())!=digest: raise ValueError('Artifact hash mismatch: '+name)
    count=0
    for path in sorted((g.HERE/'checks').glob('uppaal-*/runs.json')):
        for run in json.loads(path.read_text()):
            for stream in ('stdout','stderr'):
                p=g.HERE/run[stream+'_reference']; raw=p.read_bytes()
                if run.get(stream+'_storage_encoding')=='gzip':
                    if g.sha(raw)!=run[stream+'_storage_hash']: raise ValueError('Stored gzip hash mismatch')
                    raw=gzip.decompress(raw)
                if g.sha(raw)!=run[stream+'_hash']: raise ValueError('Raw log hash mismatch: '+str(p))
            count+=1
    print(f'{len(index["files"])} artifact hashes and {count} raw run log pairs match; static integrity only.')


if __name__=='__main__': main()
