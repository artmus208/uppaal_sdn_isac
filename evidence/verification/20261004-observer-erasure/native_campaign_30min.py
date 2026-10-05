"""User-authorized Issue #116 rerun: 1800 seconds per formula."""
import argparse
import sys
from pathlib import Path
import native_campaign as base

vm, HERE, REPO = base.vm, base.HERE, base.REPO
ROOT = HERE/'native-30min'

def queue_for(query, attempt):
    return ROOT/('observer-erasure-116-20261005-'+query+'-'+attempt)

def prepare(attempt):
    source = REPO/'evidence/instantiation/uav-service-completion-candidate/queries'
    if vm.digest(HERE/'observer-erased.xml') != 'b80db319ff7cdb511cb97aa155be01f1d68707358399fbe02fa39c1c6c32be6c':
        raise ValueError('Diagnostic XML changed')
    for query in base.QUERIES:
        queue = queue_for(query, attempt)
        vm.initialize(queue, HERE/'observer-erased.xml', source/(query+'.q'), base.VERIFIER, 1800, 2048)
        if (queue/'query-001.q').read_bytes() != (source/(query+'.q')).read_bytes():
            raise ValueError('Accepted query bytes changed')
    vm.save(ROOT/('protocol-'+attempt+'.json'), {
        'issue':116, 'authorization':'User requests 30-minute reruns and conditional status-write repair/rerun',
        'timeout_seconds':1800, 'memory_mib':2048, 'options':['-o','0','-t','0'],
        'model_hash':vm.digest(HERE/'observer-erased.xml'),
        'manager_hash':vm.digest(vm.__file__), 'driver_hash':vm.digest(__file__),
        'windows_process_hash':vm.digest(REPO/'src/uppaal_mcp/windows_process.py'),
        'python':sys.executable, 'python_hash':vm.digest(sys.executable),
        'verifier_hash':vm.digest(base.VERIFIER),
        'previous_protocol':'native/protocol.json',
        'repair_enabled':False,
        'monitoring':'Consume worker stdout; do not open hot status files through PowerShell',
        'direct_scope':'29-process diagnostic XML; transfer requires independent proof acceptance'})

def run(query, attempt):
    queue = queue_for(query, attempt)
    if (queue/'reservation.json').exists() or list(queue.glob('attempts/*')):
        raise ValueError('Already reserved; a retry needs its own run ID')
    if base.git('status','--porcelain','--untracked-files=all'):
        raise ValueError('Execution checkpoint must be clean')
    protocol = vm.read(ROOT/('protocol-'+attempt+'.json'))
    for actual, expected in [(vm.digest(vm.__file__),protocol['manager_hash']),
                             (vm.digest(__file__),protocol['driver_hash']),
                             (vm.digest(sys.executable),protocol['python_hash'])]:
        if actual != expected:
            raise ValueError('Pinned execution code changed')
    vm.verify_inputs(queue, vm.read(queue/'queue.json'))
    vm.save(queue/'reservation.json', {
        'run_id':queue.name, 'execution_commit':base.git('rev-parse','HEAD'),
        'clean_before_reservation':True, 'reserved_at':vm.now(),
        'driver_hash':vm.digest(__file__), 'manager_hash':vm.digest(vm.__file__),
        'model_hash':protocol['model_hash'],
        'query_hash':vm.read(queue/'queue.json')['tasks'][0]['query_hash'],
        'worker_command':[sys.executable,str(Path(__file__).resolve()),'run',query,'--attempt',attempt]})
    code = vm.main(['start',str(queue)])
    vm.save(queue/'worker-exit.json',{'exit_code':code,'finished_at':vm.now()})
    return code

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('prepare','run'))
    parser.add_argument('query',nargs='?',choices=base.QUERIES)
    parser.add_argument('--attempt',choices=('02','03'),default='02')
    args = parser.parse_args()
    if args.action == 'prepare':
        prepare(args.attempt)
    elif args.query:
        raise SystemExit(run(args.query,args.attempt))
    else:
        parser.error('query required')
