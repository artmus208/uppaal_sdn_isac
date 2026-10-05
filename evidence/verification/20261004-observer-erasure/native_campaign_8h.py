"""Issue #116: persistent sequential native campaign, 8 hours / 7 GiB per query."""
import argparse
import json
import os
import sys
import traceback
from pathlib import Path
import native_campaign as base

vm, HERE, REPO = base.vm, base.HERE, base.REPO
ROOT = HERE/'native-8h'
QUEUE = ROOT/'queue'
IDS = ['observer-erasure-116-20261005-'+q+'-04' for q in base.QUERIES]

def prepare():
    ROOT.mkdir(exist_ok=False)
    source = REPO/'evidence/instantiation/uav-service-completion-candidate/queries'
    query_bytes = [(source/(q+'.q')).read_bytes() for q in base.QUERIES]
    pack = ROOT/'queries.q'
    pack.write_bytes(b''.join(query_bytes))
    vm.initialize(QUEUE,HERE/'observer-erased.xml',pack,base.VERIFIER,28800,7168)
    cfg = vm.read(QUEUE/'queue.json')
    if cfg['model_hash'] != 'b80db319ff7cdb511cb97aa155be01f1d68707358399fbe02fa39c1c6c32be6c':
        raise ValueError('Diagnostic XML changed')
    if len(cfg['tasks']) != 2:
        raise ValueError('Expected exactly two formulas')
    for task, original in zip(cfg['tasks'],query_bytes):
        if (QUEUE/task['file']).read_bytes() != original:
            raise ValueError('Accepted query bytes changed')
    vm.save(ROOT/'protocol.json',{
        'issue':116, 'authorization':'User requests 8 hours and 7 GiB per formula',
        'timeout_seconds':28800, 'memory_mib':7168, 'options':['-o','0','-t','0'],
        'run_mapping':dict(zip([t['id'] for t in cfg['tasks']],IDS)),
        'model_hash':cfg['model_hash'], 'query_hashes':[t['query_hash'] for t in cfg['tasks']],
        'manager_hash':vm.digest(vm.__file__), 'driver_hash':vm.digest(__file__),
        'base_driver_hash':vm.digest(base.__file__),
        'windows_process_hash':vm.digest(REPO/'src/uppaal_mcp/windows_process.py'),
        'python':sys.executable, 'python_hash':vm.digest(sys.executable),
        'verifier_hash':vm.digest(base.VERIFIER),
        'hardware_reference':'../native/environment.json',
        'instance_reference':'../native/environment.json input_inventory',
        'direct_scope':'29-process diagnostic XML; transfer requires independent proof acceptance',
        'monitoring':'Append-only worker output and immutable completed attempts; avoid hot status.json readers',
        'stop_on':['error','monitor_error','license/version/input mismatch'],
        'initial_attempts_per_formula':1})

def collect(commit, worker_code):
    protocol = vm.read(ROOT/'protocol.json')
    records = []
    for path in sorted(QUEUE.glob('attempts/*/result.json')):
        r = vm.read(path)
        task = path.parent.name.split('-',1)[0]
        for name, expected in vm.read(path.parent/'hashes.json').items():
            if vm.digest(path.parent/name) != expected:
                raise ValueError('Attempt evidence changed: '+name)
        records.append({**r,'native_attempt_id':r['run_id'],
            'run_id':protocol['run_mapping'][task], 'execution_commit':commit,
            'result_path':path.relative_to(HERE).as_posix(),'result_hash':vm.digest(path)})
    vm.save(ROOT/'results.json',records)
    vm.save(ROOT/'worker-exit.json',{'exit_code':worker_code,'finished_at':vm.now(),
        'completed_attempts':len(records),'phase':'finished' if len(records)==2 else 'halted'})
    return records

def worker():
    if (ROOT/'reservation.json').exists() or list(QUEUE.glob('attempts/*')):
        raise ValueError('Campaign already reserved: no automatic retry')
    # The launcher creates only these append-only logs before Python starts.
    status = base.git('status','--porcelain','--untracked-files=all').splitlines()
    permitted = {'?? '+(ROOT/('worker.'+kind+'.log')).relative_to(REPO).as_posix()
                 for kind in ('stdout','stderr')}
    if any(line not in permitted for line in status):
        raise ValueError('Execution checkpoint dirty beyond launch logs')
    protocol = vm.read(ROOT/'protocol.json')
    pins = [(vm.__file__,'manager_hash'),(__file__,'driver_hash'),(base.__file__,'base_driver_hash'),
            (REPO/'src/uppaal_mcp/windows_process.py','windows_process_hash'),
            (sys.executable,'python_hash'),(base.VERIFIER,'verifier_hash')]
    if any(vm.digest(path)!=protocol[key] for path,key in pins):
        raise ValueError('Pinned runtime/code changed')
    vm.verify_inputs(QUEUE,vm.read(QUEUE/'queue.json'))
    commit = base.git('rev-parse','HEAD')
    vm.save(ROOT/'reservation.json',{'execution_commit':commit,'reserved_at':vm.now(),
        'clean_except_append_only_launch_logs':True,'worker_pid':os.getpid(),
        'worker_command':[sys.executable,str(Path(__file__).resolve()),'worker'],
        'run_mapping':protocol['run_mapping'],'protocol_hash':vm.digest(ROOT/'protocol.json')})
    try:
        code = vm.main(['start',str(QUEUE)])
        collect(commit,code)
        return code
    except BaseException as exc:
        vm.save(ROOT/'worker-error.json',{'finished_at':vm.now(),'exception':repr(exc),
            'execution_commit':commit,'traceback':traceback.format_exc()})
        raise

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('prepare','worker'))
    args = parser.parse_args()
    if args.action == 'prepare':
        prepare()
    else:
        raise SystemExit(worker())
