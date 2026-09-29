"""Read-only audit of the completed #76 evidence; not model checking."""
import csv
import gzip
import hashlib
import json
from pathlib import Path
import re


def sha(data):
    return hashlib.sha256(data).hexdigest()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def audit(root, records=None):
    root=Path(root)
    here=root/'evidence/scalability/runs/uav-family-p4-20260929'
    manifest=json.loads((root/'manifests/baselines/uav-family-r1.yaml').read_bytes())
    folder=here/'campaign-002'
    settings=json.loads((folder/'settings.json').read_bytes())
    require(settings['status'] in ('completed','stopped'),'campaign still active')
    records=records if records is not None else json.loads((folder/'runs.json').read_bytes())
    plan=json.loads((root/'evidence/scalability/family-series-68/p4-plan.json').read_bytes())['steps']
    require(len(records)==len(plan)==117,'missing scheduled cell')
    require(len({r['run_id'] for r in records})==117,'duplicate run ID')
    require(settings['baseline_manifest_sha256']==sha((root/'manifests/baselines/uav-family-r1.yaml').read_bytes()),'manifest changed')
    require(settings['used_seconds']<=7200,'budget exceeded')
    require(settings['working_tree_at_start']=='clean','unclean source checkout')
    require(settings['tool_version']==manifest['tool_version'],'campaign version mismatch')
    for filename,field in (('runner.py','runner_sha256'),('monitor.ps1','monitor_sha256')):
        require(sha((here/filename).read_bytes())==settings[field],'execution source changed: '+filename)
    require(sha((here/'campaign-001/settings.json').read_bytes())==settings['reused_metadata_sha256'],'metadata reuse drift')
    successful=[];completed=[]; charged=settings['prior_verifier_budget_seconds']
    for row, scheduled in zip(records,plan):
        for key in ('repeat','phase','N'):
            require(row[key]==scheduled[key],'schedule identity changed')
        if scheduled['phase']=='model-checking':
            require(row['query_id']==scheduled['query_id'],'query order changed')
            require(row['formula']==scheduled['formula'],'formula changed')
        if row['status']=='not_started':
            require(bool(row.get('reason')) and row.get('property_verdict') is None,'invalid not-started cell')
            continue
        require(row['source_commit']==settings['source_commit'],'source commit mismatch')
        require(row['status'] in ('success','timeout','memory_limit','error','monitor_error','verdict_error'),'unknown cell status')
        if row['phase']=='generation':
            for stream in ('stdout','stderr'):
                require(sha((folder/row['cell_id']/(stream+'.txt')).read_bytes())==row[stream+'_sha256'],'generation stream hash mismatch')
            if row['status']=='success':
                generated=json.loads((folder/row['cell_id']/'stdout.txt').read_bytes())
                require(generated['count']==len(generated['files'])==70,'generation incomplete')
                for relative,digest in generated['files'].items():
                    require(sha((folder/row['cell_id']/'generated'/relative).read_bytes())==digest,'generated artifact drift')
                    require(sha((root/'evidence/scalability/family-series-68/generated'/relative).read_bytes())==digest,'generated input mismatch')
            continue
        charged+=row.get('budget_charged_seconds',0)
        model=manifest['models'][row['N']-1]
        require(row['model_hash']==model['files']['model.xml']['sha256'],'model hash mismatch')
        require(sha((root/row['model_path']).read_bytes())==row['model_hash'],'model bytes mismatch')
        require(row['tool_version']==manifest['tool_version'],'tool version mismatch')
        require(row['generator_hash']==model['generator_hash'],'generator mismatch')
        if row.get('query_path'):
            require(sha((root/row['query_path']).read_bytes())==row['query_hash'],'query hash mismatch')
        require(row['hardware_description']['available_physical_ram_bytes']>=3*1024**3,'RAM headroom missing')
        require(row['timeout_seconds']==60 and row['memory_limit_bytes']==2*1024**3,'resource limits changed')
        monitor=json.loads((here/row['monitor_reference']).read_text(encoding='utf-8-sig'))
        for key in ('command','exit_code','runtime_seconds','samples','process_reaped','peak_private_bytes','peak_reported_working_set_bytes'):
            require(row[key]==monitor[key],'monitor record mismatch: '+key)
        require(row['status']==monitor['status'] or (row['status']=='verdict_error' and monitor['status']=='success'),'monitor status mismatch')
        require(row['samples']>0 and row['process_reaped'],'monitor measurement or termination missing')
        samples=list(csv.DictReader((here/row['memory_samples_reference']).read_text().splitlines()))
        require(len(samples)==row['samples'],'sample count mismatch')
        streams={}
        for stream in ('stdout','stderr'):
            info=row[stream]; raw=(here/info['reference']).read_bytes()
            require(sha(raw)==info['storage_sha256'],'stored stream hash mismatch')
            data=gzip.decompress(raw) if info['encoding']=='gzip' else raw
            require(sha(data)==info['sha256'],'raw stream hash mismatch')
            streams[stream]=data.decode(errors='replace')
        for info in row['trace']['files']:
            raw=(here/info['reference']).read_bytes()
            require(sha(raw)==info['storage_sha256'],'trace storage hash mismatch')
            data=gzip.decompress(raw) if info['encoding']=='gzip' else raw
            require(sha(data)==info['sha256'],'trace bytes mismatch')
        verdicts=re.findall(r'-- Formula is (NOT satisfied|satisfied)\.',streams['stdout'])
        if row['phase']=='model-checking':
            if row['status']=='success':
                require(row['exit_code']==0 and len(verdicts)==1,'successful query lacks unique verdict')
                verdict='satisfied' if verdicts[0]=='satisfied' else 'violated'
                require(row['property_verdict']==verdict,'verdict differs from raw stdout')
                require(row['result_per_query']==[{'formula':row['formula'],'verdict':verdict}],'per-query result mismatch')
                successful.append({k:row[k] for k in ('run_id','status','model_hash','query_hash','tool_version','property_verdict')})
            else:
                require(row['property_verdict'] is None and not row['result_per_query'],'censored cell contains verdict')
        completed.append(row['run_id'])
    require(abs(charged-settings['used_seconds'])<1e-6,'budget accounting mismatch')
    return {'kind':'evidence_integrity_audit_not_new_verification','scheduled_cells':117,
            'completed_verifier_cells':len(completed),'budget_seconds':settings['used_seconds'],
            'successful_query_records':successful}


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);a=p.parse_args()
    print(json.dumps(audit(a.root),indent=2))
