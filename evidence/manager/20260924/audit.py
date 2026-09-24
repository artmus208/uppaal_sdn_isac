"""Read-only integrity check of copied native software-smoke evidence."""
import hashlib
import json
from pathlib import Path
HERE = Path(__file__).resolve().parent
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_text(encoding='utf-8'))
q = HERE/'native-002/queue'
smoke = read(HERE/'native-002/smoke.json')
assert smoke['manager_hash'] == sha(HERE.parents[2]/'src/uppaal_mcp/verification_manager.py')
assert smoke['smoke_script_hash'] == sha(HERE/'native-smoke.py')
for p in q.glob('attempts/*/hashes.json'):
    for name, expected in read(p).items(): assert sha(p.parent/name) == expected, name
    r = read(p.parent/'result.json')
    assert r['status'] == 'success' and r['model_hash'] == sha(q/'model.xml')
    task = r['run_id'].split('-')[0]
    assert r['query_hash'] == sha(q/f'query-{task}.q')
    expected = 'Formula is satisfied' if r['verdict']=='satisfied' else 'Formula is NOT satisfied'
    assert expected in (p.parent/'stdout.txt').read_text()
    assert r['tool_version'] == (q/'sessions'/r['session']/'version.stdout.txt').read_text()
    assert r['returncode'] == 0 and r['peak_rss_bytes'] > 0
assert len(list(q.glob('attempts/*/result.json'))) == 2
assert smoke['continuation_skipped_completed']
print('Native raw hashes, model/query hashes, version, verdicts and memory samples OK')
