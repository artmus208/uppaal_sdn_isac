"""Record Gate 1 static/software readiness; never invoke model checking."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
BASE = 'bb5741b45480944630e1116fb7435effb2026655'
HIST = ROOT / 'evidence/instantiation/20260908-p2-integrated/reviewer-scoped-005-20260908'
SCOPE = HERE.relative_to(ROOT).as_posix() + '/'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def write(path, value):
    path.write_bytes((json.dumps(value, indent=2, ensure_ascii=False) + '\n').encode())


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT).decode().strip()


def index_check(directory):
    records = []
    for line in (directory / 'SHA256SUMS').read_text().splitlines():
        expected, name = line.split('  ', 1)
        path = (directory / name).resolve()
        if not path.is_relative_to(directory.resolve()):
            raise ValueError('checksum path escapes directory')
        actual = sha(path.read_bytes())
        records.append({'path': name, 'sha256': actual, 'matches': actual == expected})
    if not all(x['matches'] for x in records):
        raise ValueError('historical checksum mismatch')
    return records


def compare(output):
    """Compare all metadata except the explicitly different execution commit."""
    current = json.loads((output / 'generated/composition.json').read_bytes())
    historical = json.loads((HIST / 'generated/composition.json').read_bytes())
    comparison = {k: current[k] == historical[k] for k in current if k != 'source_commit'}
    assert set(current) == set(historical)
    assert all(comparison.values()), comparison
    for name in ('model.xml', 'queries.q'):
        assert (output / 'generated' / name).read_bytes() == (HIST / 'generated' / name).read_bytes()
    sources = dict(current['source_hashes'], **current['implementation_sources'])
    sources.update({k: v['actual_sha256'] for k, v in current['context_document_hashes'].items()})
    source_records = []
    for path, expected in sorted(sources.items()):
        raw = (ROOT / path).read_bytes()
        blob = subprocess.check_output(['git', 'show', f'{BASE}:{path}'], cwd=ROOT)
        assert sha(raw) == expected and raw == blob, path
        source_records.append({'path': path, 'sha256': expected, 'equals_base_git_blob': True})
    xml = ET.fromstring((output / 'generated/model.xml').read_bytes())
    templates = {t.findtext('name'): t for t in xml.findall('template')}
    instances = dict(re.findall(r'(\w+)\s*=\s*(\w+)\(\);', xml.findtext('system')))
    order = re.search(r'\bsystem\s+([^;]+);', xml.findtext('system'))[1].split(', ')
    assert order == current['system_order'] and set(order) == set(instances)
    assert all(t in templates for t in instances.values())
    counts = {'core': sum(not p.startswith(('obs_', 'boundary_')) for p in order),
              'boundary': sum(p.startswith('boundary_') for p in order),
              'observers': sum(p.startswith('obs_') for p in order), 'total': len(order)}
    assert counts == current['instance_vector']['expected_process_counts']
    for t in templates.values():
        ids = {x.get('id') for x in t.findall('location')}
        for node in t.iter():
            if node.tag in ('source', 'target', 'init'):
                assert node.get('ref') in ids
    queries = current['query_map']
    assert len({q['id'] for q in queries}) == len(queries)
    text = ''.join(f"// {q['id']} -- candidate, no verdict\n{q['candidate']}\n" for q in queries if 'candidate' in q)
    assert text.encode() == (output / 'generated/queries.q').read_bytes()
    for p, loc in re.findall(r'\b(\w+)\.(\w+)', text):
        assert p in instances and loc in [x.findtext('name') for x in templates[instances[p]].findall('location')]
    maps = {'parameter-set': {'boundary_policy': current['parameter_set'],
                             'source_parameters': current['source_parameters'],
                             'constant_declarations': re.findall(r'\bconst\s+int\s+[^;]+;', xml.findtext('declaration')),
                             'time_unit': 'abstract_model_unit', 'physical_time_scale_seconds': None,
                             'interpretation': 'All constant declarations retained verbatim; numeric bounds also occur in guards, pinned by model_hash.'},
            'instance-vector': current['instance_vector'], 'query-map': queries,
            'interface-map': {'channels': current['channels'], 'process_map': current['process_map'],
                              'system_order': order},
            'source-hashes': current['source_hashes'],
            'implementation-hashes': current['implementation_sources']}
    map_hashes = {}
    for name, value in maps.items():
        path = output / (name + '.json')
        write(path, value)
        map_hashes[name] = {'path': path.relative_to(ROOT).as_posix(), 'sha256': sha(path.read_bytes())}
    manifest_paths = ['AGENTS.md', 'CONTRIBUTING.md', 'manifests/v1.md',
                      'manifests/collaboration-v1.yaml', 'manifests/baselines/reviewer-r1.yaml',
                      'levels_tex/samplepaper.tex', 'pdfs/018100004273.pdf',
                      'evidence/validation/20260907-p1/validation-report.md',
                      'evidence/validation/20260907-p1/inventory.json',
                      'evidence/instantiation/20260907-p2-scope/model-scope-specification.md',
                      'evidence/instantiation/20260907-p2-scope/decisions.md',
                      'evidence/instantiation/20260907-p2-scope/interface-contract.md',
                      'evidence/instantiation/20260908-p2-integrated/decisions.md']
    document_hashes = {p: sha((ROOT / p).read_bytes()) for p in manifest_paths}
    for p, h in document_hashes.items():
        assert sha(subprocess.check_output(['git', 'show', f'{BASE}:{p}'], cwd=ROOT)) == h
    history = {str(p.relative_to(ROOT)): index_check(p) for p in [HIST,
        ROOT / 'evidence/validation/20260907-p1', ROOT / 'evidence/instantiation/20260907-p2-scope']}
    report = {'base_commit': BASE, 'execution_commit': current['source_commit'],
              'historical_execution_commit': historical['source_commit'],
              'historical_published_equivalent_commit': '87d1b1055e2ff320715c8792ce468f4b42775d0f',
              'metadata_equal_except_source_commit': comparison, 'model_query_bytes_identical': True,
              'source_records': source_records, 'process_counts': counts,
              'query_count': sum('candidate' in q for q in queries),
              'excluded_query_ids': [q['id'] for q in queries if 'candidate' not in q],
              'maps': map_hashes, 'document_hashes': document_hashes,
              'historical_checksum_records': history,
              'verification_status': 'not_run'}
    write(output / 'comparison.json', report)
    print(json.dumps({'static_comparison': 'success', 'counts': counts,
                      'query_count': report['query_count'], 'source_files': len(source_records),
                      'historical_indexed_files': sum(map(len, history.values()))}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--compare-only', action='store_true')
    parser.add_argument('--verifyta', type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to(HERE):
        parser.error('output must be inside Issue #21 scope')
    if args.compare_only:
        compare(output)
        return 0
    status = git('status', '--short')
    if status:
        raise RuntimeError('clean committed checkout required: ' + status)
    changed = git('diff', '--name-only', BASE, 'HEAD').splitlines()
    assert all(p.startswith(SCOPE) for p in changed), changed
    output.mkdir(parents=True, exist_ok=False)
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1')
    env.pop('PYTHONPATH', None)
    n = int(env.get('GIT_CONFIG_COUNT', '0'))
    env.update({f'GIT_CONFIG_KEY_{n}': 'core.autocrlf', f'GIT_CONFIG_VALUE_{n}': 'false', 'GIT_CONFIG_COUNT': str(n+1)})
    python = os.path.abspath(sys.executable)
    report = {'run_id': output.name, 'issue': 21, 'base_commit': BASE,
              'source_commit': git('rev-parse', 'HEAD'), 'worktree_status_at_start': status,
              'base_to_execution_changed_paths': changed, 'cwd': str(ROOT),
              'evidence_class': 'static_and_software_readiness', 'verification_status': 'not_run',
              'licensing_model_checking_status': 'not_tested', 'python': python,
              'operating_environment': platform.platform(),
              'hardware': {'cpu': platform.processor(), 'logical_cpu_count': os.cpu_count(),
                           'ram_bytes': os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES')},
              'environment_overrides': {'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONUTF8': '1', 'core.autocrlf': 'false'},
              'commands': []}
    commands = [
        ('versions', [python, '-c', 'import sys,importlib.metadata as m; print(sys.version); print("mcp="+m.version("mcp")); print("PyYAML="+m.version("PyYAML"))']),
        ('pip-check', [python, '-m', 'pip', 'check']),
        ('pip-freeze', [python, '-m', 'pip', 'freeze']),
        ('generate', [python, '-B', '-m', 'uppaal_mcp.integrated.generator', '--output', str(output / 'generated')]),
        ('compare', [python, '-B', str(Path(__file__).resolve()), '--output', str(output), '--compare-only']),
        ('historical-audit', [python, '-B', 'evidence/instantiation/20260908-p2-integrated/audit.py', str(HIST)]),
        ('coordination', [python, '-B', 'scripts/check_coordination.py']),
        ('yaml', [python, '-c', 'import pathlib,yaml; p=list(pathlib.Path("manifests").rglob("*.yaml")); [yaml.safe_load(x.read_text()) for x in p]; print(len(p),"YAML manifests parsed")']),
        ('unit-tests', [python, '-B', '-m', 'unittest', 'discover', '-s', 'tests', '-v']),
        ('mcp-construction', [python, '-c', 'from uppaal_mcp.server import build_mcp; print(type(build_mcp()).__name__)']),
        ('examples', [str(Path(python).parent / 'uppaal-verifyta'), 'list-examples']),
        ('diff-check', ['git', 'diff', '--check', BASE + '...HEAD']),
    ]
    if args.verifyta:
        commands.append(('verifyta-version', [str(args.verifyta), '--version']))
    for name, command in commands:
        start = datetime.datetime.now(datetime.timezone.utc).isoformat()
        tick = time.monotonic()
        try:
            result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, timeout=180 if name == 'unit-tests' else 30)
            code, stdout, stderr = result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired as exc:
            code, stdout, stderr = None, exc.stdout or b'', exc.stderr or b''
        except OSError as exc:
            code, stdout, stderr = None, b'', str(exc).encode()
        record = {'name': name, 'command': command, 'exit_code': code, 'started_at_utc': start,
                  'finished_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  'runtime_seconds': time.monotonic()-tick, 'status': 'success' if code == 0 else 'error_or_timeout'}
        for stream, raw in [('stdout', stdout), ('stderr', stderr)]:
            path = output / f'{name}.{stream}.log'
            path.write_bytes(raw)
            record[stream + '_path'] = path.name
            record[stream + '_sha256'] = sha(raw)
        report['commands'].append(record)
        write(output / 'checks.json', report)
        print(name + ': exit=' + str(code), flush=True)
    return int(any(x['exit_code'] != 0 for x in report['commands']))


if __name__ == '__main__':
    raise SystemExit(main())
