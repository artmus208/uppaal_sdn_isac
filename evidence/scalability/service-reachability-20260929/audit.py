#!/usr/bin/env python3
"""Read-only provenance/verdict audit; no verifier launches."""
import argparse
import copy
import csv
import gzip
import hashlib
import json
import subprocess
from pathlib import Path
import runner as r

HERE=r.HERE

def require(condition, message):
    if not condition:
        raise ValueError(message)


def raw(info):
    data=(HERE/info['reference']).read_bytes()
    require(hashlib.sha256(data).hexdigest()==info['storage_sha256'], 'stored stream hash')
    decoded=gzip.decompress(data) if info['encoding']=='gzip' else data
    require(hashlib.sha256(decoded).hexdigest()==info['sha256'], 'raw stream hash')
    return decoded


def check_record(rec):
    monitor=json.loads((HERE/rec['monitor_reference']).read_text())
    for key,value in monitor.items():
        require(rec[key]==value, 'monitor mismatch: '+key)
    require(rec['status'] in ('success','timeout','memory_limit'), 'unsupported status')
    require(rec['execution_status']==monitor['status'], 'execution status')
    require(rec['process_reaped'] and rec['samples']>0, 'unmonitored/unreaped process')
    require(rec['timeout_seconds']==30 and rec['memory_limit_bytes']==2*1024**3, 'limits changed')
    require(rec['hardware_description']['available_physical_ram_bytes']>=3*1024**3, 'insufficient headroom')
    stdout=raw({key:rec['stdout_'+key] for key in ('reference','storage_sha256','sha256','encoding')}).decode(errors='replace')
    raw({key:rec['stderr_'+key] for key in ('reference','storage_sha256','sha256','encoding')})
    for kind in ('model','query'):
        path=rec[kind+'_path']
        require(r.sha(r.ROOT/path)==rec[kind+'_hash'],kind+' hash')
        data=subprocess.check_output(['git','show',rec['source_commit']+':'+path],cwd=r.ROOT)
        require(hashlib.sha256(data).hexdigest()==rec[kind+'_hash'],kind+' source commit')
    expected_folder=str(r.INPUT.relative_to(r.ROOT))+f'/generated/n{rec["N"]}'
    require(rec['model_path']==expected_folder+'/model.xml', 'model instance')
    require(rec['query_path']==expected_folder+f'/p4/u{rec["entity"]}-service.q', 'query instance')
    query=(r.ROOT/rec['query_path']).read_text().strip()
    require(query==f'E<> family_grant_{rec["entity"]}', 'query semantics')
    require(rec['run_id']==f'service-002-n{rec["N"]}-u{rec["entity"]}-service','run identity')
    cmd=rec['command']
    require(cmd[1:1+len(r.SEARCH)]==r.SEARCH,'search settings')
    # Relocated reviewer checkouts retain the original absolute command paths.
    # Match portable repository suffixes rather than the reviewer's local prefix.
    for arg,kind in zip(cmd[-2:],('model','query')):
        require(arg.replace('\\','/').endswith('/'+rec[kind+'_path']), 'command '+kind+' path')
    require(cmd[1+len(r.SEARCH):3+len(r.SEARCH)]==['-t','0'],'trace setting')
    meta=json.loads((r.ROOT/rec['model_path']).with_name('metadata.json').read_text())
    require(rec['generator_hash']==meta['generator_hash'],'generator hash')
    require(rec['source_hash']==meta['source_hash'],'input source hash')
    for key,name in [('parameter_set','parameters.json'),('instance_vector','instance-vector.json')]:
        require(rec[key]==json.loads((r.ROOT/rec['model_path']).with_name(name).read_text()),key)
    explicit=r.driver.verdict(stdout)
    expected=explicit if rec['status']=='success' else None
    require(rec['property_verdict']==expected,'unsupported verdict')
    require(rec['raw_stdout_verdict']==explicit,'raw verdict mismatch')
    require(rec['result_per_query']==([{'formula':query,'verdict':explicit}] if expected else []),'query verdict mismatch')
    if rec['status']=='success': require(explicit is not None,'missing explicit result')
    rows=list(csv.DictReader((HERE/rec['memory_samples_reference']).read_text().splitlines()))
    require(len(rows)==rec['samples'],'sample count')
    require(max(int(row['private_bytes']) for row in rows)==rec['peak_private_bytes'],'private peak')
    require(max(int(row['peak_working_set_bytes']) for row in rows)==rec['peak_reported_working_set_bytes'],'working-set peak')
    for trace in rec['trace']['files']: raw(trace)
    require(rec['trace']['availability']==('present' if rec['trace']['files'] else 'not_produced'),'trace availability')


def audit(self_test=False):
    pins=r.pins()
    folder=HERE/'runs/service-002'
    settings=json.loads((folder/'settings.json').read_text())
    require(settings['status']=='completed','campaign incomplete')
    require(settings['working_tree_before_campaign']=='clean','unclean source')
    records=json.loads((folder/'runs.json').read_text())
    require([(x['N'],x['entity']) for x in records]==[(n,i) for n in range(1,5) for i in range(n)],'plan coverage/order')
    require(len({x['run_id'] for x in records})==10,'duplicate runs')
    version=(HERE/settings['version_reference']).read_text().splitlines()[0]
    require(r.sha(HERE/settings['version_reference'])==settings['version_sha256'],'captured version')
    for rec in records:
        require(rec['source_commit']==settings['source_commit'],'campaign source')
        require(rec['tool_version']==version,'tool version')
        check_record(rec)
    helper=json.loads((folder/'help/metadata.json').read_text())
    for stream in ('stdout','stderr'):
        require(r.sha(folder/'help'/f'{stream}.txt')==helper[stream+'_sha256'],'help stream hash')
    total=sum(x['runtime_seconds'] for x in records)+helper['runtime_seconds']+settings['prior_metadata_seconds']
    require(abs(total-settings['used_seconds'])<1e-6 and total<=420,'total budget')
    require(all(x['runtime_seconds']<60 for x in records),'unexpected cleanup overrun')
    count=0
    if self_test:
        for field,bad in [('model_hash','0'*64),('query_hash','0'*64),('property_verdict','fabricated'),('samples',0)]:
            damaged=copy.deepcopy(records[0]);damaged[field]=bad
            try:check_record(damaged)
            except ValueError:count+=1
            else:raise ValueError('Audit accepted mutation: '+field)
    return {'kind':'static_evidence_audit_not_new_verification','records':len(records),'input_hashes':len(pins['files']),
            'rejected_mutations':count,'verifier_wall_seconds':total,
            'outcomes':[{'run_id':x['run_id'],'status':x['status'],'verdict':x['property_verdict'],
                         'model_hash':x['model_hash'],'query_hash':x['query_hash'],'tool_version':x['tool_version']} for x in records]}


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--self-test',action='store_true')
    a=ap.parse_args()
    print(json.dumps(audit(a.self_test),indent=2))
