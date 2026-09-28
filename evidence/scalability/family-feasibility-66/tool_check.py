#!/usr/bin/env python3
"""Bounded UPPAAL compile and initial-state load only. Never runs scientific queries."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import time
import generate as g


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--verifyta', required=True, type=Path)
    p.add_argument('--run-id', required=True)
    a=p.parse_args()
    if not a.run_id.replace('-','').replace('_','').isalnum(): p.error('simple unique run-id required')
    exe=a.verifyta.resolve()
    out=g.HERE/'checks'/a.run_id
    if out.exists(): p.error('run directory already exists; evidence is immutable')
    # Capture source state BEFORE generating any output files.
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=g.ROOT,text=True).strip()
    dirty=subprocess.check_output(['git','status','--porcelain','--untracked-files=normal'],cwd=g.ROOT,text=True).strip()
    if dirty: p.error('commit candidate and checks before tool runs; working tree is dirty')
    out.mkdir(parents=True)
    env=os.environ.copy()
    env.pop('UPPAAL_COMPILE_ONLY',None)
    windows=exe.suffix.lower()=='.exe' and os.name!='nt'
    def tool_path(path):
        return subprocess.check_output(['wslpath','-w',str(path)],text=True).strip() if windows else str(path)
    cpu='not_available'
    if Path('/proc/cpuinfo').exists():
        cpu=next((l.split(':',1)[1].strip() for l in Path('/proc/cpuinfo').read_text().splitlines() if l.startswith('model name')),cpu)
    records=[]
    version=''
    def run(name,cmd,compile_only=False,model=None,query=None,kind='static_validation',n=None):
        started=datetime.datetime.now(datetime.timezone.utc).isoformat(); begin=time.monotonic()
        runenv=env.copy()
        if compile_only:
            runenv['UPPAAL_COMPILE_ONLY']='1'
            if windows:
                runenv['WSLENV']=runenv.get('WSLENV','')+':UPPAAL_COMPILE_ONLY'
        stdout=out/(name+'.stdout.txt'); stderr=out/(name+'.stderr.txt')
        with stdout.open('wb') as so, stderr.open('wb') as se:
            try:
                r=subprocess.run(cmd,stdout=so,stderr=se,env=runenv,cwd=exe.parent,timeout=10)
                code=r.returncode; status='success' if code==0 else 'error'
            except subprocess.TimeoutExpired:
                code=None; status='timeout'
        data={'run_id':a.run_id+'-'+name,'status':status,'exit_code':code,'source_commit':commit,'working_tree_before_run':'clean',
              'command':cmd,'cwd':str(exe.parent),'environment_override':{'UPPAAL_COMPILE_ONLY':'1'} if compile_only else {},
              'started_at_utc':started,'runtime_seconds':time.monotonic()-begin,'timeout_seconds':10,
              'operating_environment':platform.platform(),'execution_environment':'Windows verifyta via WSL interop' if windows else platform.platform(),
              'hardware_description':{'cpu':cpu,'logical_cpu_count':os.cpu_count(),'ram_bytes':os.sysconf('SC_PAGE_SIZE')*os.sysconf('SC_PHYS_PAGES') if hasattr(os,'sysconf') else None},
              'peak_memory':'not_available','states_explored':'not_available','trace':'not_requested',
              'source_hash':g.inputs()['source_hash'],'generator_hash':g.sha((g.HERE/'generate.py').read_bytes()),
              'tool_version':version,'model_hash':g.sha(model.read_bytes()) if model else None,
              'query_hash':g.sha(query.read_bytes()) if query else None,'evidence_kind':kind,
              'property_verdict':'not_applicable','claim_scope':'syntax/types or initial-state load only; no scientific query verdict',
              'stdout_reference':str(stdout.relative_to(g.HERE)),'stderr_reference':str(stderr.relative_to(g.HERE)),
              'stdout_hash':g.sha(stdout.read_bytes()),'stderr_hash':g.sha(stderr.read_bytes()),'acceptance_status':'not_reviewed'}
        if n:
            data['instance_vector']=json.loads((g.HERE/'generated'/f'n{n}'/'instance-vector.json').read_text())
            data['parameter_set']=json.loads((g.HERE/'generated'/f'n{n}'/'parameters.json').read_text())
        records.append(data)
        (out/'runs.json').write_bytes(g.encoded(records))
        print(name,status,code,flush=True)
        return data,stdout.read_text(errors='replace'),stderr.read_text(errors='replace')
    rec,so,se=run('version',[str(exe),'--version'],kind='tool_availability')
    if rec['status']!='success' or 'Licensed to' not in so: raise SystemExit('No licensed tool version')
    version=so.splitlines()[0]; rec['tool_version']=version
    (out/'runs.json').write_bytes(g.encoded(records))
    for n in (1,2):
        folder=g.HERE/'generated'/f'n{n}'; model=folder/'model.xml'; q=folder/'queries.q'
        rec,so,se=run(f'n{n}-compile',[str(exe),tool_path(model),tool_path(q)],True,model,q,n=n)
        if rec['status']!='success' or 'Verifying formula' in so: raise SystemExit('Compile-only validation failed')
        q=folder/'load.q'
        rec,so,se=run(f'n{n}-load',[str(exe),'-q','-s','-r','66',tool_path(model),tool_path(q)],False,model,q,'direct_model_checking',n)
        if rec['status']=='success' and so.count('Formula is satisfied.')==1:
            rec['property_verdict']='satisfied'
            rec['result_per_query']=[{'formula':'E<> true','verdict':'satisfied'}]
            rec['claim_scope']='initial-state engine load only; not progress, nonvacuity, C01/C02 or P4'
            (out/'runs.json').write_bytes(g.encoded(records))
        else: raise SystemExit('Initial-state load failed; see raw logs')
    # Controls determine whether compile-only really parses the query set.
    badq=out/'invalid-query.q'; badq.write_text('E<> family_NONEXISTENT\n')
    model=g.HERE/'generated/n1/model.xml'
    rec,so,se=run('invalid-query-compile',[str(exe),tool_path(model),tool_path(badq)],True,model,badq)
    # UPPAAL 5 compile-only ignores external queries: preserve the observed control.
    rec['claim_scope']='compile-only ignores external queries; not query validation'
    (out/'runs.json').write_bytes(g.encoded(records))
    # Parse the entire query file but execute only its initial-state first query.
    for n in (1,2):
        folder=g.HERE/'generated'/f'n{n}'; model=folder/'model.xml'
        combined=out/f'n{n}-parse-all.q'
        combined.write_bytes(b'E<> true\n'+(folder/'queries.q').read_bytes())
        rec,so,se=run(f'n{n}-query-parse',[str(exe),'-q','-s','-r','66','--query-index','0',tool_path(model),tool_path(combined)],False,model,combined,'direct_model_checking',n)
        if rec['status']!='success' or so.count('Formula is satisfied.')!=1: raise SystemExit('Query parse/load failed')
        rec['property_verdict']='satisfied'; rec['result_per_query']=[{'formula':'E<> true','verdict':'satisfied'}]
        rec['claim_scope']='whole query-file parsing; execution restricted to E<> true at index 0'
        (out/'runs.json').write_bytes(g.encoded(records))
    invalid_all=out/'invalid-query-after-initial.q'; invalid_all.write_text('E<> true\nE<> family_NONEXISTENT\n')
    rec,so,se=run('invalid-query-after-initial',[str(exe),'-q','--query-index','0',tool_path(model),tool_path(invalid_all)],False,model,invalid_all)
    if rec['status']=='success': raise SystemExit('Selected-query execution skipped validation of unselected queries')
    model=g.HERE/'generated/n1/model.xml'
    badmodel=out/'invalid-model.xml'; badmodel.write_text(model.read_text().replace('u0_mac_queue_q=0','u0_mac_queue_q=family_NONEXISTENT',1))
    rec,so,se=run('invalid-model-compile',[str(exe),tool_path(badmodel),tool_path(g.HERE/'generated/n1/load.q')],True,badmodel,g.HERE/'generated/n1/load.q')
    if rec['status']=='success': raise SystemExit('Model negative control not rejected')
    print('Both model/query type checks, initial-state loads and parser controls completed.')


if __name__=='__main__': main()
