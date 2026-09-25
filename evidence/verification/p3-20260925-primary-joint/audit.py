"""Audit supplemental joint-primary probes without invoking verifyta."""
import hashlib, json, tarfile, tempfile
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[3]
RID = "p3-20260925-primary-joint-001"
RAW = ROOT / "evidence/verification/runs" / RID
MODEL_HASH = "592678ed678ce8f70cf278f542e48bd2bb739969b53a962423d3e63f91e3e1e2"

def check(raw):
    run=json.loads((raw/'run.json').read_text())
    results=json.loads((raw/'results.json').read_text())
    assert run['model_hash']==MODEL_HASH
    assert run['query_scope'].startswith('supplemental diagnostics')
    assert run['selected_property_ids']==['joint-prerequisites','standby-receiver','alternative-receiver']
    for result in results:
        assert result['model_hash']==MODEL_HASH and result['verdict'] is None or result['verdict']=='satisfied'
        assert (raw/result['query_path']).read_text()==result['formal_query']+'\n'
        assert hashlib.sha256((raw/result['query_path']).read_bytes()).hexdigest()==result['query_hash']
        assert result['status'] in ['success','timeout']
        if result['status']=='success':
            assert result['verdict']=='satisfied' and len(result['trace_paths'])==1
        else: assert result['verdict'] is None and result['trace_paths']==[]
    for line in (raw/'SHA256SUMS').read_text().splitlines():
        digest,name=line.split('  ',1); assert hashlib.sha256((raw/name).read_bytes()).hexdigest()==digest

if __name__=='__main__':
    check(RAW)
    print('Supplemental joint probe archive, query identity, verdict/status fields and raw hashes pass; no global conclusion.')
