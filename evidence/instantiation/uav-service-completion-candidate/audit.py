"""Read-only audit of exact candidate, archives and engine causal evidence."""
import hashlib
import json
from pathlib import Path
import zipfile

import generate

HERE=Path(__file__).resolve().parent


def require(value,message):
    if not value:raise ValueError(message)


def read(name):
    p=HERE/name
    if p.exists():return p.read_bytes()
    with zipfile.ZipFile(HERE/'raw-traces.zip') as z:return z.read(name)


def data(name):return json.loads(read(name))


def events(cell):return [json.loads(line) for line in read(f'runs/{cell}/steps.jsonl').decode().splitlines()]


def audit():
    generated=generate.outputs()
    for name,content in generated.items():require((HERE/name).read_bytes()==content,f'generated drift {name}')
    with zipfile.ZipFile(HERE/'raw-traces.zip') as z:
        index=data('raw-index.json');require(set(z.namelist())==set(index),'raw archive inventory')
        for name,item in index.items():
            content=z.read(item['entry']);require(generate.sha(content)==item['sha256'] and len(content)==item['bytes'],f'raw hash {name}')
    with zipfile.ZipFile(HERE/'source-snapshots.zip') as z:
        for cell,item in data('source-index.json').items():
            commit=z.read(item['commit_object'])
            identity=hashlib.sha1(b'commit '+str(len(commit)).encode()+b'\0'+commit).hexdigest()
            require(identity==item['commit'],f'commit identity {cell}')
            for f in item['files']:require(generate.sha(z.read(f['entry']))==f['hash'],f'source hash {cell}/{f["path"]}')
    inventory=data('inventory.json');model_hash=inventory['model_hash'];runs=[];total=0
    expected={'simulate-001':'error','simulate-002':'error','simulate-003':'schedule_exhausted',
      'simulate-004':'schedule_exhausted','simulate-005':'error','simulate-006':'goal_reached',
      'replay-001':'replay_complete','negative-discrete-001':'rejected','negative-clock-001':'rejected'}
    for cell,status in expected.items():
        result=data(f'runs/{cell}/result.json');provenance=data(f'runs/{cell}/provenance.json')
        monitor=data(f'runs/{cell}/monitor.json');hardware=data(f'runs/{cell}/hardware.json')
        require(result['status']==status,f'status {cell}')
        require(result['query_hash'] is None and result['property_verdict'] is None,f'query verdict {cell}')
        require(result['tool_version'].startswith('UPPAAL version 5.0.0 (rev. 714BA9DB36F49691), June 2023 -- server.'),f'version {cell}')
        require(monitor['process_tree_reaped'] and monitor['native_status']=='success',f'cleanup {cell}')
        require(monitor['runtime_seconds']<60 and monitor['peak_tree_sample_bytes']<2147483648,f'caps {cell}')
        require(hardware['available_ram_bytes']>=3221225472,f'resources {cell}')
        total+=data(f'runs/{cell}/native-summary.json')['total_wall_seconds']
        if cell not in ['simulate-001','simulate-002','simulate-003','simulate-004']:
            require(result['model_hash']==model_hash,f'final model {cell}')
        source=data('source-index.json')[cell]
        model_entry=next(f for f in source['files'] if f['path'].endswith('/uav-service-completion-candidate/model.xml'))
        require(model_entry['hash']==result['model_hash'],f'per-cell model {cell}')
        runs.append({'run_id':provenance['run_id'],'status':result['status'],'evidence_kind':'simulation',
           'model_hash':result['model_hash'],'query_hash':None,'property_verdict':None,'tool_version':result['tool_version'],
           'source_commit':provenance['source_commit'],'source_hash':source['source_hash'],
           'generator_hash':provenance['generator_hash'],'command':provenance['command'],
           'runtime_seconds':monitor['runtime_seconds'],
           'peak_memory_sample_bytes':monitor['peak_tree_sample_bytes'],
           'result':f'runs/{cell}/result.json','provenance':f'runs/{cell}/provenance.json',
           'monitor':f'runs/{cell}/monitor.json','hardware':f'runs/{cell}/hardware.json',
           'accepted_transitions':result.get('accepted_transitions'),'partial_events':len(events(cell)),
           'raw_archive':'raw-traces.zip','source_archive':'source-snapshots.zip'})
    require(total<=600,'aggregate budget')
    replay=data('runs/replay-001/result.json');simulation=data('runs/simulate-006/result.json')
    require(simulation['accepted_transitions']==100 and simulation['goal'],'healthy simulation')
    require(replay['accepted_transitions']==100 and replay['stored_states']==101 and replay['goal'],'healthy replay')
    require(replay['trace_hash']==generate.sha(read('runs/simulate-006/trace.xtr')),'replay trace input')
    states=events('replay-001');sim=events('simulate-006')
    require(len(states)==101 and len(sim)==101,'state count')
    for a,b in zip(states,sim):
        require(a['snapshot']['locations']==b['snapshot']['locations'],'full location replay')
        require(a['snapshot']['values']==b['snapshot']['values'],'full integer replay')
        require(a.get('frontier',1)<=8,'replay frontier')
    variables={n:i for i,n in enumerate(replay['variable_names'])};clocks={n:i for i,n in enumerate(replay['clock_names'])}
    def value(state,name):return state['snapshot']['values'][variables[name]]
    milestones=[]
    for flag,actor,edge in [('c82_active',16,2),('c82_admitted',26,23),('c82_sampled',3,25),
          ('c82_enqueued',50,4),('c82_dispatched',21,1),('c82_attempted',50,6),('c82_success',50,7)]:
        matches=[j for j in range(1,len(states)) if not value(states[j-1],flag) and value(states[j],flag)]
        require(len(matches)==1,f'milestone uniqueness {flag}');j=matches[0]
        require(any(part.strip().split()[:2]==[str(actor),str(edge)] for part in states[j]['edges'].split(';')),f'causal edge {flag}')
        milestones.append({'milestone':flag,'state_index':j,'edges':states[j]['edges']})
    require([m['state_index'] for m in milestones]==sorted(m['state_index'] for m in milestones),'causal order')
    sample=next(m['state_index'] for m in milestones if m['milestone']=='c82_sampled')
    for state in states[sample:]:
        for q in ['pd','fa','miss','acc','cov']:require(value(state,'c82_'+q)==0,f'immutable healthy quality {q}')
    last=states[-1]
    require(last['snapshot']['locations'][16]=='Completed' and value(last,'c82_outcome')==1,'APP terminal')
    for flag in ['received','sampled','admitted','enqueued','dispatched','attempted','receipt_timely','receipt_quality']:
        require(value(last,'c82_'+flag)==1,f'terminal flag {flag}')
    for ident in ['request_id','admitted_id','job_id','sample_id','sample_request_id','tx_request_id','tx_sample_id','received_request_id','received_sample_id']:
        require(value(last,'c82_'+ident)==1,f'terminal identity {ident}')
    for flag in ['cancelled','sensing_failed','tx_lost','queue_failed']:require(value(last,'c82_'+flag)==0,f'healthy failure flag {flag}')
    zone=last['snapshot']['zone']
    require(zone[clocks['c82_sample_age']][0]<=10,'strict receipt sample age <5')
    require(zone[clocks['c82_service_age']][0]<=81,'receipt request age <=40')
    for cell,reason in [('negative-discrete-001','discrete_state_mismatch'),('negative-clock-001','clock_zone_disjoint')]:
        r=data(f'runs/{cell}/result.json')
        require(r['control_expected_rejection'] and r['accepted_transitions']==99 and r['first_unavailable_state_index']==100 and r['reason']==reason,f'negative control {cell}')
    stale=events('simulate-005')[-1]
    require(stale['snapshot']['locations'][16]=='ServiceFailed' and not value(stale,'c82_success') and value(stale,'c82_received'),'real stale receipt rejection')
    if (HERE/'artifacts-sha256.json').exists():
        for name,expected_hash in data('artifacts-sha256.json').items():require(generate.sha((HERE/name).read_bytes())==expected_hash,f'artifact hash {name}')
    return {'evidence_kind':'simulation','acceptance_status':'pending_independent_review',
       'candidate_id':'uav-service-completion-candidate-82-n1','model_hash':model_hash,
       'query_verdicts':{name:None for name in inventory['queries']},'native_wall_seconds':total,
       'runs':runs,'healthy_causal_milestones':milestones,'healthy_replay_states':101,
       'claim':'One engine-confirmed full matching fresh APP completion path; no universal completion/fairness or exhaustive verdict.'}


if __name__=='__main__':
    result=audit();print(json.dumps({'audit':'ok','runs':len(result['runs']),'replay_states':101,'native_wall_seconds':result['native_wall_seconds'],'model_hash':result['model_hash']}))
