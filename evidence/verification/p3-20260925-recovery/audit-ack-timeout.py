"""Audit archived witness and its endpoint; no verifier execution."""
import hashlib, importlib.util, json, tarfile, tempfile
from pathlib import Path
import xml.etree.ElementTree as E
ROOT=Path(__file__).resolve().parents[3]
RID='p3-20260925-ack-timeout-001'
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
 assert result['formal_query']=='E<> mac_phy_ack_timeout'
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
 assert values['sys.mac_phy_ack_timeout']=='1'
 locations=r.find("location_vector[@id='%s']" % node.get('location_vector')).get('locations').split()
 scheduler=next(x for x in locations if x.startswith('mac_A_SCH_0.'))
 assert scheduler=='mac_A_SCH_0.ScheduleFailure'
 print(json.dumps({'run_id':result['run_id'],'status':result['status'],'verdict':result['verdict'],'witness_transitions':count,'endpoint':current,'final_edges':last.get('edges').split(),'scheduler_location':scheduler,'endpoint_values':{k:v for k,v in values.items() if k in ['sys.mac_phy_ack_timeout','sys.mac_obs_ack_active','sys.mac_obs_ack_late','sys.mac_phy_command_pending','sys.mac_mac_report_pending']},'limitation':'existential ACK-timeout witness only; not universal completion, successful ACK delivery or deadlock freedom'},indent=2))
