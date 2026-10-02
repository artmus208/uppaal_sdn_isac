"""Derive run metadata/event table from retained engine outputs; no engine calls."""
import csv
import json
from pathlib import Path
from audit import HERE, ROOT, digest, interval, load, steps


def main():
    model = ROOT / 'evidence/scalability/family-series-68/generated/n1/model.xml'
    cells = []
    for folder in sorted((HERE / 'runs').iterdir()):
        r, p, m = load(folder / 'result.json'), load(folder / 'provenance.json'), load(folder / 'monitor.json')
        cells.append({'run_id': p['run_id'], 'method': p['method'], 'status': r['status'],
                      'model_hash': r['model_hash'], 'query_hash': None, 'property_verdict': None,
                      'source_commit': p['source_commit'], 'baseline_id': p['baseline_id'],
                      'tool_version': r['tool_version'], 'command': p['command'],
                      'operating_environment': p['operating_environment'], 'hardware': load(folder / 'hardware.json'),
                      'runtime_seconds': m['runtime_seconds'], 'peak_memory_bytes': m['peak_tree_sample_bytes'],
                      'accepted_transitions': r['accepted_transitions'], 'process_tree_reaped': m['process_tree_reaped'],
                      'started_at_utc': m['started_utc'], 'finished_at_utc': m['finished_utc'],
                      'parameter_set_ref': str(model.parent.relative_to(ROOT) / 'parameters.json'),
                      'instance_vector_ref': str(model.parent.relative_to(ROOT) / 'instance-vector.json'),
                      'stdout_reference': str((folder / 'stdout.txt.gz').relative_to(HERE)),
                      'stderr_reference': str((folder / 'stderr.txt.gz').relative_to(HERE)),
                      'trace_reference': str((folder / ('trace.xtr.xz' if r['mode'] == 'simulate' else 'reachable-prefix.xtr.xz')).relative_to(HERE)),
                      'reason': r.get('reason')})
    summary = {'issue': 80, 'atomic_ids': ['R07'], 'evidence_kind': 'simulation',
               'status': 'candidate_APP_rejection_and_violation_report', 'property_verdict': None, 'query_hash': None,
               'accepted_verification_run_id': None, 'acceptance_status': 'candidate_pending_independent_review',
               'base_commit': '91113a1b634f030c7e895f54f5c36a0b140d66eb',
               'branch': 'codex/vadimnbkg/80-r07-service-trace', 'model_hash': digest(model.read_bytes()),
               'baseline_id': 'uav-family-r1-20260929', 'baseline_manifest_hash': digest((ROOT / 'manifests/baselines/uav-family-r1.yaml').read_bytes()),
               'parameter_set': load(model.parent / 'parameters.json'), 'instance_vector': load(model.parent / 'instance-vector.json'),
               'query_set_hash_not_executed': digest((model.parent / 'queries.q').read_bytes()),
               'total_native_wall_seconds': sum(load(folder / 'native-summary.json')['total_wall_seconds'] for folder in (HERE / 'runs').iterdir()),
               'APP_outcome': 'Rejected', 'service_completed': False, 'report_time_abstract': 5,
               'observed_report_elapsed_abstract': 0, 'report_deadline_abstract': 3,
               'open_dependencies': ['P5-applicable Gate 1 disposition', 'P3_core_evidence_accepted for exact UAV N=1',
                                     'matching accepted verification run', 'independent reviewer appointment and acceptance'],
               'runs': cells}
    (HERE / 'results.json').write_text(json.dumps(summary, indent=2) + '\n')
    result = load(HERE / 'runs/replay001/result.json')
    ss = steps(HERE / 'runs/replay001/steps.jsonl')
    mapping = load(HERE / 'model-map.json')
    names = result['variable_names']
    meaningful = ['u0_phy_env_scenario', 'u0_phy_PdClass', 'u0_phy_sensing_degraded_flag',
                  'u0_app_service_request_pending', 'u0_app_admissionClass', 'u0_app_pdClass',
                  'u0_app_missedDetectionClass', 'u0_app_detectionFreshnessClass', 'u0_app_updatePeriodClass',
                  'u0_mac_scheduleMode', 'u0_sdn_policyClass', 'u0_sdn_telemetryClass',
                  'u0_bus_mac_report_consumed', 'u0_bus_outcome_for_request', 'u0_bus_violation_recorded']
    notes = {1: 'The only demand creates a strict safety-critical UAV sensing request.',
             4: 'APP request sent; APP admission clock resets. Single service-context correlation begins.',
             6: 'Captured request forwarded to SDN Evaluate; decision clock resets.',
             15: 'SharedLoad chooses one queue arrival before its optional service epoch.',
             18: 'MAC tick starts KPI collection.',
             43: 'PHY input publishes PD_FAILED, MISS_CRITICAL and sensing-degraded scenario.',
             46: 'Channel report wakes sensing evaluation and PHY aggregate.',
             47: 'Sensing report sets degraded flag; highest_priority_SQ assigns SensingState=7.',
             48: 'Aggregate publishes PHY sensing-degraded KPI to boundary.',
             50: 'Fresh KPI maps detection/miss to APP and degradation to SDN; shared fan-out.',
             51: 'MAC consumes the PHY report and enters SelectMode.',
             52: 'SDN monitor receives PHY notification. Pending policy evaluation reads mapped telemetry.',
             53: 'APP KPI broadcast occurs while request is pending; A_REQ does not receive it in RequestPending.',
             54: 'Violation notification moves A_SLA to SLAViolated and resets response clock.',
             58: 'MAC selects JOINT. This is a scheduler choice, not successful APP service.',
             59: 'SDN sensing boost proposes degraded admission for the captured request.',
             60: 'Bridge maps ADM_DEGRADED to APP with sensing-failure reason.',
             61: 'Safety guard forbids degraded sensing and converts admission to rejected.',
             62: 'APP receives service_reject and clears pending; A_REQ reaches Rejected.',
             63: 'APP sends SLA violation report; environment records it. Pre-report elapsed=0 <= 3.'}
    rows = []
    for prev, s in zip(ss, ss[1:]):
        index = s['state_index'];v = dict(zip(names, s['snapshot']['values']));old = dict(zip(names, prev['snapshot']['values']))
        edge_records = []
        for edge in s['edges'].split(';'):
            if not edge.strip():
                continue
            ids = [int(i) for i in edge.split()];entry = mapping[ids[0]];t = entry['transitions'][ids[1]]
            edge_records.append((entry['process'], t))
        processes = '; '.join(p for p, _ in edge_records)
        transitions = '; '.join(f"{p}: {t['source']}->{t['target']} [{t['labels'].get('synchronisation', 'internal')}]" for p, t in edge_records)
        changes = '; '.join(f'{k}: {old[k]}->{v[k]}' for k in meaningful if old[k] != v[k])
        changes += '; '.join(f"; {mapping[i]['process']}: {a}->{b}" for i, (a, b) in enumerate(zip(prev['snapshot']['locations'], s['snapshot']['locations'])) if a != b)
        rows.append({'step': index, 'time_or_clock_constraint': '#time in ' + interval(s['snapshot']['zone'], 1),
                     'automata_or_layers': processes, 'transition_or_channel': transitions,
                     'state_changes': changes, 'meaning': notes.get(index, 'Reachable prefix transition; see full machine state and model-map.json.'),
                     'machine_reference': f'runs/replay001/steps.jsonl.gz: state_index={index}'})
    with (HERE / 'scenario-events.csv').open('w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=rows[0].keys(), lineterminator='\n');writer.writeheader();writer.writerows(rows)
    lines = ['# Selected events; full 63-step table in scenario-events.csv', '',
             'Times are marginal bounds from reachable prefix DBMs, not independently chosen timestamps. The t=5 suffix is fixed consistently by the engine path. All units are abstract.', '',
             '| Step | Reachable time | Event | Machine reference |', '|---:|---|---|---|']
    for row in rows:
        if row['step'] in notes:
            lines.append(f"| {row['step']} | {row['time_or_clock_constraint']} | {row['meaning']} | state_index={row['step']} |")
    lines.extend(['', 'All references address `runs/replay001/steps.jsonl.gz`. The full CSV includes participating processes, channels and changed values/locations.'])
    (HERE / 'scenario-events.md').write_text('\n'.join(lines) + '\n')
    print(json.dumps({'runs': len(cells), 'events': len(rows), 'native_wall_seconds': summary['total_native_wall_seconds']}))


if __name__ == '__main__':
    main()
