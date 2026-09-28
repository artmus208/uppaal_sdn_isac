#!/usr/bin/env python3
"""Losslessly compress large raw compiler output; preserve hashes of original bytes."""
import gzip
import json
from pathlib import Path
import generate as g

for folder in sorted((g.HERE/'checks').glob('uppaal-*')):
    record=folder/'runs.json'
    if not record.exists(): continue
    runs=json.loads(record.read_text())
    for run in runs:
        for stream in ('stdout','stderr'):
            key=stream+'_reference'; p=g.HERE/run[key]
            if p.suffix=='.gz' or p.stat().st_size<100000: continue
            raw=p.read_bytes()
            if g.sha(raw)!=run[stream+'_hash']: raise ValueError('Raw log changed')
            packed=p.with_suffix(p.suffix+'.gz')
            packed.write_bytes(gzip.compress(raw,mtime=0))
            run[key]=str(packed.relative_to(g.HERE))
            run[stream+'_storage_encoding']='gzip'
            run[stream+'_hash_basis']='uncompressed raw bytes'
            run[stream+'_storage_hash']=g.sha(packed.read_bytes())
            p.unlink()
    record.write_bytes(g.encoded(runs))
