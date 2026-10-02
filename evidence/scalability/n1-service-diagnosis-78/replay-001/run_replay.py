"""Build and run the three fixed native directed-replay cells; never query verifyta."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
UPPAAL = Path('/mnt/c/Program Files (x86)/UPPAAL-5.0.0')
JDK = Path('/mnt/c/Program Files/Eclipse Adoptium/jdk-17.0.19.10-hotspot')
MODEL = ROOT / 'evidence/scalability/family-series-68/generated/n1/model.xml'
TRACE = HERE.parent / 'manual-001/05-service-before-overflow.xtr'
PINS = {MODEL: '5234cb087e5274798926d516dedc77d1f9542ea7df59cec39f83859771ce1385',
        TRACE: '8186e1b68324ba288abe6249abdc73fa771400d95414d4bf77d2d1f9fdfbfcf7'}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def windows(path):
    return subprocess.check_output(['wslpath', '-w', str(path)], text=True, timeout=5).strip()


def call(argv, name, cwd, timeout=30):
    completed = subprocess.run(argv, cwd=cwd, capture_output=True, timeout=timeout)
    (HERE / (name + '.stdout.txt')).write_bytes(completed.stdout)
    (HERE / (name + '.stderr.txt')).write_bytes(completed.stderr)
    if completed.returncode:
        raise RuntimeError(f'{name}: exit {completed.returncode}; inspect raw logs')
    return completed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    for path, expected in PINS.items():
        assert sha(path) == expected, path
    build = Path('/tmp/uppaal-replay-build')
    build.mkdir(exist_ok=True)
    compile_argv = [str(JDK / 'bin/javac.exe'), '-encoding', 'UTF-8', '-cp', windows(UPPAAL / 'lib/model.jar'),
                    '-d', windows(build), windows(HERE / 'TimedReplay.java')]
    call(compile_argv, 'compile', UPPAAL)
    cp = ';'.join([windows(build), windows(UPPAAL / 'lib') + '\\*', windows(UPPAAL / 'uppaal.jar')])
    java = [str(JDK / 'bin/java.exe'), '-Xmx512m', '-Djava.awt.headless=true', '-cp', cp, 'TimedReplay']
    call(java + ['--self-test', windows(TRACE)], 'selftest', UPPAAL)
    call(java + ['--model-test', windows(MODEL)], 'model-load-test', UPPAAL)
    if not args.execute:
        print('Build/parser/DBM controls passed; engine not invoked')
        return
    assert not subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT), 'Commit build logs and source before --execute'
    campaign = HERE / 'native-002'
    campaign.mkdir()  # unique output; refusal to overwrite or retry
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    cells = []
    for mode in ('replay', 'negative-discrete', 'negative-clock'):
        out = campaign / mode
        out.mkdir()
        argv = java + [windows(UPPAAL / 'bin/server.exe'), windows(MODEL), windows(TRACE), windows(out), mode]
        cells.append({'mode': mode, 'run_id': 'n1-service-78-replay-001-' + mode,
                      'command': argv, 'argument_string': subprocess.list2cmdline(argv[1:]),
                      **{key: windows(out / file) for key, file in {
                          'hardware': 'hardware.json', 'stdout': 'stdout.txt', 'stderr': 'stderr.txt',
                          'memory': 'memory.csv', 'monitor': 'monitor.json', 'owned': 'owned.json', 'result': 'result.json'}.items()}})
    config = {'java': windows(JDK / 'bin/java.exe'), 'cwd': windows(UPPAAL), 'cells': cells,
              'prior_native_wall_seconds': 2.2721119,
              'summary': windows(campaign / 'native-summary.json')}
    config_path = campaign / 'config.json'
    config_path.write_text(json.dumps(config, indent=2) + '\n')
    hashes = {str(p): sha(p) for p in [MODEL, TRACE, HERE / 'TimedReplay.java', HERE / 'native.ps1', HERE / 'run_replay.py',
                                     UPPAAL / 'bin/server.exe', UPPAAL / 'lib/model.jar', UPPAAL / 'uppaal.jar', JDK / 'bin/java.exe']}
    provenance = {'source_commit': head, 'input_checkpoint': 'b403fd3903b1d9f925cb51382ba5433810612f99',
                  'hashes': hashes, 'compile_command': compile_argv, 'python': os.sys.version,
                  'execution_status': 'started', 'property_verdict': None}
    (campaign / 'provenance.json').write_text(json.dumps(provenance, indent=2) + '\n')
    command = ['/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe', '-NoProfile', '-NonInteractive',
               '-ExecutionPolicy', 'Bypass', '-File', windows(HERE / 'native.ps1'), '-ConfigPath', windows(config_path)]
    started = time.monotonic()
    try:
        completed = subprocess.run(command, cwd=UPPAAL, capture_output=True, timeout=315)
    except subprocess.TimeoutExpired:
        cleanup = [command[0], '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-File',
                   windows(HERE / 'cleanup.ps1'), '-Root', windows(campaign)]
        rescue = subprocess.run(cleanup, cwd=UPPAAL, capture_output=True, timeout=20)
        (campaign / 'watchdog-cleanup.stdout.txt').write_bytes(rescue.stdout)
        (campaign / 'watchdog-cleanup.stderr.txt').write_bytes(rescue.stderr)
        provenance.update(execution_status='wrapper_timeout', cleanup_exit=rescue.returncode)
        (campaign / 'provenance.json').write_text(json.dumps(provenance, indent=2) + '\n')
        raise
    (campaign / 'wrapper.stdout.txt').write_bytes(completed.stdout)
    (campaign / 'wrapper.stderr.txt').write_bytes(completed.stderr)
    provenance.update(execution_status='wrapper_complete' if completed.returncode == 0 else 'wrapper_error',
                      wrapper_command=command, wrapper_exit=completed.returncode, wall_seconds=time.monotonic()-started)
    (campaign / 'provenance.json').write_text(json.dumps(provenance, indent=2) + '\n')
    print(json.dumps(provenance))
    if completed.returncode:
        raise RuntimeError('Native campaign wrapper failed; preserve outputs and do not retry')


if __name__ == '__main__':
    main()
