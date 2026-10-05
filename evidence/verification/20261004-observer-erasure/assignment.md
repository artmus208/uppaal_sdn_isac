Process: P3 — observer erasure with bounded native validation.
Deliverable: one source-bound observer-erasure/transfer proof package plus a bounded model-checking experiment on its exact 29-process diagnostic composition.
Atomic IDs: supporting C01/C03/C04/C05; primary ownership unchanged, no automatic requirement closure.
Owner/account-id: vadimnbkg. Independent Reviewer/Integrator: artmus208.
Authorization: user explicitly approved publication of the prepared Issue, dedicated branch and draft PR, then requested model checking on 2026-10-05. This extends the earlier local proof-only protocol to the bounded experiment below. No merge, acceptance or messages to other chats are authorized.
Base ref: origin/read
Base commit: e5c299d0b426e57652cb8a78f37ae770949b53b1
Target branch: read
Write scope: evidence/verification/20261004-observer-erasure/**
Read-only: production models/generators/queries/manifests, prior evidence and manuscript.
Selected scientific input: uav-service-completion-r1-20261002, N=1/51 processes, one request/result, scientific commit 61386aa358805082b705dcd00c8cbfde5fb98248.
Original model SHA256 b8ab50e112b71491f8242789cc7906497baf8440c473d7a5a4d5214840187e02; manifest SHA256 4b4bf71f55767123cc5934074024179289fa5ad3355fa4c0e37385e8261ef98d.
Dependencies accepted: #83 candidate; #84 A/B https://github.com/artmus208/uppaal_sdn_isac/issues/84#issuecomment-5946722646 and activation https://github.com/artmus208/uppaal_sdn_isac/issues/84#issuecomment-5947256320; v2 #64. No #89/#108/#115 result assumed.
Scope audit: no existing observer-erasure assignment found. #115 owns FIFO/termination proof; #108 completion proof; this package edits neither.

Prepared result: 22 Obs processes removed, 27 hidden bookkeeping identifiers, 77 helper audits, 74 observer edges, eight broadcast receives, five committed observer locations with complementary exits. Diagnostic XML SHA256 b80db319ff7cdb511cb97aa155be01f1d68707358399fbe02fa39c1c6c32be6c.
Native protocol:
- Scientific question: can observer-erased model checking settle the exact completion-safety predicate and separately exhibit successful completion?
- Two sequential single-query runs: unchanged accepted completion-safety.q and success.q copied byte-for-byte into scope; at most one attempt each. Success is independent non-vacuity evidence, not a substitute for safety.
- Native Windows UPPAAL verifyta.exe, observed version recorded verbatim; fixed options -o 0 -t 0 (BFS, diagnostic trace).
- Search limit 600 seconds per formula, sampled memory cap 2048 MiB, maximum combined search 1200 seconds, exclusive owned queues. Only owned processes terminated. Version preflight <=20 seconds.
- Stop on error/monitor_error/license/version/input mismatch; timeout/memory_limit retained as inconclusive, then next planned query; no retries or budget increases.
- Run IDs: observer-erasure-<issue>-20261005-<query>-01; exact XML/query/executable/code hashes, clean execution commit, full commands, environment/hardware, telemetry, stdout/stderr and traces retained.
- Direct verdicts concern the 29-process diagnostic XML only. Transfer to the full 51-process input is conditional on independent acceptance of the proof; no author self-acceptance. Prior native results remain unchanged.

Acceptance:
1. Explicit retained-state relation and finite timed projection/lifting, committed normalization, property directions and deadlock/liveness/error-detection limits.
2. Fail-closed stdlib audit, exact inputs and diagnostic transformation; mutation controls below hash gate, deterministic certificate across hash seeds.
3. English reviewer/article text and claim/artifact map; relevant software checks with failures/skips preserved.
4. Native executions comply with the fixed protocol; results and limitations distinguish direct reduced-model evidence from conditional full-model transfer.
5. Scoped checkpoint commits, durable published branch and draft PR to read; independent acceptance pending.
Evidence kinds: mathematical_argument, static_validation and direct_model_checking only when a successful complete explicit native result exists.
Out of scope: model/generator/manifest/manuscript changes, arbitrary-N theorem, full-model run campaign, native retries/budget extension, requirement/gate closure or merge.
Status: in-review; bounded experiment completed inconclusively; draft PR #118.

## User-authorized 30-minute rerun, 2026-10-05

The user extended timeout to 1800 seconds per formula and authorized a
conditional repair/rerun if the status-write error recurred. The scientific
inputs and 2048-MiB sampled memory stop were unchanged. Both runs ended on
memory_limit, with no native verdict: safety after 971.813 seconds, success
after 1064.141 seconds. The status-write error did not recur; no repair or
suffix-03 run was activated. Raw logs, exact bindings and integrity validation
are in native-30min/. Historical native/ evidence remains byte-for-byte intact.
Published branch remains codex/vadimnbkg/116-observer-erasure, draft PR #118;
independent acceptance remains pending. No active native worker remains.
