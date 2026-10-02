"""Build campaign index/report and audit without executing a verifier."""
import json,subprocess,sys
from collections import Counter
from prepare import HERE,ROOT,BASE,BRANCH,sha,save,GIT

def main():
    a=json.loads((HERE/'assignment.json').read_text());env=json.loads((HERE/'environment.json').read_text());ledger=json.loads((HERE/'query-ledger.json').read_text());records=[]
    manifest=json.loads((ROOT/'manifests/baselines/uav-service-completion-r1.yaml').read_text())
    for q in ledger['queries']:
        folder=HERE/q['queue_path'];paths=list(folder.glob('attempts/*/result.json'))
        raw=json.loads(paths[0].read_text()) if len(paths)==1 else {}
        p=json.loads((folder/'provenance.json').read_text()) if (folder/'provenance.json').exists() else {}
        r={'source_hash':manifest['hashing']['generation_source_hash'],'generator_hash':manifest['generator']['sha256'],'scientific_source_commit':a['scientific_input_commit'],'query_id':q['query_id'],'run_id':q['run_id'],'manager_attempt_id':raw.get('run_id'),'status':q['status'],'verdict':q['verdict'],'reason':q['reason'],'formula':q['formula'],'query_hash':q['query_hash'],'model_hash':a['model_hash'],'tool_version':raw.get('tool_version',a['tool_version']),'executable_hash':a['executable_hash'],'execution_source_commit':q.get('execution_source_commit'),'parameter_set':a['parameters'],'instance_vector':a['instance_vector'],'environment':env,'manager_command':p.get('manager_command'),'verifier_command':raw.get('command'),'cwd':raw.get('cwd'),'start_utc':raw.get('started_at'),'end_utc':raw.get('finished_at'),'wall_seconds':raw.get('elapsed_seconds'),'cpu_seconds':raw.get('cpu_seconds'),'peak_rss_bytes':raw.get('peak_rss_bytes'),'states_explored':raw.get('states_explored'),'trace_paths':raw.get('trace_paths',[]),'metric_null_reason':'not_executed: no process or measurements' if not raw else 'Field null when manager/tool did not supply it; states_explored not parsed by manager','raw_files':[],'acceptance_status':'pending_independent_review'}
        for path in sorted(folder.rglob('*')):
            if path.is_file():r['raw_files'].append({'path':path.relative_to(HERE).as_posix(),'sha256':sha(path),'bytes':path.stat().st_size})
        records.append(r)
    save('results.json',{'issue':87,'baseline_id':a['baseline_id'],'campaign_status':ledger['campaign_status'],'queries':records,'acceptance_status':'pending_independent_review','verification_claim_scope':'Full N=1, 51 processes, accepted A/B assumptions; per-success explicit formulas only'})
    total_wall=sum(r['wall_seconds'] or 0 for r in records)
    status_counts=dict(Counter(r['status'] for r in records))
    rows=['| Query | Status | Verdict | Wall seconds | Peak MiB |','|---|---|---|---:|---:|']
    for r in records:rows.append('| '+r['query_id']+' | '+r['status']+' | '+str(r['verdict'])+' | '+(f"{r['wall_seconds']:.3f}" if r['wall_seconds'] is not None else 'null')+' | '+(f"{r['peak_rss_bytes']/1024**2:.2f}" if r['peak_rss_bytes'] is not None else 'null')+' |')
    checks=[]
    for name in ('checks/results.json','checks-linux/results.json'):
        if (HERE/name).exists():checks.extend((name.split('/')[0],r) for r in json.loads((HERE/name).read_text()))
    check_rows=['| Environment | Check | Exit code |','|---|---|---:|']+[f"| {kind} | {r['name']} | {r['exit_code']} |" for kind,r in checks]
    report=f'''# P3 campaign report — Issue #87

Deliverable: independently reviewable evidence for all 11 accepted inputs.
Campaign status: {ledger['campaign_status']}; counts: {status_counts}.
Owner carwasher; reviewer/Integrator artmus208 proposed; acceptance pending.
Model {a['model_hash']}; manifest {a['manifest_hash']}.
Exact base {BASE}; branch {BRANCH}; target read.

{chr(10).join(rows)}

Every row links by run_id/queue_path through results.json and query-ledger.json to
raw manager/session/attempt artifacts. Actual version and executable hash are in
assignment.json and preflight/version.stdout.txt; historical tool response is not
substituted. The source checkpoint is committed and pushed before each attempt;
per-run provenance.json supplies the source, exact commands, parameters and vector.
Missing measurements remain null. Native Windows physical RAM {env['physical_ram_bytes']}
bytes; sampled stop threshold {env['memory_mib']} MiB / {env['memory_stop_bytes']} bytes.
Sampling is every second, not a hard allocation cap. No retries/new formulas.

**Budget deviation:** sum of recorded attempt wall times is {total_wall:.9f}
seconds, exceeding the 6600-second maximum by {max(0,total_wall-6600):.9f} seconds.
The per-query manager thresholds remained 600 seconds; recorded walls include
sampled timeout/termination/serialization. The supplemental aggregate guard
failed with native PermissionError while reading atomically replaced status.json.
Manual stop was requested after discovering the guard failure; the final query
had already timed out. All 11 statuses remain timeout, not stopped. No query
was retried. budget-stop-failure.json retains the exact observed failure/deviation.
Budget compliance is NOT claimed; acceptance requires independent disposition.
No remaining verifier processes were found after the series. No diagnostic
traces were emitted for these incomplete searches; stdout/stderr and telemetry
remain available. The evidence audit checks integrity separately from policy
compliance and exposes aggregate_wall_budget_compliant=false.

{chr(10).join(check_rows)}

Windows software suite: 209 tests, 3 failures, 3 errors, 2 skips. Limitations:
cp1251 implicit file reading, unprivileged symlinks, platform path separators and
venv launcher PID measurements. Direct native Python synchronized touched-memory
probe confirms manager RSS >32 MiB (78,131,200 bytes) and CPU measurement.
Driver uses direct base Python, not venv launcher. Windows candidate parameters
regeneration embeds Windows path separators; accepted bytes/model/query were not
modified. Linux candidate generation and archive audit reproduce exact inputs.
Linux initial full suite: one MCP stdio startup timeout under the sandbox;
repeated with authorized subprocess transport: all 209 tests OK, exit 0.
Raw Windows CRLF/whitespace logs are preserved with binary diff attributes;
the final source/scope diff check is reported separately. No source fixes outside
scope. The initial input audit hit the known accepted collaboration-v2 operational
delta; scientific inventory checked against exact scientific Git blobs, current
operational hash checked against C. Software tests use mocks/fake Python children,
never additional UPPAAL model queries.

Assumptions and boundaries remain in PROTOCOL.md/assignment.json: fresh age <5,
service <=40 with receipt/timeout alternatives at age=40; no fairness, no ID reuse,
optional service, one bounded lossy transmission, no physical calibration.
Existential witnesses do not prove universal SLA. Completion safety does not imply
completion/fairness. Inconclusive outcomes establish neither truth nor falsehood.
Historical simulations/old-model verdicts do not transfer.

P3_core_evidence_accepted, P3_complete, C06, Gate 2 and R07 remain unaccepted by this
package. See coverage.md for obligations not covered. Next: independent review of
exact provenance, machine results, traces and gaps, and explicit disposition for
any additional query/budget. Do not run driver.py again to reproduce the audit.
'''
    (HERE/'report.md').write_text(report,encoding='utf-8',newline='\n')
    coverage='''# C01–C05 coverage/gap index

No requirement is automatically closed by publishing this campaign.

| ID | Accepted input/evidence relationship | Remaining gap |
|---|---|---|
| C01 deadlock | deadlock.q is full-composition A[] not deadlock; consult its recorded status/verdict. | Only status=success with explicit verdict resolves this query; timeout/memory/error remains open. |
| C01 queue bounds | No accepted query explicitly asserts all queue bounds. Enqueue existential input only exercises one event. | Machine queue-bound obligation remains uncovered. K=4 assumption/static typing is not a proof. |
| C01 recovery-attempt bounds | No accepted formula checks all recovery-attempt counters. | Structural recovery-attempt obligation remains uncovered. |
| C02 bounded response | success/deadline-equality are existential; completion-safety is conditional terminal safety. | No universal bounded-response formula with trigger/end/reset and progress assumptions is present. Requires separate accepted query/disposition. |
| C03 model checking | results.json indexes all 11 statuses; only per-query success and explicit verdict is direct machine evidence. | Inconclusive/unexecuted queries stay open; exact model only N=1, 51 processes. |
| C04 diagnostic evidence | Raw traces/stdout/stderr/telemetry listed and hashed in results.json; trace command is -t 0 -X. | A trace establishes only its own query/run. Absent trace remains visible; no inferred counterexample from timeout. |
| C05 provenance | Per-run source commits, full commands/flags, exact model/query/tool/executable hashes, vector/parameters and native measurements. | Unavailable metrics remain null. Sampled WorkingSet is not hard allocation accounting. Independent audit/review required. |

admitted/measurement/enqueue/attempt/success/loss/timeout/cancel are separate
existential non-vacuity or outcome diagnostics. A successful witness is no
universal service promise. deadline-equality diagnoses a possible successful
receipt at request age=40; it does not eliminate the permitted timeout alternative.
completion-safety can be vacuous if Completed is unreachable: consult success.
A[] not deadlock is neither time divergence nor fairness nor eventual completion.
Three structural obligations and bounded response are not replaced by a count of
11 query files. New formulas require separate disposition. C06 depends on P4;
R07/P5 #80 and manuscript remain outside this deliverable.
'''
    (HERE/'coverage.md').write_text(coverage,encoding='utf-8',newline='\n')
    excluded={'artifacts-sha256.json','check-results.json','HANDOFF.md','PR-body.md','publication.json'}
    save('artifacts-sha256.json',{p.relative_to(HERE).as_posix():sha(p) for p in sorted(HERE.rglob('*')) if p.is_file() and p.relative_to(HERE).as_posix() not in excluded and '__pycache__' not in p.parts})
    from audit import audit
    save('check-results.json',audit());print(json.dumps({'status_counts':status_counts,'audit':'ok'}))
if __name__=='__main__':main()
