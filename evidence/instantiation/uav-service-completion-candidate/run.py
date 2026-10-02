"""Native bounded Issue #82 simulation/replay; immutable unique run directories."""
import argparse
import hashlib
import json
import platform
from pathlib import Path
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
UPPAAL = Path('/mnt/c/Program Files (x86)/UPPAAL-5.0.0')
JDK = Path('/mnt/c/Program Files/Eclipse Adoptium/jdk-17.0.19.10-hotspot')
MODEL = HERE / 'model.xml'
BUILD = Path('/tmp/uppaal-service-82-build')
HELPER = ROOT / 'evidence/scalability/n1-service-diagnosis-78/replay-001/TimedReplay.java'
PS = '/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe'


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def win(p):
    return subprocess.check_output(['wslpath', '-w', str(p)], text=True, timeout=5).strip()


def write(p, data):
    p.write_text(json.dumps(data, indent=2) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', action='store_true')
    parser.add_argument('--cell', choices=['simulate', 'replay', 'negative-discrete', 'negative-clock'])
    parser.add_argument('--name')
    parser.add_argument('--input', type=Path)
    args = parser.parse_args()
    model_hash = json.loads((HERE / 'inventory.json').read_text())['model_hash']
    assert sha(MODEL) == model_hash
    BUILD.mkdir(exist_ok=True)
    if args.build:
        cmd = [str(JDK / 'bin/javac.exe'), '-encoding', 'UTF-8', '-cp', win(UPPAAL / 'lib/model.jar'),
               '-d', win(BUILD), win(HELPER), win(HERE / 'CausalReplay.java')]
        done = subprocess.run(cmd, cwd=UPPAAL, capture_output=True, timeout=30)
        (HERE / 'compile.stdout.txt').write_bytes(done.stdout)
        (HERE / 'compile.stderr.txt').write_bytes(done.stderr)
        write(HERE / 'compile.json', {'command': cmd, 'exit_code': done.returncode, 'engine_invoked': False})
        print('compile exit', done.returncode)
        if done.returncode == 0:
            cp = ';'.join([win(BUILD), win(UPPAAL / 'lib') + '\\*', win(UPPAAL / 'uppaal.jar')])
            check = [str(JDK / 'bin/java.exe'), '-Xmx512m', '-Djava.awt.headless=true', '-cp', cp,
                     'CausalReplay', '--model-check', win(MODEL)]
            loaded = subprocess.run(check, cwd=UPPAAL, capture_output=True, timeout=30)
            (HERE / 'model-load.stdout.txt').write_bytes(loaded.stdout)
            (HERE / 'model-load.stderr.txt').write_bytes(loaded.stderr)
            write(HERE / 'model-load.json', {'command': check, 'exit_code': loaded.returncode, 'engine_invoked': False})
            return loaded.returncode
        return done.returncode
    assert args.cell and args.name and args.input
    assert not subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT), 'Checkpoint before execution'
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    prior = sum(json.loads(p.read_text())['total_wall_seconds'] for p in (HERE / 'runs').glob('*/native-summary.json')) if (HERE / 'runs').exists() else 0
    assert prior < 510, 'Native campaign reserve'
    runs = list((HERE / 'runs').glob('*/provenance.json')) if (HERE / 'runs').exists() else []
    assert len(runs) < 9, 'Fixed invocation budget including setup errors and a diagnosed freshness-boundary correction'
    out = HERE / 'runs' / args.name
    out.mkdir(parents=True, exist_ok=False)
    cp = ';'.join([win(BUILD), win(UPPAAL / 'lib') + '\\*', win(UPPAAL / 'uppaal.jar')])
    argv = [str(JDK / 'bin/java.exe'), '-Xmx512m', '-Djava.awt.headless=true', '-cp', cp, 'CausalReplay',
            win(UPPAAL / 'bin/server.exe'), win(MODEL), win(args.input.resolve()), win(out), args.cell, model_hash]
    native_argv = [win(JDK / 'bin/java.exe')] + argv[1:]
    cell = {'mode': args.cell, 'run_id': 'uav-completion-82-20261002-' + args.name, 'command': native_argv,
            'argument_string': subprocess.list2cmdline(native_argv[1:]),
            **{k: win(out / f) for k, f in {'hardware': 'hardware.json', 'stdout': 'stdout.txt',
            'stderr': 'stderr.txt', 'memory': 'memory.csv', 'monitor': 'monitor.json',
            'owned': 'owned.json', 'result': 'result.json'}.items()}}
    # One cell per monitored wrapper; prior accounted by runner, summary remains incremental.
    cfg = {'java': win(JDK / 'bin/java.exe'), 'cwd': win(UPPAAL), 'cells': [cell],
           'prior_native_wall_seconds': 0, 'summary': win(out / 'native-summary.json')}
    write(out / 'config.json', cfg)
    inputs = [MODEL, args.input.resolve(), HERE / 'PROTOCOL.md', HERE / 'CausalReplay.java',
              HERE / 'run.py', HERE / 'native.ps1', HELPER, UPPAAL / 'bin/server.exe',
              UPPAAL / 'lib/model.jar', UPPAAL / 'uppaal.jar', JDK / 'bin/java.exe',
              ROOT / 'manifests/baselines/uav-family-r1.yaml', MODEL.parent / 'parameters.json', MODEL.parent / 'instance-vector.json', HERE / 'generate.py', HERE / 'inventory.json', HERE / 'cleanup.ps1']
    provenance = {'run_id': cell['run_id'], 'method': 'directed_symbolic_simulation' if args.cell == 'simulate' else 'symbolic_replay',
                  'source_commit': head, 'base_commit': '91113a1b634f030c7e895f54f5c36a0b140d66eb',
                  'baseline_id': None, 'candidate_id': 'uav-service-completion-candidate-82-n1', 'historical_input_baseline_id': 'uav-family-r1-20260929', 'model_hash': model_hash, 'generator_hash': sha(HERE / 'generate.py'), 'query_pack_hash': sha(HERE / 'inventory.json'), 'hashes': {str(p): sha(p) for p in inputs},
                  'command': native_argv, 'python': sys.version, 'operating_environment': platform.platform(),
                  'property_verdict': None, 'query_hash': None, 'prior_native_seconds': prior}
    write(out / 'provenance.json', provenance)
    command = [PS, '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-File', win(HERE / 'native.ps1'),
               '-ConfigPath', win(out / 'config.json')]
    started = time.monotonic()
    try:
        done = subprocess.run(command, cwd=UPPAAL, capture_output=True, timeout=80)
        (out / 'wrapper.stdout.txt').write_bytes(done.stdout)
        (out / 'wrapper.stderr.txt').write_bytes(done.stderr)
        provenance.update(wrapper_exit=done.returncode, wrapper_status='complete', wall_seconds=time.monotonic()-started)
    except subprocess.TimeoutExpired as exc:
        (out / 'wrapper.stdout.txt').write_bytes(exc.stdout or b'')
        (out / 'wrapper.stderr.txt').write_bytes(exc.stderr or b'')
        rescue = subprocess.run([PS, '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-File', win(HERE / 'cleanup.ps1'), '-Root', win(out)], cwd=UPPAAL, capture_output=True, timeout=20)
        (out / 'cleanup.stdout.txt').write_bytes(rescue.stdout)
        (out / 'cleanup.stderr.txt').write_bytes(rescue.stderr)
        provenance.update(wrapper_status='timeout', cleanup_exit=rescue.returncode, wall_seconds=time.monotonic()-started)
    write(out / 'provenance.json', provenance)
    result = json.loads((out / 'result.json').read_text()) if (out / 'result.json').exists() else {'status': 'no_result'}
    print(json.dumps({'run_id': cell['run_id'], 'status': result['status'], 'accepted_transitions': result.get('accepted_transitions'), 'error': result.get('error')}))
    return 0 if provenance['wrapper_status'] == 'complete' and provenance['wrapper_exit'] == 0 else 2


if __name__ == '__main__':
    raise SystemExit(main())
