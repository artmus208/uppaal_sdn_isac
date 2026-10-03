# Issue #89: UAV service-boundary protocol

Status: prepared for domain and native-execution decision; no verification result.
Owner vadimnbkg; protocol reviewer/integrator artmus208. The Runner is the actual
account declared in execution/approval.json. The Runner's
later review is producer review. Independent scientific acceptance requires a
separate reviewer or an explicit Integrator disposition, currently absent.

## Pinned inputs and authorization

Operational base is `452571598d4a5c1e070dace3a918ea737904e239` (actual merge #88),
replacing the earlier proposal base `46bf268c66d6ec2c106ae4ce8e8d5f893315ad91`.
Scientific input commit remains `61386aa358805082b705dcd00c8cbfde5fb98248`.
Runner execution commits will include the approved preparation, host/approval
records and each durable reservation. These three roles are not interchangeable.

Baseline `uav-service-completion-r1-20261002`: N=1, 51 processes, one request/result.
Exact model, manifest, generator, parameters/vector and decision pins are in
`input-pins.json`. Accepted [P1/P2 and Gate 1](https://github.com/artmus208/uppaal_sdn_isac/issues/84#issuecomment-5946722646)
and [activation](https://github.com/artmus208/uppaal_sdn_isac/issues/84#issuecomment-5947256320)
authorize input selection, not this new native campaign.

The exact Issue body and comments at start are in `inputs/`. The new user
assignment and [claim record](https://github.com/artmus208/uppaal_sdn_isac/issues/89#issuecomment-5968337905)
authorize preparation. The body explicitly says “materialize only an approved
diff”; therefore the current deliverable contains an in-memory-derived patch,
prospective hash and complete change list, without a saved Hnom XML.
`execution/model.xml` is the sole proposed materialization path, to be delegated
to Runner explicitly in the decision. It never overwrites production M.

PR #88 is merged, but the retrieved reviews/comment lists contain no explicit
acceptance or budget disposition. All eleven old attempts are timeout/null;
their aggregate overrun of 7.477845500001 seconds remains a disclosed historical
deviation. None of that old budget or any old success trace transfers here.

## Three different scientific questions

A (Q3): a correct successful execution exists inside Hnom. B (Q4): every actual
sent request in Hnom gets a correct successful response within 40 abstract time
units. C (Q6): every sent request in full M reaches an APP terminal location
within 40, possibly by rejection, failure, timeout or cancellation. A does not
prove B. C does not guarantee delivery; A together with C still does not prove B.

The clock resets in `c82_emit_request()` on actual `u0_app_service_request!`.
Admission records its ID without resetting this clock. `c82_D_service=40`.
Measurement takes five units after measurement start. `c82_store_measurement()`
resets sample age when storing the actual sample, not at request/admission.
Successful receipt requires sample age **strictly below 5**. At service age 40,
correct receipt and timeout remain alternatives. No physical time calibration.

Q3/Q4 use receipt records (`c82_receipt_sample_band==0`, receipt quality/timely
and service bands) rather than constraining the continuing sample clock after
Completed. Correlated request/sample/admission/job/transmit/receive IDs, captured
requirements and causal-stage flags are all included. `c82_payload_quality()` is
side-effect-free and checks the stored sample. Q5/Q6 require actual APP terminal
locations because cancellation flags can precede the APP handoff.

## Proposed nominal-input diagnostic region

`prepare.py` reads hash-pinned M, changes original byte spans, constructs the
candidate only in memory, compares the complete parsed structure against an
allowlisted transformation, and emits `hnom/proposed.patch`, `changes.json` and
`prospective-model.json`. Unchanged XML bytes are not reformatted.

1. E_PHY_INPUT: 23 sequential `value` selectors become singleton ranges:
   p0=2, p1–p22=0. The final two selectors become miss=0, scenario=0. Initialization
   remains exactly as in M (including p0=0 before the first input sample).
2. SharedLoad: pick_arrival and pick_m1–pick_m6 become singleton zero ranges.
   Original queue initialization, tick phase and mechanics remain unchanged.
3. E_FAULT: remove the 15 Before→Rule/Link/Node injection-choice edges, comprising
   three injection types × Idle/Forward/Ack/RecFlow/Rollback phases. Retain the five
   no-injection Before→Done alternatives and every other transition, including
   unreachable fault-phase forwarding/ACK/drop behavior. No guard is weakened.

This is nominal external observations with isolated background load and no
injected fault. It is a diagnostic scenario whose application relevance still
needs the recorded domain decision; it is not a sufficient success contract or a minimal
mathematical restriction. It is chosen from initialization, never by future
success, admission, dispatch, receipt flags or absence of a negative outcome.

The 40 changed XML elements are enumerated with original transition indices,
source/target and exact before/after values. All 51 instances, initial values,
observers, timing, other guards/clocks/updates, admission/KPI/control loss,
measurement failure, optional server=-1, result loss, cancellation, timeout,
skipped tick/delivery and waiting choices remain. No fairness, urgency, priority,
new invariant or time bound is introduced. Hnom gets a distinct hash and is not
a frozen baseline. Every Hnom claim remains scoped to Hnom unless separately
justified against M; no native replay is included in the six attempts.

## Ordered queries and decision method

The exact source is `inputs/issue-89.json`. S/G/Q2/Q5/Q6 are expanded by
`prepare.py` into one-line UTF-8 files without BOM and with a final LF.
`query-inventory.json` pins formula, model path/hash, query path/hash and cap.

| Slot | Model | Question | Cap seconds |
|---|---|---|---:|
| 1 | Hnom | Actual send is reachable | 180 |
| 2 | Hnom | Matching admission is reachable | 180 |
| 3 | Hnom | Correct correlated fresh successful receipt by 40 is reachable | 180 |
| 4 | Hnom | Every sent request gets correct successful receipt by 40 | 600 |
| 5 | Hnom | No deadlock before an actual APP terminal outcome | 180 |
| 6 | M | Every sent request gets an actual APP terminal outcome by 40 | 180 |

Q1–Q5 share one exact prospective Hnom hash. Q6 uses exact M. Q1 false makes the
domain vacuous; Q1/Q2/Q3 timeout leaves that coverage open. No replacements follow
negative results or timeouts. The approved six slots may continue in order after
a successful positive/negative machine verdict or timeout/memory stop. Q5 does
not prove time divergence or component progress.

The [UPPAAL symbolic semantics](https://docs.uppaal.org/language-reference/query-semantics/symb_queries/)
interpret leads-to over subsequent action/delay choices. We add no fairness or
exclusion of zero-time cycles. A negative trace must be classified as admission,
measurement, freshness/quality, queue/service, transport loss, cancellation,
timeout, deadlock or instantaneous loop. A Q3 witness needs offline causal-order
and ID inspection. Any missing trace or ambiguous endpoint stays an explicit gap.

Static obstruction (not a machine verdict): the result-job internal loss edge
competes with correct delivery under the same active/attempt timing guard and
has no retry. Nominal inputs do not delete it. Unconditional measurement failure
and optional service remain too. Intentional failure is not automatically a bug.
A stronger reliability/progress contract belongs to a separately assigned P1/P2
task. No model repair or manuscript edit is part of #89.

## Native budget and watchdog

The explicitly declared Runner uses the recorded Issue authorization of the exact checkpoint,
Hnom patch/hash, six query hashes, config hash, native host/executable and stop
policy. The latest user selection is native Windows Python + Windows PE verifyta,
superseding the Linux preparation preserved at 9e4743bf. The exact path/hash and
observed host/Python bindings are in `approval-template.json`; the persistent
native Windows checkout and accepted new preparation HEAD still require the
execution record. Account names are declared explicitly, not matched to the
repository owner. The Runner branch is codex/<runner>/89-uav-bounded-response-runs;
bundles and session metadata use that same identity. Historical UPPAAL version is an expected identity only; actual
full version and help are captured once after authorization, within the session.

At most six attempts, no retries; one verifier at a time; search allocation 1500 s;
whole native session 1800 s from preflight to owned-process cleanup. There are
two preflight commands (-v/-h), each capped at 30 s, and no preflight query.
Options `-o 1 -t 0 -X <prefix>` must match actual help (symbolic DFS and some XML
diagnostic trace). Memory stop remains floor(min(physical RAM/2,8 GiB)/MiB) MiB,
measured as sampled sum of Windows Job Object process working sets. Private
commit is reported separately. Sampling is not a hard allocation guarantee.

The independent `guard.py` uses monotonic whole-session and per-command deadlines.
`windows_native.py` assigns each suspended process atomically to an owned Windows
Job Object at CreateProcess, before acknowledging ownership and resuming it.
KILL_ON_JOB_CLOSE and the sole watchdog-owned handle terminate descendants even
if the watchdog crashes. No Linux process-group watchdog is used. Native host,
Python identity and PE path/format/hash are checked before the first command.

Timeout/memory_limit => null verdict; later authorized slots may run with remaining
budget. Error, preflight/version/help/monitor mismatch, watchdog failure, stop or
measured budget overrun halts the series. Ctrl-C asks the controller to stop;
controller death/EOF and watchdog death also stop owned processes. Termination
never selects processes by name. Deadlines reserve two seconds for cleanup.
Windows scheduling can still overrun; measured overruns are disclosed and halt.

The watchdog never reads status JSON and performs no telemetry writes while
children run. Samples are buffered and returned after cleanup, so a blocked
controller or disk cannot delay child termination through telemetry I/O. Abrupt
watchdog loss leaves unavailable metrics explicitly unknown. Full API contracts,
measurement limits and real Windows synthetic test evidence are in `WINDOWS.md`.

Each slot is consumed before launching, in a fsynced ledger and Git checkpoint
with complete bundle in a persistent Runner checkout. Interrupted reservations
remain used. A session claim is exclusive and never automatically reset. Each
attempt saves raw stdout/stderr/telemetry/XML traces, timing/CPU/peak RSS, tool
and input hashes, parameters/vector, command, UTC and execution source commit.
Missing states/trace/metrics remain unknown. `success` requires exit zero and
exactly one explicit indexed formula verdict; nonzero/partial output never counts.

## Ownership and handoff

Owner writes preparation in the sole Issue scope. Runner's proposed lease is only
`evidence/verification/uav-bounded-response-89/execution/**`, including approved
model materialization, approval/host records, ledger, raw evidence and recovery
bundles. Owner suspends writes there while the lease is active. Runner branch
starts at the explicitly accepted preparation HEAD, never moving read.

Runner must publish its exact final HEAD or full durable bundle and record lease
return in #89. Owner then merges that Runner commit into the Owner branch without
rebasing away execution commits, performs offline audit/trace classification,
updates results/report/coverage and submits the single final PR into read.
Preparation alone does not close #89, C02, P3, Gate 2, C06 or R07.
