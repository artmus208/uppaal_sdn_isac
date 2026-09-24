"""Audit immutable run bytes and the controlled single-invariant mutation."""
import hashlib, json, sys
from pathlib import Path
import xml.etree.ElementTree as E
import build
p = Path(__file__).resolve().parent
root = p.parents[2]
d = Path(sys.argv[1])
for name, data in build.generate().items(): assert (p/name).read_bytes() == data
r = E.parse(p/'model.xml')
loc = r.find(".//location[@id='wait']")
loc.remove(loc.find("label[@kind='invariant']"))
assert E.canonicalize(E.tostring(r.getroot(), encoding='unicode'), strip_text=True) == E.canonicalize((p/'negative-control.xml').read_text(), strip_text=True)
for line in (d/'SHA256SUMS').read_text().splitlines():
    h, n = line.split('  ', 1)
    assert hashlib.sha256((d/n).read_bytes()).hexdigest() == h, n
results = json.loads((d/'results.json').read_text())
assert len(results) == 4
for v in results:
    assert v['status'] == 'success' and v['verdict'] == v['expected_verdict']
    assert hashlib.sha256((root/v['model_path']).read_bytes()).hexdigest() == v['model_hash']
    assert hashlib.sha256((v['query']+'\n').encode()).hexdigest() == v['query_hash']
    assert 'Formula is '+('NOT satisfied' if v['verdict']=='violated' else 'satisfied') in (d/v['stdout_reference']).read_text()
    assert v['tool_version'] == (d/'version.stdout.txt').read_bytes().decode()
    assert v['source_commit'] == json.loads((d/'run.json').read_text())['source_commit']
    print(v['run_id'], v['status'], v['verdict'], v['runtime_seconds'])
print('Raw hashes, verdicts, model/query identity and single-invariant negative control OK')
