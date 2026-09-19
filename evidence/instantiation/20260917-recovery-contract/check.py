"""Record immutable targeted recovery diagnostics and software checks from a clean commit."""
import argparse
import datetime
import gzip
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import platform
import re
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / 'src'))
import diagnostics
from uppaal_mcp.integrated.generator import generate

# Reuse the already regression-tested process/error/verdict recorder, not its ACK runs.
spec = importlib.util.spec_from_file_location('ack_runner', ROOT / 'evidence/instantiation/20260916-ack-observer/check.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)
runner.ROOT = ROOT
SHA = lambda b: hashlib.sha256(b).hexdigest()


def dump(p, value):
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--verifyta', required=True)
    parser.add_argument('--timeout', type=float, default=60)
    parser.add_argument('--software-timeout', type=float, default=300)
    args = parser.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9_-]+', args.run_id):
        parser.error('run-id must be a simple unique name')
    if any(not math.isfinite(v) or v <= 0 for v in (args.timeout, args.software_timeout)):
        parser.error('timeouts must be positive finite seconds')
    if subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT):
        raise SystemExit('Commit all changes first; run requires clean source tree.')
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    out = HERE / 'runs' / args.run_id
    out.mkdir(parents=True, exist_ok=False)
    env = {k: v for k, v in os.environ.items() if not k.startswith('UPPAAL_')}
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    commands, records = [], []
    def execute(name, cmd, expected=None, limit=None):
        stdout, rec = runner.run_command(out, name, cmd, expected, limit or args.timeout, env)
        commands.append(rec)
        dump(out / 'commands.json', commands)
        print(name, rec['status'], rec['exit_code'], rec['verdicts'], flush=True)
        return stdout, rec
    version_bytes, version_rec = execute('version', [args.verifyta, '--version'])
    version = version_bytes.decode(errors='replace')
    def native(p):
        return runner.winpath(p) if args.verifyta.lower().endswith('.exe') else str(p)
    c = generate(ROOT)
    metadata = dict(c.metadata)
    metadata.pop('adaptations', None)  # Input/output XMLs and source commit already preserved.
    dump(out / 'composition.json', metadata)
    cases = [('integrated-parser', c.model_xml.encode(), [('engine load only', 'E<> true', True)],
              'Full integrated model engine load; no recovery/ACK property of full model checked.')]
    cases += diagnostics.cases(diagnostics.original_xml(), c.model_xml)
    for name, model, queries, scope in cases:
        p, q = out / (name + '.xml'), out / (name + '.q')
        p.write_bytes(model)
        qb = ('\n'.join(x[1] for x in queries) + '\n').encode()
        q.write_bytes(qb)
        expected = ['satisfied' if x[2] else 'NOT satisfied' for x in queries]
        cmd = [args.verifyta, '-q', '-t', '1', '-f', native(out / (name + '-trace')), native(p), native(q)]
        _, rec = execute(name, cmd, expected)
        rec.update(run_id=args.run_id + '-' + name, source_commit=commit,
                   model_hash=SHA(model), query_hash=SHA(qb), tool_version=version,
                   model_path=p.name, query_path=q.name, scope=scope,
                   per_query=[{'requirement': req, 'query': query, 'expected': exp,
                               'actual': rec['verdicts'][i] if i < len(rec['verdicts']) else None}
                              for i, ((req, query, _), exp) in enumerate(zip(queries, expected))])
        records.append(rec)
        dump(out / 'commands.json', commands)
        dump(out / 'results-index.json', records)
    execute('software', [sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v'], limit=args.software_timeout)
    execute('coordination', [sys.executable, '-B', 'scripts/check_coordination.py'])
    execute('mcp', [sys.executable, '-c', 'from uppaal_mcp.server import build_mcp; print(type(build_mcp()).__name__)'])
    execute('examples', [str(Path(sys.executable).parent / 'uppaal-verifyta'), 'list-examples'])
    execute('pip-check', [sys.executable, '-m', 'pip', 'check'])
    execute('diff', ['git', 'diff', '--check', diagnostics.BASE, '--', 'src', 'tests', str(HERE.relative_to(ROOT))])
    cpu = next((l.split(':', 1)[1].strip() for l in Path('/proc/cpuinfo').read_text().splitlines() if l.startswith('model name')), 'unknown')
    record = {'run_id':args.run_id, 'source_commit':commit, 'base_commit':diagnostics.BASE,
              'source_tree_clean_at_start':True, 'produced_by_github_handle':'vadimnbkg',
              'reviewed_by_github_handle':None, 'tool_version':version,
              'python':sys.version, 'operating_environment':platform.platform(),
              'hardware':{'cpu_model':cpu, 'logical_cpu_count':os.cpu_count(),
                          'ram_bytes':os.sysconf('SC_PAGE_SIZE')*os.sysconf('SC_PHYS_PAGES'),
                          'scope':'WSL host; Windows verifyta via WSL interop' if args.verifyta.endswith('.exe') else 'native'},
              'resource_limit':{'per_command_seconds':args.timeout, 'software_seconds':args.software_timeout, 'memory':'no explicit cap'},
              'parameter_set':c.metadata['parameter_set'], 'instance_vector':c.metadata['instance_vector'],
              'generator_hash':c.metadata['generator_hash'], 'model_hash':c.metadata['model_hash'], 'query_hash':c.metadata['query_hash'],
              'runner_exit_code':runner.run_exit_code(commands),
              'claim_limits':'Targeted diagnostic peers/mutants only; no full-model recovery/ACK proof, inevitable zero-time completion, physical calibration, P1/P2/Gate acceptance.'}
    dump(out / 'run.json', record)
    # Lossless, deterministic storage of large XMLs and machine traces. Hashes of
    # verifier inputs above refer to uncompressed bytes. Exact command paths can
    # be restored with python unpack.py RUN_DIRECTORY.
    packed = []
    for p in sorted(out.iterdir()):
        if p.suffix == '.xml' or '-trace-' in p.name or p.name.endswith(('.stdout.txt', '.stderr.txt')):
            raw = p.read_bytes()
            dest = p.with_name(p.name + '.gz')
            dest.write_bytes(gzip.compress(raw, mtime=0))
            packed.append({'path':p.name, 'sha256':SHA(raw), 'gzip_path':dest.name, 'gzip_sha256':SHA(dest.read_bytes())})
            p.unlink()
    dump(out / 'compressed-artifacts.json', packed)
    (out / 'SHA256SUMS').write_text(''.join(f'{SHA(p.read_bytes())}  {p.name}\n' for p in sorted(out.iterdir()) if p.is_file()))
    print('RUN', args.run_id, 'EXIT', record['runner_exit_code'], flush=True)
    return record['runner_exit_code']


if __name__ == '__main__':
    raise SystemExit(main())
