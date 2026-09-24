"""Audit saved P3 evidence; no verifier execution and no independent approval."""
import hashlib,json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sha=lambda b:hashlib.sha256(b).hexdigest()
def audit(out):
 run=json.loads((out/'run.json').read_text());results=json.loads((out/'results.json').read_text())
 assert run['status']=='completed' and len(results)==run['result_count']
 baseline=ROOT/'evidence/governance/20260906-baseline/gate1-20260923'
 specs=json.loads((baseline/'selected-queries.json').read_text())
 if run.get('selected_property_ids'):
  ids=run['selected_property_ids'];specs=[s for s in specs if s['id'] in ids]
 assert len(specs)==len(results)
 assert sha((baseline/'model.xml').read_bytes())==run['model_hash']
 assert sha((baseline/'selected-queries.q').read_bytes())==run['frozen_query_set_hash']
 assert sha((ROOT/'manifests/baselines/reviewer-r1.yaml').read_bytes())==run['baseline_manifest_sha256']
 assert (out/'version.stdout.txt').read_bytes().decode()==run['tool_version']
 audit=json.loads((out/'baseline-audit.json').read_text());assert audit['hash_status']=='match' and audit['baseline_frozen']
 for line in (out/'SHA256SUMS').read_text().splitlines():
  expected,name=line.split('  ',1);assert '/' not in name and '\\' not in name
  assert sha((out/name).read_bytes())==expected,name
 for s,r in zip(specs,results):
  assert r['property_id']==s['id'] and r['formal_query']==s['query']
  assert (out/r['query_path']).read_text()==s['query']+'\n'
  assert sha((out/r['query_path']).read_bytes())==r['query_hash']
  assert r['model_hash']==run['model_hash'] and r['source_commit']==run['source_commit'] and r['tool_version']==run['tool_version']
  text=(out/r['stdout_path']).read_text()+'\n'+(out/r['stderr_path']).read_text()
  values=re.findall(r'Formula is (NOT satisfied|satisfied|MAYBE satisfied)',text)
  if r['status']=='success':
   assert r['termination']=='completed' and r['exit_code']==0 and len(values)==1
   assert r['verdict']=={'satisfied':'satisfied','NOT satisfied':'violated','MAYBE satisfied':'inconclusive'}[values[0]]
  else:assert r['verdict'] is None
  for trace in r['trace_paths']:assert (out/trace).is_file() and (out/trace).stat().st_size>0
  if r['status']=='success' and (((s['query'].startswith('A[]') or '-->' in s['query']) and r['verdict']=='violated') or (s['query'].startswith('E<>') and r['verdict']=='satisfied')):
   assert r['trace_paths'],'missing diagnostic trace: '+s['id']
 print(f'Evidence audit OK: {len(results)} formulas, frozen identity, raw hashes, statuses and trace presence. No independent acceptance.')
if __name__=='__main__':audit(Path(sys.argv[1]).resolve())
