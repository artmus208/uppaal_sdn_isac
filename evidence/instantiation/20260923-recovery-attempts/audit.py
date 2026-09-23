"""Check saved #45 evidence bytes and result consistency; does not run UPPAAL."""
import hashlib
import json
from pathlib import Path
import tarfile


HERE = Path(__file__).resolve().parent


def main():
    publication = json.loads((HERE / 'publication.json').read_text())
    archive = HERE / publication['archive']
    assert hashlib.sha256(archive.read_bytes()).hexdigest() == publication['archive_sha256']
    with tarfile.open(archive) as tar:
        members = [m for m in tar if m.isfile()]
        assert len(members) == publication['archive_file_count']
        prefix = publication['run_id'] + '/'
        assert all(m.name.startswith(prefix) and '/' not in m.name[len(prefix):] for m in members)
        files = {m.name[len(prefix):]: tar.extractfile(m).read() for m in members}
        assert len(files) == len(members)
    indexed = set()
    for line in files['SHA256SUMS'].decode().splitlines():
        expected, name = line.split('  ', 1)
        assert name not in indexed
        indexed.add(name)
        assert hashlib.sha256(files[name]).hexdigest() == expected, name
    assert indexed == set(files) - {'SHA256SUMS'}
    for name in ['run.json', 'results-index.json', 'composition.json', 'commands.json']:
        assert (HERE / name).read_bytes() == files[name], name
    run = json.loads(files['run.json'])
    results = json.loads(files['results-index.json'])
    commands = json.loads(files['commands.json'])
    assert run['source_commit'] == publication['source_commit']
    assert run['source_tree_clean_at_start'] and run['runner_exit_code'] == 0
    assert all(c['exit_code'] == 0 and c['status'] not in ('error', 'timeout') for c in commands)
    assert files['version.stdout.txt'].decode() == run['tool_version']
    for result in results:
        assert result['status'] == 'success' and result['exit_code'] == 0
        assert result['source_commit'] == run['source_commit']
        assert result['tool_version'] == run['tool_version']
        assert hashlib.sha256(files[result['model_path']]).hexdigest() == result['model_hash']
        assert hashlib.sha256(files[result['query_path']]).hexdigest() == result['query_hash']
        assert result['verdicts'] == result['expected']
        for i, query in enumerate(result['per_query'], 1):
            assert query['actual'] == query['expected'] == result['verdicts'][i - 1]
            if query['actual'] == 'NOT satisfied' and query['query'].startswith('A[]'):
                assert files[f"{result['name']}-trace-{i}"], 'missing counterexample'
    import re
    for result in results:
        actual = re.findall(r'-- Formula is (NOT satisfied|satisfied)\.', files[result['stdout']].decode())
        assert actual == result['verdicts'], result['name']
    assert sum(len(r['per_query']) for r in results) == publication['query_results'] == 49
    assert b'Ran 178 tests' in files['software.stderr.txt']
    assert files['software.stderr.txt'].rstrip().endswith(b'OK')
    print(f"Evidence integrity OK: {len(files)} files, 49 recorded query results, 178 recorded software tests. No new model checking.")


if __name__ == '__main__':
    main()
