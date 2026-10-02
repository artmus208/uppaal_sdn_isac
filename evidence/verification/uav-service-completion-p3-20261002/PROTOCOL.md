# Issue #87 — bounded P3 campaign

Owner carwasher; independent reviewer/Integrator artmus208 proposed. ONE package,
C01–C05 supporting evidence; C06/P3_complete/P4/R07 and manuscript out of scope.
Exact base 46bf268c66d6ec2c106ae4ce8e8d5f893315ad91; target read.
Branch codex/carwasher/87-uav-completion-verification. Only this directory changes.

Explicitly selected baseline uav-service-completion-r1-20261002, full N=1,
51 processes, one request/result. Manifest SHA256
4b4bf71f55767123cc5934074024179289fa5ad3355fa4c0e37385e8261ef98d.
Model SHA256 b8ab50e112b71491f8242789cc7906497baf8440c473d7a5a4d5214840187e02.
Scientific input commit 61386aa358805082b705dcd00c8cbfde5fb98248.
Current pointer remains historical; preparation flags are not rewritten.

Authoritative decisions, preserved as API snapshots in preflight:
- v2: https://github.com/artmus208/uppaal_sdn_isac/issues/64#issuecomment-5878071165
- A/B: https://github.com/artmus208/uppaal_sdn_isac/issues/84#issuecomment-5946722646
- C: https://github.com/artmus208/uppaal_sdn_isac/issues/84#issuecomment-5947256320

Order: admitted, measurement, enqueue, attempt, success, loss, timeout, cancel,
deadline-equality, completion-safety, deadlock. One queue for each ORIGINAL .q.
At most one native model-checking attempt per input, sequential. Search timeout
600 seconds each, maximum 6600 seconds total. No retries/continue/smoke queries,
reductions, approximations, new queries or changes to global license/proxy settings.
Manager options are BFS/exact symbolic `-o 0 -t 0`, diagnostic `-X <trace>`.
Native Windows Python and Windows verifyta only. Actual tool version/executable
hash, measured host physical RAM and floor(min(RAM/2,8 GiB)/MiB) are saved.
Memory is sampled native WorkingSet/PeakWorkingSet, not a hard allocation cap.
Timeout/memory_limit retain null verdict and permit next query. Error,
monitor_error, stopped or inconclusive without the prescribed continuation
policy stop this scoped driver conservatively. Remaining inputs not_executed.
Version mismatch, unavailable engine, normalization drift or unavailable native
monitoring block execution. The version capture is not a query execution.

Execution: `python -B driver.py` from a clean committed checkout. Before each
start, driver commits attempt reservation and publishes the source checkpoint.
The execution source commit is saved in that run's provenance. Raw evidence is
written directly into this scope after start; the next query waits for a commit
and successful push of the completed raw evidence and ledger. Driver stdout stays
in the invoking terminal; manager stdout/stderr go into the owned queue.
A surviving reserved/incomplete ledger entry counts as consumed; driver refuses
restart. Inspect owned PIDs and durable remote ledger before any recovery.
Do not automatically kill another run or remove/reset/stash original changes.

Assumptions: no ID reuse; fixed five-unit acquisition; age classes [0,5), [5,10),
[10,infinity), including update class as an age abstraction; single-result FIFO
rank in K=4 with absorbing overflow; optional one COMM/JOINT service per five-unit
epoch, no fairness; lossy one-attempt transport within one unit; abstract units,
no physical calibration. Freshness is STRICT sample age <5. Service age <=40;
at age=40 receipt and timeout are both possible alternatives.

Success plus explicit formula result is required for a satisfied/violated claim.
Existential witness is not universal SLA; completion safety is not mandatory
completion, fairness or liveness. Static reproduction/audits/software tests are
not model checking. Missing metrics are null with a reason. Eleven inputs do not
cover all structural obligations or bounded-response requirements. Independent
review is required; no automatic P3_core_evidence_accepted/Gate 2/R07 closure.

Reproduce inputs without execution using candidate generate.py --check/audit.py;
use scoped audit.py for this package. driver.py is a one-shot campaign, not an audit.
To reproduce on another device, restore this branch, inspect durable ledger,
install package dependencies and substitute measured native host paths only under
a new separately authorized campaign. Original host paths document actual commands.
