"""Evaluate pinned primary guards on saved witness states, not model checking."""
import hashlib, json, tarfile
from pathlib import Path
import xml.etree.ElementTree as E
ROOT=Path(__file__).resolve().parents[3]
MODEL=ROOT/'evidence/governance/20260906-baseline/gate1-20260923/model.xml'
HASH='592678ed678ce8f70cf278f542e48bd2bb739969b53a962423d3e63f91e3e1e2'
assert hashlib.sha256(MODEL.read_bytes()).hexdigest()==HASH
model=E.parse(MODEL).getroot();decl=model.findtext('declaration')
assert 'sdn_TEL_FRESH=0, sdn_TEL_STALE=1, sdn_TEL_MISSING=2' in decl
assert 'sdn_POL_CONSTRAINED=3, sdn_POL_REROUTE=4, sdn_POL_REJECT=5' in decl
assert 'bool sdn_reconfig_allowed() { return sdn_telemetryClass == sdn_TEL_FRESH && sdn_policyClass != sdn_POL_CONSTRAINED && sdn_policyClass != sdn_POL_REJECT; }' in decl
rec=next(t for t in model.findall('template') if t.findtext('name')=='sdn_Template_A_REC')
guards=[e.findtext("label[@kind='guard']") for e in rec.findall('transition')]
assert guards[2:5]==['sdn_standby_available && sdn_reconfig_allowed()','sdn_alternative_config_exists && sdn_reconfig_allowed()','!sdn_standby_available && !sdn_alternative_config_exists || !sdn_reconfig_allowed()']

def evaluate(v):
 standby=bool(int(v['sdn_standby_available']));alternative=bool(int(v['sdn_alternative_config_exists']))
 fresh=int(v['sdn_telemetryClass'])==0;permitted=int(v['sdn_policyClass']) not in [3,5]
 allowed=fresh and permitted
 return {'fresh_telemetry':fresh,'policy_permits':permitted,'reconfig_allowed':allowed,'primary_standby_guard':standby and allowed,'primary_alternative_guard':alternative and allowed,'direct_rollback_guard':(not standby and not alternative) or not allowed}

observations=[]
for rid in ['p3-20260925-recovery-001','p3-20260925-recovery-002']:
 summary=ROOT/'evidence/verification/p3-20260923'/rid
 archive=json.loads((summary/'archive.json').read_text());p=ROOT/archive['archive']
 assert hashlib.sha256(p.read_bytes()).hexdigest()==archive['sha256']
 result=next(x for x in json.loads((summary/'results.json').read_text()) if x['status']=='success')
 with tarfile.open(p) as tar:
  r=E.fromstring(tar.extractfile(rid+'/'+result['trace_paths'][0]).read())
 nodes={n.get('id'):n for n in r.findall('node')};locations={n.get('id'):n.get('locations').split() for n in r.findall('location_vector')}
 vectors={v.get('id'):{x.get('variable').removeprefix('sys.'):x.get('value') for x in v} for v in r.findall('variable_vector')}
 for tr in r.findall('transition'):
  if 'sdn_A_REC_0' not in tr.get('edges',''):continue
  for ref in ['from','to']:
   node=nodes[tr.get(ref)]
   if 'sdn_A_REC_0.FailureDetected' not in locations[node.get('location_vector')]:continue
   v=vectors[node.get('variable_vector')]
   if any(o['run_id']==result['run_id'] and o['state']==node.get('id') for o in observations):continue
   values={k:v[k] for k in ['sdn_standby_available','sdn_alternative_config_exists','sdn_telemetryClass','sdn_policyClass']}
   observations.append({'run_id':result['run_id'],'trace':rid+'/'+result['trace_paths'][0],'state':node.get('id'),'values':values,'guard_evaluation':evaluate(values)})
assert len(observations)==2
assert all(not o['guard_evaluation']['primary_standby_guard'] and not o['guard_evaluation']['primary_alternative_guard'] and o['guard_evaluation']['direct_rollback_guard'] for o in observations)
# Sensitivity control on guard transcription; synthetic valuations are NOT reachable-state claims.
control={'sdn_standby_available':'0','sdn_alternative_config_exists':'1','sdn_telemetryClass':'0','sdn_policyClass':'0'}
assert evaluate(control)['primary_alternative_guard']
assert not evaluate(dict(control,sdn_policyClass='5'))['primary_alternative_guard']
assert not evaluate(dict(control,sdn_telemetryClass='2'))['primary_alternative_guard']
print(json.dumps({'model_hash':HASH,'classification':'saved-witness guard diagnosis only','observations':observations,'synthetic_control':'fresh telemetry + permitted policy + alternative enables the local primary guard; flipping either policy or freshness disables it; reachability and synchronization not tested','remaining':'a globally reachable state satisfying a primary guard AND binary receiver/target constraints; then separately primary followed by rollback'},indent=2))
