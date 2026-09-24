"""Summarize observed XML trace edges/terminal values; never infer universal claims."""
import json,sys,xml.etree.ElementTree as E
from pathlib import Path
p=Path(sys.argv[1]);r=E.parse(p).getroot()
nodes={n.get('id'):n for n in r.findall('node')}
variables={v.get('id'):{x.get('variable'):x.get('value') for x in v} for v in r.findall('variable_vector')}
edges={e.get('id'):e for e in r.findall('.//edge')}
current=r.get('initial_node');path=[];matching=[]
for t in r.findall('transition'):
 assert t.get('from')==current
 for ident in t.get('edges','').split():
  e=edges[ident];record={'edge':ident,'from':e.get('from'),'to':e.get('to'),'sync':e.findtext('sync'),'update':e.findtext('update')}
  path.append(record)
  if e.get('from','').endswith('.WaitPHYAck') and e.get('to','').endswith('.Idle') and 'mac_phy_ack?' in (e.findtext('sync') or ''):matching.append(record)
 current=t.get('to')
values=variables[nodes[current].get('variable_vector')]
print(json.dumps({'trace':p.name,'initial_node':r.get('initial_node'),'terminal_node':current,'transition_count':len(r.findall('transition')),'terminal_monitor_values':{k:v for k,v in values.items() if any(x in k for x in ['mac_queue_','sdn_attempt_','mac_obs_ack','mac_phy_ack_timeout'])},'matching_ack_edges':matching,'edges':path,'scope':'This single symbolic trace only; no concrete timestamp or universal claim inferred.'},ensure_ascii=False,indent=2))
