#!/usr/bin/env python3
"""Derive the review matrix and Gate 1 candidate references from immutable runs."""
import json
import generate as g


def main():
    campaign = 'diagnostic-001'
    folder = g.HERE/'checks'/campaign
    settings = json.loads((folder/'settings.json').read_text())
    if not settings.get('completed_at_utc'):
        raise SystemExit('campaign is incomplete; do not write a final summary')
    runs = json.loads((folder/'runs.json').read_text())
    if any(r['runtime_seconds'] > 60 for r in runs):
        raise SystemExit('actual invocation exceeded the user bound; report this before summarizing')
    selected = {(r['N'], r['query_id']): r for r in runs if r['N']}

    def outcome(n, query):
        row = selected.get((n, query))
        if not row:
            return 'not run'
        return row['property_verdict'] or row['status']

    lines = ['# Recorded preparation outcomes', '',
             'These are full-composition diagnostic runs, not a P4 resource series or Gate 1 decision.', '',
             f"Source commit: `{settings['source_commit']}` (published, clean at campaign start).",
             f"Actual tool: **{runs[0]['tool_version']}**.", '',
             '| N | Automata | Compile | Load/parse | Capacity | Each service i=0…N−1 | Joint encoded backlog | u0 queue safety | u0 queue full |',
             '|---|---:|---|---|---|---|---|---|---|']
    for n in g.SIZES:
        values = [str(n), str(49*n+1), outcome(n, 'compile-only'), outcome(n, 'initial-load'),
                  outcome(n, 'shared-capacity'), ', '.join(outcome(n, f'u{i}-service') for i in range(n)),
                  outcome(n, 'joint-backlog'), outcome(n, 'u0-queue-safety'), outcome(n, 'u0-queue-full')]
        lines.append('| '+' | '.join(values)+' |')
    budget = sum(r['runtime_seconds'] for r in runs)
    peak = max(max(r['peak_private_bytes'], r['peak_reported_working_set_bytes']) for r in runs)
    unknown = [r['run_id'] for r in runs if r['run_kind'] == 'behavior' and r['property_verdict'] is None]
    lines += ['', f'Total native verifier wall time, including metadata/compile/load: **{budget:.3f} s** / 1200 s.',
              f'Largest monitored native peak: **{peak:,} bytes** (max sampled private bytes / reported peak working set).',
              'Timeout thresholds were 10 s for setup and 30 s for behavior; process cleanup is included in recorded wall time.',
              'No automatic repeats or increased limits were used. Each invocation stayed within the user’s 60 s bound.', '',
              '`success` in Compile denotes compilation only. Load/parse executes only `E<> true` after parsing all query text.',
              '`satisfied` / `violated` are explicit successful scientific-query verdicts; `timeout` has no verdict.',
              'Joint backlog includes the absorbing overflow sentinel; it does not prove all queues are pre-overflow.',
              'The u0 invariant is exactly the original renamed C01-queue predicate. A violation is a negative result for that predicate.', '',
              '## Traceable records', '',
              'Every row below links the run index containing status, model_hash, query_hash, exact tool_version, commands, parameters/vector, raw logs and trace hashes.', '']
    for run in runs:
        if run['run_kind'] in ('behavior', 'model_load'):
            reference = f'checks/{campaign}/runs.json'
            lines.append(f"- [`{run['run_id']}`]({reference}): status=`{run['status']}`, verdict=`{run['property_verdict'] or 'absent'}`; {run['runtime_seconds']:.3f} s.")
    lines += ['', '## Open checks and readiness', '',
              f'{len(unknown)} behavioral attempts ended without a verdict. Their formulas remain open at the recorded model hashes and budget.',
              'All four models compiling/loading and saved diagnostic outcomes make the package reproducible and reviewable.',
              'They do not establish per-entity service reachability or the other timed-out predicates. In particular, service reachability is needed to substantiate that the common resource is exercised by every entity.',
              'Before claiming that nonvacuity for P4, obtain an appropriate witness under a separately justified check, or record an Integrator disposition narrowing the experimental claim. Do not add fairness or alter the model silently.',
              'Capacity has local structural support in CONTRACT.md, but a timeout is not a successful universal model-checking result.',
              'Future checks should be justified by their contribution to the selected P4 curves; simply repeating this campaign is not authorized by this package.', '']
    (g.HERE/'RESULTS.md').write_text('\n'.join(lines))
    candidates = []
    for n in g.SIZES:
        path = g.HERE/'generated'/f'n{n}'
        meta = json.loads((path/'metadata.json').read_text())
        candidates.append({'N': n, 'process_count': 49*n+1, 'directory': str(path.relative_to(g.HERE)),
                           'source_hash': meta['source_hash'], 'generator_hash': meta['generator_hash'],
                           'files': meta['files'], 'compile_status': outcome(n, 'compile-only'),
                           'load_status': selected[(n, 'initial-load')]['status'],
                           'load_verdict': selected[(n, 'initial-load')]['property_verdict'],
                           'load_run_id': selected[(n, 'initial-load')]['run_id']})
    packet = {'status': 'candidate_for_independent_review_not_frozen', 'gate_1_accepted': False,
              'issue': 'https://github.com/artmus208/uppaal_sdn_isac/issues/68',
              'owner_account': 'vadimnbkg', 'reviewer_integrator': 'artmus208 / user-integrator',
              'base_ref': 'read', 'base_commit': g.BASE, 'source_commit': settings['source_commit'],
              'old_baseline': 'reviewer-r1-gate1-20260923; historical scope unchanged',
              'old_p3_transferred': False, 'tool_version': runs[0]['tool_version'],
              'readiness': 'reproducible package; service nonvacuity unresolved, requires evidence or explicit disposition before the corresponding P4 claim',
              'readiness_blockers_for_p4': ['No diagnostic witness of service for each entity; do not assert this prerequisite until resolved or explicitly narrowed by Integrator.'],
              'protocol_sha256': g.sha((g.HERE/'PROTOCOL.md').read_bytes()),
              'query_schema_sha256': g.sha((g.HERE/'query_schema.py').read_bytes()),
              'p4_plan_sha256': g.sha((g.HERE/'p4-plan.json').read_bytes()),
              'models': candidates, 'diagnostics': {'index': f'checks/{campaign}/runs.json',
              'index_sha256': g.sha((folder/'runs.json').read_bytes()), 'total_verifier_wall_seconds': budget,
              'open_behavioral_run_ids': unknown},
              'required_decisions': [
                  'Accept finite N=1..4 domain, preserved optional shared service and per-UAV logical SDN context semantics.',
                  'Review preserved abstraction/observer limitations and exact model/query/parameter/vector hashes.',
                  'Resolve or explicitly dispose of open service nonvacuity and other diagnostic predicates before asserting them for P4.',
                  'Accept compact query roles and separate fixed-entity/global/coverage cost reporting.',
                  'Accept sequential three-repeat 60s/2GiB, 2-hour future P4 plan and per-run headroom probe.',
                  'P0/Integrator freezes a new baseline/version through a separate Gate 1 decision; no author self-acceptance.'],
              'does_not_close': ['R03', 'R04', 'C06']}
    (g.HERE/'gate-candidate.json').write_bytes(g.encoded(packet))
    print('Derived result matrix and candidate references; no acceptance asserted')


if __name__ == '__main__':
    main()
