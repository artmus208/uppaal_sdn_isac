# P3 campaign report — Issue #87

Deliverable: independently reviewable evidence for all 11 accepted inputs.
Campaign status: completed; counts: {'timeout': 11}.
Owner carwasher; reviewer/Integrator artmus208 proposed; acceptance pending.
Model b8ab50e112b71491f8242789cc7906497baf8440c473d7a5a4d5214840187e02; manifest 4b4bf71f55767123cc5934074024179289fa5ad3355fa4c0e37385e8261ef98d.
Exact base 46bf268c66d6ec2c106ae4ce8e8d5f893315ad91; branch codex/carwasher/87-uav-completion-verification; target read.

| Query | Status | Verdict | Wall seconds | Peak MiB |
|---|---|---|---:|---:|
| admitted | timeout | null | 601.039 | 976.83 |
| measurement | timeout | null | 600.604 | 965.29 |
| enqueue | timeout | null | 600.960 | 970.54 |
| attempt | timeout | null | 601.034 | 958.43 |
| success | timeout | null | 600.792 | 971.56 |
| loss | timeout | null | 600.607 | 977.21 |
| timeout | timeout | null | 600.468 | 982.27 |
| cancel | timeout | null | 600.428 | 966.67 |
| deadline-equality | timeout | null | 600.193 | 863.46 |
| completion-safety | timeout | null | 600.593 | 899.68 |
| deadlock | timeout | null | 600.760 | 509.85 |

Every row links by run_id/queue_path through results.json and query-ledger.json to
raw manager/session/attempt artifacts. Actual version and executable hash are in
assignment.json and preflight/version.stdout.txt; historical tool response is not
substituted. The source checkpoint is committed and pushed before each attempt;
per-run provenance.json supplies the source, exact commands, parameters and vector.
Missing measurements remain null. Native Windows physical RAM 17106464768
bytes; sampled stop threshold 8156 MiB / 8552185856 bytes.
Sampling is every second, not a hard allocation cap. No retries/new formulas.

**Budget deviation:** sum of recorded attempt wall times is 6607.477845500
seconds, exceeding the 6600-second maximum by 7.477845500 seconds.
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

| Environment | Check | Exit code |
|---|---|---:|
| checks | coordination | 0 |
| checks | historical-hashes | 0 |
| checks | candidate-generation | 1 |
| checks | candidate-audit | 1 |
| checks | candidate-controls | 0 |
| checks | software-suite | 1 |
| checks | mcp-smoke | 0 |
| checks | examples | 0 |
| checks | diff-check | 2 |
| checks-linux | coordination | 0 |
| checks-linux | historical-hashes | 0 |
| checks-linux | candidate-generation | 0 |
| checks-linux | candidate-audit | 0 |
| checks-linux | software-suite | 1 |
| checks-linux | mcp-smoke | 0 |
| checks-linux | examples | 0 |
| checks-linux | diff-check | 0 |
| checks-linux | software-suite-authorized | 0 |

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
package. See coverage.md for obligations not covered. Own offline integrity audit covers all eleven records; five in-memory negative
controls detect registry verdict/formula/query/model/raw-status tampering.
See check-results.json and checks/audit-controls.json.

Next: independent review of
exact provenance, machine results, traces and gaps, and explicit disposition for
any additional query/budget. Do not run driver.py again to reproduce the audit.
