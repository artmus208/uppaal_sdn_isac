"""Issue #116 fixed, single-attempt native campaign; no automatic retries."""
import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(REPO / 'src'))
from uppaal_mcp import verification_manager as vm

GIT = r'C:\Users\musta\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\git\cmd\git.exe'
VERIFIER = r'C:\Program Files (x86)\UPPAAL-5.0.0\bin\verifyta.exe'
QUERIES = ('completion-safety', 'success')

def git(*args):
    return subprocess.check_output([GIT, '-c', 'safe.directory='+REPO.as_posix(), *args], cwd=REPO, text=True).strip()

def prepare():
    source = REPO / 'evidence/instantiation/uav-service-completion-candidate/queries'
    if vm.digest(HERE/'observer-erased.xml') != 'b80db319ff7cdb511cb97aa155be01f1d68707358399fbe02fa39c1c6c32be6c':
        raise ValueError('Diagnostic XML hash mismatch')
    for query in QUERIES:
        queue = HERE/'native'/('observer-erasure-116-20261005-'+query+'-01')
        vm.initialize(queue, HERE/'observer-erased.xml', source/(query+'.q'), VERIFIER, 600, 2048)
        # Manager-normalized single query must remain byte-for-byte identical.
        if (queue/'query-001.q').read_bytes() != (source/(query+'.q')).read_bytes():
            raise ValueError('Query normalization changed accepted bytes')
    vm.save(HERE/'native/protocol.json', {
        'issue': 116, 'queries': list(QUERIES), 'attempts_per_query': 1,
        'timeout_seconds': 600, 'memory_mib': 2048, 'options': ['-o','0','-t','0'],
        'model_hash': vm.digest(HERE/'observer-erased.xml'),
        'verifier_hash': vm.digest(VERIFIER), 'manager_hash': vm.digest(vm.__file__),
        'windows_process_hash': vm.digest(REPO/'src/uppaal_mcp/windows_process.py'),
        'python': sys.executable, 'python_hash': vm.digest(sys.executable),
        'input_manifest': 'manifests/baselines/uav-service-completion-r1.yaml',
        'input_manifest_hash': vm.digest(REPO/'manifests/baselines/uav-service-completion-r1.yaml'),
        'instance': 'N=1, one request/result, no identifier reuse; original 51 processes, diagnostic 29',
        'stop_on': ['error','monitor_error','license/version/input mismatch'],
        'transfer': 'Conditional on independent proof acceptance; direct verdict applies only to diagnostic XML.'})

def run(query):
    queue = HERE/'native'/('observer-erasure-116-20261005-'+query+'-01')
    if (queue/'reservation.json').exists() or list(queue.glob('attempts/*/*')):
        raise ValueError('Single attempt already reserved: no retry authorized')
    if git('status','--porcelain','--untracked-files=all'):
        raise ValueError('Execution checkpoint must be clean')
    protocol = vm.read(HERE/'native/protocol.json')
    if vm.digest(vm.__file__) != protocol['manager_hash'] or vm.digest(sys.executable) != protocol['python_hash']:
        raise ValueError('Execution code/runtime changed')
    if query == 'success':
        previous = HERE/'native/observer-erasure-116-20261005-completion-safety-01'
        results = [vm.read(p) for p in previous.glob('attempts/*/result.json')]
        if len(results) != 1 or results[0]['status'] not in ('success','timeout','memory_limit','inconclusive'):
            raise ValueError('Previous run failed: campaign halted')
    vm.verify_inputs(queue, vm.read(queue/'queue.json'))
    vm.save(queue/'reservation.json', {
        'run_id': queue.name, 'execution_commit': git('rev-parse','HEAD'),
        'clean_before_reservation': True, 'reserved_at': vm.now(),
        'native_worker_command': [sys.executable, str(Path(__file__).resolve()), 'run', query],
        'model_hash': protocol['model_hash'], 'query_hash': vm.read(queue/'queue.json')['tasks'][0]['query_hash']})
    code = vm.main(['start', str(queue)])
    vm.save(queue/'worker-exit.json', {'exit_code': code, 'finished_at': vm.now()})
    return code

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare','run'))
    parser.add_argument('query', nargs='?', choices=QUERIES)
    args = parser.parse_args()
    if args.action == 'prepare':
        prepare()
    else:
        if not args.query:
            parser.error('query required')
        raise SystemExit(run(args.query))
