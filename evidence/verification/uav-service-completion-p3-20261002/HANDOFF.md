# Issue #87 durable handoff

Deliverable: ONE independently reviewable P3 evidence package for all eleven
accepted UAV completion query inputs, with raw logs/telemetry, provenance,
results, integrity audit and coverage gaps. Owner/account: carwasher.
Branch: `codex/carwasher/87-uav-completion-verification`; target: `read`; base-ref: `origin/read`.
Exact base: `46bf268c66d6ec2c106ae4ce8e8d5f893315ad91`.
Execution/audit source checkpoint: `d4fb22ca3723ad78d5756e2b40deca38da62694f`.
Final package HEAD is recorded in the canonical PR and Issue #87 handoff comment
following the final artifact commit; do not substitute a moving read HEAD.
Per-query exact clean execution source commits are in query-ledger.json and
runs/<run_id>/provenance.json. No source commit exists only in a temporary sandbox:
all named checkpoints were pushed to canonical GitHub origin before execution.

Results: **11 timeout, 11 null verdicts**, one attempt each, no retries.
Actual aggregate attempt wall time 6607.477845500001 seconds, exceeding the 6600
maximum by 7.477845500001 seconds. Supplemental guard failed with native
PermissionError; manual stop was too late. Evidence integrity is ok; budget
compliance is false and must receive an independent disposition. No property,
P3_core_evidence_accepted/P3_complete, C06, Gate 2 or R07 is accepted by this package.

Baseline: `uav-service-completion-r1-20261002`; full N=1, 51 processes, one request/result.
Manifest SHA256 `4b4bf71f55767123cc5934074024179289fa5ad3355fa4c0e37385e8261ef98d`.
Model SHA256 `b8ab50e112b71491f8242789cc7906497baf8440c473d7a5a4d5214840187e02`.
Exact actual full tool response in preflight/version.stdout.txt and assignment.json;
UPPAAL 5.0.0 rev. 714BA9DB36F49691, executable SHA256 `4c8af2716ff61f3cf35c6d1dc408ccf306d44bb22478e104548a8f0f7a3febe5`.
Per-query hashes/formulas/commands/start/end/resource measurements and null reasons
are retained in results.json and native attempt/session records. No diagnostic
traces were produced by these incomplete attempts. Raw files remain in runs/**.

Checks: Linux full suite 209/209 OK after sandbox transport retry; coordination,
57-file historical hash audit, exact candidate generation/archive audit, MCP and
CLI examples smoke succeeded. Candidate controls 12/12 OK. Windows limitations
and initial failed checks retained in report.md and checks/**. Offline audit
checks all 11 attempts and hashes; five negative controls detect tampering.
Source/scope diff checks report no paths outside the approved scope. Native cleanup
probe found zero remaining verifyta processes. No additional native queries were
used in testing. Check commands/exit codes are in checks*/results.json and
checks-final.json. Raw Windows logs are kept byte-for-byte with binary diff attributes.

Artifacts: results.json SHA256 `c9e32ea537cc4ff1236f788e0714d7a9076e1919f25cff0fd36494f16fb4b7a4`;
artifacts-sha256.json SHA256 `7f821b0e48b5ef73866e6e80b7e862a09967026c196758e558855f8dfa8ca732`.
The artifact index covers raw data and package code/report; HANDOFF.md and the
self-index/audit output are excluded to avoid circular hashes and protected by Git.

Reviewer reproduction from a fresh canonical branch clone, without native execution:

```bash
python -B evidence/verification/uav-service-completion-p3-20261002/audit.py
python -B evidence/verification/uav-service-completion-p3-20261002/audit_controls.py
python -B evidence/instantiation/uav-service-completion-candidate/generate.py --check
python -B evidence/instantiation/uav-service-completion-candidate/audit.py
```

Use Linux for exact candidate JSON regeneration: the unchanged historical compiler
embeds host path separators in parameter provenance. The scoped offline audit is
portable and uses exact saved Windows commands as data. Do not rerun driver.py or
prepare.py: ledger reservations have already been consumed. A new verifier
campaign requires its own disposition and authorization.

Durable retrieval: canonical remote https://github.com/artmus208/uppaal_sdn_isac,
named branch `codex/carwasher/87-uav-completion-verification`; raw artifacts and all source commits included in Git.
Persistent owner-side clone: `D:/uppaal_mcp/.workstreams/issue87` (WSL path
`/mnt/d/uppaal_mcp/.workstreams/issue87`). Original dirty checkout was preserved.
Final isolated working tree is checked clean before PR handoff. A complete branch
bundle may be exported from this canonical branch without recreating native runs;
remote publication is the primary handoff, no temporary-only archive is required.

Next step: independent reviewer/integrator audits the raw package, considers the
7.478-second aggregate deviation, and records acceptance/disposition and coverage
gaps. Queue/recovery bounds and a genuine bounded-response query remain uncovered;
all eleven behavioral verdicts remain open. P5 #80/manuscript/previous evidence
were not changed. No merge/self-approval was performed.
