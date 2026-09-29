#!/usr/bin/env python3
"""Read and cross-check the completed #78 campaign; never invokes verifyta."""
import csv
import gzip
import hashlib
import json
from pathlib import Path
import re
import subprocess

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def content(item):
    p=ROOT/item['path'];raw=p.read_bytes()
    assert hashlib.sha256(raw).hexdigest()==item['storage_sha256']
    data=gzip.decompress(raw) if item['encoding']=='gzip' else raw
    assert hashlib.sha256(data).hexdigest()==item['sha256']
    return data


def inspect():
    folder=HERE/'runs/diagnostic-001'
    settings=json.loads((folder/'settings.json').read_text())
    rows=json.loads((folder/'runs.json').read_text())
    protocol=json.loads((HERE/'protocol.json').read_text())
    manifest=json.loads((ROOT/'manifests/baselines/uav-family-r1.yaml').read_text())
    n1=manifest['models'][0]
    assert settings['status']=='completed' and settings['within_total_budget'] is True
    assert 0<settings['elapsed_wall_seconds']<=protocol['total_wall_seconds']==300
    assert settings['protocol_hash']==sha(HERE/'protocol.json')
    assert settings['authorization_sha256']==sha(HERE/'authorization.json')
    assert settings['monitor_hash']==sha(ROOT/protocol['monitor'])
    assert settings['runner_hash']==sha(HERE/'run_diagnostics.py')
    assert settings['metadata_helper_hash']==sha(HERE/'metadata.ps1')
    source=settings['source_commit']
    for path,digest in [(HERE/'run_diagnostics.py',settings['runner_hash']),(HERE/'metadata.ps1',settings['metadata_helper_hash']),(ROOT/protocol['model'],protocol['model_hash'])]:
        raw=subprocess.check_output(['git','show',source+':'+str(path.relative_to(ROOT))],cwd=ROOT)
        assert hashlib.sha256(raw).hexdigest()==digest
    assert [x['name'] for x in settings['controls']]==['normal','timeout','memory']
    assert all(x['passed'] and x['monitor']['process_reaped'] and x['monitor']['samples']>0 for x in settings['controls'])
    assert [x['option'] for x in settings['metadata']]==['--version','--help']
    for x in settings['metadata']:
        assert x['result']['status']=='success' and x['result']['process_reaped'] and x['result']['exit_code']==0
        assert not content(x['stderr'])
    version=next(s.strip() for s in content(settings['metadata'][0]['stdout']).decode().splitlines() if s.startswith('UPPAAL '))
    assert version==settings['tool_version']==manifest['tool_version']
    assert len(rows)==3
    summaries=[]
    for q,row in zip(protocol['queries'],rows):
        assert row['query_id']==q['id'] and row['formula']==q['query']
        assert row['source_commit']==source and row['tool_version']==version
        assert row['model_hash']==protocol['model_hash']==sha(ROOT/protocol['model'])
        assert row['query_hash']==q['sha256']==sha(ROOT/q['path'])
        assert row['generator_hash']==n1['generator_hash'] and row['source_hash']==n1['source_hash']
        for key,name in [('parameter_set','parameters.json'),('instance_vector','instance-vector.json')]:
            assert row[key]==json.loads((ROOT/n1['files'][name]['path']).read_text())
        assert row['timeout_seconds']==30 and row['memory_limit_bytes']==2147483648
        h=row['hardware_description']
        assert h['available_physical_ram_bytes']>=3221225472 and str(h['os_build'])=='19045'
        assert any('i5-8300H' in c for c in h['cpu_models'])
        cfg=json.loads((folder/q['id']/'tool.config.json').read_text())
        cmd=row['command'];assert cmd==[cfg['executable']]+cfg['arguments']
        assert row['cwd']==cfg['cwd'] and cfg['compile_only'] is False
        assert cfg['timeout_seconds']==30 and cfg['memory_limit_bytes']==2147483648 and cfg['sample_interval_ms']==50
        assert cmd[1:19]==q['arguments'][:18]
        # The three remaining path arguments are exact expanded trace/model/query paths.
        for actual,relative in [(cmd[-2],protocol['model']),(cmd[-1],q['path'])]:
            assert actual.replace('\\','/').endswith('/'+relative)
        assert cmd[-3].replace('\\','/').endswith('/'+str((folder/q['id']/'trace').relative_to(ROOT)))
        raw=json.loads((ROOT/row['monitor_reference']).read_text(encoding='utf-8-sig'))
        assert raw['status']==row['status']=='timeout'
        assert row['property_verdict'] is None and row['result_per_query']==[]
        assert raw['process_reaped'] and raw['kill_tree_requested'] and raw['samples']>0
        assert row['process_reaped'] and row['samples']==raw['samples'] and row['wrapper_exit_code']==0
        assert row['trace']=={'requested':True,'files':[]}
        assert not list((folder/q['id']).glob('trace*'))
        so=content(row['stdout']);se=content(row['stderr'])
        assert not se and not re.search(rb'-- Formula is (?:NOT )?satisfied\.',so)
        assert row['states_explored']==row['states_stored']=='not_available'
        assert not re.search(rb'States (?:explored|stored)\s*:',so)
        with (ROOT/row['memory_samples_reference']).open() as f:samples=list(csv.DictReader(f))
        assert len(samples)==raw['samples']
        for field,column in [('peak_private_bytes','private_bytes'),('peak_working_set_bytes','working_set_bytes'),('peak_reported_working_set_bytes','peak_working_set_bytes')]:
            assert row[field]==raw[field]==max(int(s[column]) for s in samples)
        peak=max(raw[k] for k in ['peak_private_bytes','peak_working_set_bytes','peak_reported_working_set_bytes'])
        assert peak<2147483648
        summaries.append({'run_id':row['run_id'],'status':row['status'],'property_verdict':None,'model_hash':row['model_hash'],'query_hash':row['query_hash'],'tool_version':version,'runtime_seconds':row['runtime_seconds'],'cpu_seconds':row['cpu_seconds'],'native_peak_bytes':peak,'prelaunch_available_ram_bytes':h['available_physical_ram_bytes'],'maximum_sample_gap_seconds':row['maximum_sample_gap_seconds'],'trace_files':0})
    return {'evidence_kind':'static_audit_of_preserved_model_checking_attempts','this_audit_invokes_verifier':False,'source_commit':source,'campaign_status':'completed','wall_seconds':settings['elapsed_wall_seconds'],'budget_seconds':300,'native_controls_passed':3,'actual_tool_version':version,'attempts':summaries,'conclusion':'Three timeouts; no property verdict, no witness, no localization of reachability blocker.'}

if __name__=='__main__':print(json.dumps(inspect(),indent=2,ensure_ascii=False))
