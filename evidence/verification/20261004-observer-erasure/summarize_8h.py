"""Audit completed 8-hour evidence; never launch or retry native verification."""
import csv
import json
from datetime import datetime
from pathlib import Path
import native_campaign_8h as campaign

HERE, ROOT, QUEUE, vm, base = (campaign.HERE, campaign.ROOT, campaign.QUEUE,
                               campaign.vm, campaign.base)


def summarize():
    protocol = vm.read(ROOT/'protocol.json')
    reservation = vm.read(ROOT/'reservation.json')
    config = vm.read(QUEUE/'queue.json')
    records = vm.read(ROOT/'results.json')
    exit_record = vm.read(ROOT/'worker-exit.json')
    assert exit_record['phase'] == 'finished' and exit_record['completed_attempts'] == 2
    assert not (ROOT/'worker-error.json').exists()
    assert len(records) == len(list(QUEUE.glob('attempts/*/result.json'))) == 2
    assert reservation['protocol_hash'] == vm.digest(ROOT/'protocol.json')
    assert reservation['execution_commit'] == '2a8b967e4899639c0e1b2ceb21b89a0ecc7a0e9c'
    vm.verify_inputs(QUEUE, config)
    pins = [(vm.__file__, 'manager_hash'), (campaign.__file__, 'driver_hash'),
            (base.__file__, 'base_driver_hash'),
            (base.REPO/'src/uppaal_mcp/windows_process.py', 'windows_process_hash'),
            (protocol['python'], 'python_hash'), (base.VERIFIER, 'verifier_hash')]
    for path, key in pins:
        assert vm.digest(path) == protocol[key], key
    old_inventory = vm.read(HERE/'artifact-hashes.json')
    historical = {p: h for p, h in old_inventory.items()
                  if p.startswith(('native/', 'native-30min/')) or
                  p in ('certificate.json', 'observer-erased.xml', 'premises.json')}
    for path, expected in historical.items():
        assert vm.digest(HERE/path) == expected, path
    assert vm.digest(base.REPO/'evidence/instantiation/uav-service-completion-candidate/model.xml') == 'b8ab50e112b71491f8242789cc7906497baf8440c473d7a5a4d5214840187e02'
    assert vm.digest(base.REPO/'manifests/baselines/uav-service-completion-r1.yaml') == '4b4bf71f55767123cc5934074024179289fa5ad3355fa4c0e37385e8261ef98d'
    verified_files = 0
    telemetry = []
    for task, query, record in zip(config['tasks'], base.QUERIES, records):
        path = HERE/record['result_path']
        raw = vm.read(path)
        assert vm.digest(path) == record['result_hash']
        assert all(record[key] == value for key, value in raw.items() if key != 'run_id')
        assert record['native_attempt_id'] == raw['run_id'] == path.parent.name
        assert record['run_id'] == protocol['run_mapping'][task['id']]
        assert record['execution_commit'] == reservation['execution_commit']
        assert record['model_hash'] == protocol['model_hash'] == config['model_hash']
        assert record['query_hash'] == task['query_hash']
        assert record['formula'] == task['query']
        original = base.REPO/'evidence/instantiation/uav-service-completion-candidate/queries'/(query+'.q')
        assert (QUEUE/task['file']).read_bytes() == original.read_bytes()
        assert record['timeout_seconds'] == 28800 and record['memory_stop_bytes'] == 7516192768
        assert record['status'] == 'memory_limit' and record['verdict'] is None
        assert not record.get('manager_error') and not record['trace_paths']
        assert record['command'] == [base.VERIFIER, '-o', '0', '-t', '0', '-X',
                                     str(path.parent/'trace'), str(QUEUE/'model.xml'), str(QUEUE/task['file'])]
        session = QUEUE/'sessions'/record['session']
        assert record['tool_version'] == vm.read(session/'session.json')['tool_version']
        assert record['tool_version'] == (session/'version.stdout.txt').read_text(encoding='utf-8')
        assert record['tool_version'].splitlines()[0] == 'UPPAAL 5.0.0 (rev. 714BA9DB36F49691), June 2023'
        for name, expected in vm.read(path.parent/'hashes.json').items():
            assert vm.digest(path.parent/name) == expected, name
            verified_files += 1
        with (path.parent/'telemetry.csv').open(newline='', encoding='utf-8') as stream:
            rows = list(csv.DictReader(stream))
        assert rows and float(rows[-1]['elapsed_seconds']) <= record['elapsed_seconds']
        assert max(int(row['peak_rss_bytes']) for row in rows) == record['peak_rss_bytes']
        assert float(rows[-1]['cpu_seconds']) == record['cpu_seconds']
        telemetry.append({'run_id': record['run_id'], 'samples': len(rows), 'last_sample': rows[-1]})
    assert datetime.fromisoformat(records[0]['finished_at']) <= datetime.fromisoformat(records[1]['started_at'])
    vm.save(ROOT/'validation.json', {
        'checked_at': vm.now(), 'input_runtime_command_version_result_bindings': 'match',
        'per_attempt_files_checked': verified_files,
        'historical_inventory_files_checked': len(historical),
        'exact_source_model_manifest_queries_and_diagnostic': 'unchanged',
        'sequential_nonoverlapping_attempts': True, 'telemetry': telemetry,
        'native_verdicts': [r['verdict'] for r in records],
        'scope': '29-process diagnostic composition; independent proof acceptance pending'})
    text = '# Completed 8-hour / 7-GiB native campaign\n\n'
    text += 'Both sequential attempts ended at the sampled memory stop, before their 28800-second time limits. Neither formula has a native verdict.\n\n'
    text += 'Native version: '+records[0]['tool_version'].splitlines()[0]+'.\n'
    text += 'Execution commit: '+reservation['execution_commit']+'. Fixed BFS options: -o 0 -t 0. Exact source queries and diagnostic model unchanged.\n\n'
    text += '| Run | Status | Verdict | Seconds | Peak bytes | CPU seconds |\n|---|---|---|---:|---:|---:|\n'
    for r in records:
        text += f"| {r['run_id']} | {r['status']} | none | {r['elapsed_seconds']:.3f} | {r['peak_rss_bytes']} | {r['cpu_seconds']:.3f} |\n"
    text += '\nThe sampled aggregate working-set stop is 7516192768 bytes (7168 MiB); polling permits a small overshoot. Worker exit code 2 records an incomplete verification campaign, not a manager exception: both planned attempts produced memory_limit records. No trace, retry, duplicate attempt, manager repair or recurring status-write error occurred.\n\n'
    text += 'Results.json preserves full commands, native version, model/query hashes, execution commit and raw result hashes. Validation.json records input/runtime pins, all per-attempt hashes, historical evidence checks and telemetry reconciliation. Load telemetry is not an independently established number of explored states.\n\n'
    text += 'Direct scope is the 29-process diagnostic XML. No property was proved or refuted by these runs; transfer to the 51-process model still requires independent proof acceptance. Increasing only the timeout cannot remove the observed memory stop. Remaining work is independent review and an explicitly chosen next experiment, without automatic retries.\n'
    (ROOT/'summary.md').write_text(text, encoding='utf-8', newline='\n')
    print(json.dumps({'attempts': len(records), 'files_checked': verified_files,
                      'historical_files_checked': len(historical), 'statuses': [r['status'] for r in records]}))


if __name__ == '__main__':
    summarize()
