"""Read-only audit of the proposed Gate 1 manifest and stored artifacts."""
import importlib.util,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('historical_auditor',HERE.parent/'audit_hashes.py')
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
a.MANIFEST=(HERE/'proposed-baseline.yaml').relative_to(ROOT).as_posix()
if __name__=='__main__':
    result=a.audit(ROOT)
    import yaml
    m=yaml.safe_load((HERE/'proposed-baseline.yaml').read_bytes())
    assert not m['metadata']['frozen'] and not m['gate_1']['passed']
    assert m['gate_1']['P1_accepted'] and m['gate_1']['P2_accepted']
    selected=json.loads((HERE/'selected-queries.json').read_text())
    assert len(selected)==15 and all(x['verdict'] is None for x in selected)
    print(json.dumps(result,ensure_ascii=False,indent=2))
    sys.exit(result['hash_status']!='match')
