"""Audit archived dispatch witnesses; never invokes verifyta."""
import hashlib, importlib.util, json, tarfile, tempfile
from pathlib import Path
import xml.etree.ElementTree as E
ROOT=Path(__file__).resolve().parents[3]
RID='p3-20260925-recovery-002'
summary=ROOT/'evidence/verification/p3-20260923'/RID
spec=importlib.util.spec_from_file_location('raw_audit',summary.parent/'audit.py')
audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)
manifest=json.loads((summary/'archive.json').read_text());archive=ROOT/manifest['archive']
assert hashlib.sha256(archive.read_bytes()).hexdigest()==manifest['sha256']
observations=[]
with tempfile.TemporaryDirectory() as tmp:
 with tarfile.open(archive) as tar:tar.extractall(tmp,filter='data')
 raw=Path(tmp)/RID;audit.audit(raw)
 for name in ['run.json','run.yaml','results.json']:assert (raw/name).read_bytes()==(summary/name).read_bytes()
 results=json.loads((raw/'results.json').read_text())
 assert [x['property_id'] for x in results]==['attempt-primary','attempt-rollback','attempt-two']
 for result in results:
  obs={k:result[k] for k in ['run_id','property_id','status','verdict','runtime_seconds','peak_working_set_bytes','model_hash','query_hash','tool_version']}
  if result['status']=='success' and result['verdict']=='satisfied':
   r=E.parse(raw/result['trace_paths'][0]).getroot();nodes={n.get('id'):n for n in r.findall('node')};transitions={}
   for t in r.findall('transition'):
    assert t.get('from') not in transitions;transitions[t.get('from')]=t
   current=r.get('initial_node');seen=set();count=0
   while current in transitions:
    assert current not in seen;seen.add(current);current=transitions[current].get('to');count+=1
   node=nodes[current];vector=r.find("variable_vector[@id='%s']" % node.get('variable_vector'))
   values={v.get('variable'):v.get('value') for v in vector}
   counts={n:int(values['sys.sdn_attempt_'+n]) for n in ['primary','rollback','total']}
   field,expected={'attempt-primary':('primary',1),'attempt-rollback':('rollback',1),'attempt-two':('total',2)}[result['property_id']]
   assert counts[field]==expected
   locations=r.find("location_vector[@id='%s']" % node.get('location_vector')).get('locations').split()
   obs.update(endpoint=current,witness_transitions=count,endpoint_active=values['sys.sdn_attempt_active'],endpoint_counts=counts,recovery_location=next(x for x in locations if x.startswith('sdn_A_REC_0.')))
  observations.append(obs)
print(json.dumps({'observations':observations,'limitation':'existential dispatch witnesses only; no successful service recovery, universal completion or deadlock claim'},indent=2))
