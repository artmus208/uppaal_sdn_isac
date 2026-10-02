# Proposed independent disposition — Issue #84

**DRAFT: this file records no decision.** Proposed reviewer/Integrator: artmus208.
Author vadimnbkg cannot approve their own Gate 1. Replace placeholders only after
independent review; record the actual decision and references in Issue #84.

## A — Changed-composition P1/P2 applicability

Proposed decision: ACCEPT the exact full UAV N=1 composition of PR83 as the object
for a new single-model baseline, subject to the assumptions below. This is a new
scientific scope disposition, not inheritance of PR73's historical family decision.

Retain the accepted component/interface descriptions, abstract units/classes,
original admission-loss/timeout and safety policy, queue capacity/overflow and
optional COMM/JOINT service. Explicitly accept for this exact changed composition:
relative age from actual request; bounded admitted request/job/sample/transport IDs;
actual five-unit acquisition after sensing readiness; immutable quality snapshot at
its completion; one FIFO result rank; lossy one-attempt delivery within one unit;
APP matching receipt as success; immutable retrospective receipt flags/bands.
New fixed acquisition and result transport are abstract assumptions. Update class
is based on sample age, not physical update period. No physical calibration,
fairness, multi-request reuse, whole-system equivalence or universal SLA is accepted.
Age=5 is stale; age=40 permits contract receipt/timeout alternatives. Global equality
reachability remains open. Inherited deadlines/observers and abstract PHY classes
are included as pinned model inputs, not individually verified properties.

Changed templates: u0_phy_Template_A_SQ, u0_app_A_REQ,
u0_Boundary_E_SERVICE, SharedLoad; added C82_ResultJob/c82_job.
Exact constants/51-process vector/constructors are in the two inventories.
Acceptance of A is scoped P1/P2 applicability; it is not exhaustive verification.
If A is rejected or narrowed, state the required P1/P2 dependency/disposition before B.

A decision: [accepted / rejected / deferred]
Independent decision actor: [actual actor]
Decision reference / actual UTC time: [fill after decision]
Reviewed proposal HEAD: [exact Git SHA]

## B — Exact input freeze / Gate 1

Proposed decision: ACCEPT Gate 1 for `uav-service-completion-r1-20261002`, only after
A and independent review of the reproducibility/evidence audit. Freeze exact inputs
below, with the full input-hashes.json and proposed-baseline.yaml, not just model XML.

- Base ref: origin/read; input commit: 61386aa358805082b705dcd00c8cbfde5fb98248.
- Accepted publication: fdbfd5619385eae31101dcfc285010b96cc85b45.
- Candidate merge: 07e45268bbfbb4c1293e4e4f4227792794583509.
- Model SHA256: b8ab50e112b71491f8242789cc7906497baf8440c473d7a5a4d5214840187e02.
- Historical source XML SHA256: 5234cb087e5274798926d516dedc77d1f9542ea7df59cec39f83859771ce1385.
- Transformer SHA256: a5310747b9e2f1b837d0fefdff26d04c9218b7f22a87672bfaa13e7ee58e0ba2.
- Parameter set: exact candidate parameters.json plus inherited n1/parameters.json
  and emitted constants from parameter-inventory.json; request deadline=40,
  sample freshness<5, acquisition=5, transmission bound=1, queue K=4, N=1.
- Instance vector: exact instance-vector.json; 51 ordered processes, constructor
  bindings pinned by instance-inventory.json, one request/result.
- Selected query set: explicitly ACCEPT all eleven input formulas in query-inventory.json:
  success, completion-safety, admitted, measurement, enqueue, attempt, loss, timeout,
  cancel, deadline-equality, deadlock. Each remains not_executed/verdict=null.
  Record exact selected_query_set_hash below; hashes/formulas cannot change silently.
- Tool evidence: Engine.getVersion in preserved replay-001 raw stdout and result.json:
  UPPAAL version 5.0.0 (rev. 714BA9DB36F49691), June 2023 -- server.
  Full response (including original license identity) and hash are pinned. This is
  historical observed working candidate execution, not a new current license probe.
- manuscript_hash: exact protected levels_tex/samplepaper.tex entry in input-hashes.json;
  revision context only, unchanged, not an accepted integration result.
- source/generation/vector/parameter/query/input/manifest hashes: exact values in
  decision-pins.json; copy them into the actual decision record or link its exact
  reviewed Git blob. Preserve original execution checkpoints from source-index.json.

B decision: [accepted / rejected / deferred]
Selected query disposition: [all eleven exact inputs accepted / specify narrower set and new package]
Independent gate reviewer: [actual actor]
Reviewed package HEAD and proposal manifest SHA256: [exact values]
Gate decision UTC time / reference: [actual values]

This freezes inputs only. It establishes no completion safety, deadlock freedom,
universal SLA, fairness or P3 result. Hardware is per-run. P3_core_evidence_accepted
is not granted; R07 stays in Issue #80.

## Operational scope authorization — separate from C

Proposed authorization after A/B: activate in Issue #84 ONLY these paths:

- manifests/baselines/uav-service-completion-r1.yaml
- manifests/collaboration-v2.yaml, only the appended explicit P3/P5 selection block

Approve the exact reviewed proposed-operational.patch hash in decision-pins.json.
Recheck active scopes; if collaboration-v2 is reserved elsewhere, obtain an explicit
Integrator overlap/transfer decision recorded in both Issues. Apply the reviewed
patch, validate, publish a checkpoint and obtain independent operational PR review
into read. Preserve current.json, historical baselines/v1/generator pins and P4 policy.
The immutable proposal manifest retains preparation status; the independent GitHub
Gate/activation records are authoritative for the subsequently approved selection.

Scope/patch authorization: [accepted / rejected / deferred]
Approved patch hash / reviewer / decision reference: [actual values]

## C — Post-merge operational activation template

**DO NOT RECORD C AS EFFECTIVE BEFORE THE ACTUAL EVENTS.** Independent A/B decisions,
authorized scope, reviewed operational PR, merge into read and a separate explicit
Integrator activation are prerequisites. Merge itself is not activation.

Baseline ID: uav-service-completion-r1-20261002
Actual operational PR / reviewed HEAD: [fill after review]
Actual operational merge commit: [fill after merge]
Manifest SHA256 at actual merge: [compute from actual merge Git blob]
Input commit: 61386aa358805082b705dcd00c8cbfde5fb98248
A and B decision references: [actual Issue/PR links]
Independent activation actor: [actual actor]
Actual activation decision UTC time: [fill after decision, not retroactive merge time]
Activation record URL: [actual Issue #84 comment]

Proposed activated scope: explicitly selecting future P3/P5 Issues, full UAV N=1,
51 processes, exact accepted inputs only. Each Issue must pin baseline ID,
manifest SHA256, input commit and this activation decision. Historical current
pointer/default and old P4 family selection remain unchanged. Selection grants no
execution authorization or native budget, transfers no old verdict, accepts no
P3_core_evidence_accepted and closes no R07. Separate run protocol and independent
P3/P5 acceptance remain necessary. C decision: [accepted / rejected / deferred].

## D — Open claims retained

All eleven query verdicts remain null/unexecuted. Simulation simulate-006 and replay-001
show one feasible healthy 100-transition path; the two negative replay rejections
and age=5 diagnostic retain their own evidence class/status. Early model diagnostics
remain visible and cannot become results of the final XML. Prior P3/P4 results and
PR81's old-model rejection remain scoped to their original model hashes.
Completion safety, deadlock freedom, boundary reachability and all non-vacuity query
verdicts remain open. Universal completion/fairness/SLA and physical performance are
not established or encoded as an accepted conclusion by this package. No R07,
P3_core_evidence_accepted, full P3 or Gate 2 acceptance is granted by A/B/C.

D disposition: [confirm retained open claims / specify disagreement for follow-up]
