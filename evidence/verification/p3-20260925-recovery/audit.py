"""Audit archived witness and its endpoint; no verifier execution."""
import hashlib, importlib.util, json, tarfile, tempfile
from pathlib import Path
import xml.etree.ElementTree as E
ROOT=Path(__file__).resolve().parents[3]
RID='p3-20260925-recovery-001'
summary=ROOT/'evidence/verification/p3-20260923'/RID
spec=importlib.util.spec_from_file_location('raw_audit',summary.parent/'audit.py')
audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)
manifest=json.loads((summary/'archive.json').read_text());archive=ROOT/manifest['archive']
assert hashlib.sha256(archive.read_bytes()).hexdigest()==manifest['sha256']
with tempfile.TemporaryDirectory() as tmp:
 with tarfile.open(archive) as tar:tar.extractall(tmp,filter='data')
 raw=Path(tmp)/RID;audit.audit(raw)
 for name in ['run.json','run.yaml','results.json']:assert (raw/name).read_bytes()==(summary/name).read_bytes()
 result=json.loads((raw/'results.json').read_text())[0]
 assert result['status']=='success' and result['verdict']=='satisfied'
 assert result['formal_query']=='E<> sdn_attempt_active'
 r=E.parse(raw/result['trace_paths'][0]).getroot()
 nodes={n.get('id'):n for n in r.findall('node')}
 transitions={}
 for t in r.findall('transition'):
  assert t.get('from') not in transitions
  transitions[t.get('from')]=t
 current=r.get('initial_node');seen=set();count=0
 while current in transitions:
  assert current not in seen;seen.add(current)
  last=transitions[current];current=last.get('to');count+=1
 node=nodes[current]
 vector=r.find("variable_vector[@id='%s']" % node.get('variable_vector'))
 values={v.get('variable'):v.get('value') for v in vector}
 assert values['sys.sdn_attempt_active']=='1'
 for name in ['primary','rollback','total']:assert values['sys.sdn_attempt_'+name]=='0'
 locations=r.find("location_vector[@id='%s']" % node.get('location_vector')).get('locations').split()
 assert 'sdn_A_REC_0.FailureDetected' in locations
 edge_ids=last.get('edges').split();edges={e.get('id'):e for e in r.findall('system/process/edge')}
 assert any(edges[x].findtext('sync')=='sdn_link_failure?' for x in edge_ids)
 assert any(edges[x].findtext('sync')=='sdn_link_failure!' for x in edge_ids)
 print(json.dumps({'run_id':result['run_id'],'status':result['status'],'verdict':result['verdict'],'witness_transitions':count,'endpoint':current,'final_edges':edge_ids,'endpoint_active':True,'endpoint_counts':{'primary':0,'rollback':0,'total':0},'recovery_location':'FailureDetected','trigger':'sdn_link_failure','limitation':'existential start witness only; not recovery success, universal termination or deadlock freedom'},indent=2))
