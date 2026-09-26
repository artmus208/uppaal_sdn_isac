# P3 core acceptance proposal — C01–C05

**Status: prepared for an explicit user acceptance decision; not yet accepted.**
Issue [#39](https://github.com/artmus208/uppaal_sdn_isac/issues/39), owner
vadimnbkg. Base `read/1bf6c51c73e0f6a2dc1e785104dadd7dcc8ff46b`; branch
`codex/vadimnbkg/39-p3-core-acceptance-20260926`; scope this directory only.

The user authorized preparation, author review and merge. Automatic approval
review rejected recording author acceptance, citing AGENTS.md. This package
therefore makes the exact decision reviewable for the user; neither this proposal
nor a PR merge accepts P3 core automatically. No independent review is claimed.

## Concrete proposed decision

Accept `P3_core_evidence_accepted` with the explicitly enumerated limitations
and exact evidence whitelist in `decision.json` and `accepted-runs.json`.
This accepts a scientifically qualified evidence package, not a claim that every
requested structural/reachability property holds. P3 as a whole and Issue #39
remain open because C06 requires P4. Gate 2 remains pending.

| ID | Proposed disposition and retained limitation |
| --- | --- |
| C01 | Queue capacity is violated; retain the counterexample and qualify article claims. Global deadlock is deferred/unproved. Retain PR #55's accepted inductive argument for per-episode attempt bounds and recorder discipline. Primary dispatch, receiver readiness and two-attempt reachability remain unconfirmed; no positive or unreachability claim. |
| C02 | Retain PR #53's pinned safety-transfer argument and ACK-or-ScheduleFailure completion within 3 abstract units on time-divergent executions. Direct full-model checking remains inconclusive. No unconditional completion, guaranteed ACK, deadlock/Zeno freedom, guaranteed time-divergent continuation from every request or physical calibration. |
| C03 | Accept actual positive, negative and inconclusive records exactly as whitelisted. Accepted evidence does not mean satisfied formula. |
| C04 | Accept both saved full-model counterexamples and the separate reduced negative control. Trace lengths are not explored-state counts or physical timelines. |
| C05 | Accept auditable provenance/resources with the specified exclusions. Reinstate recovered C02 only as diagnostic/resource evidence. Exclude three joint metadata-only records. Four reduced/control runs have unavailable memory samples; raw zero is not zero consumption. |
| C06 | Outside core acceptance; pending accepted P4 and a qualified scalability conclusion. |

The queue counterexample agrees with the accepted contract: five arrivals with
no service reach the overflow witness at capacity four. Matching control ACKs
do not dequeue. The [PR #60 audit](../p3-20260926-dispositions/README.md) checks
this against frozen XML and raw trace. The proposed decision retains the negative
finding; it does not introduce service fairness, admission clipping or a new
baseline. Integration must remove/qualify universal non-overflow claims.

## Evidence proposed for acceptance

Every registry row includes exact run_id, status, verdict, model/query hashes,
actual full tool_version, metadata/raw references and permitted use. No unlisted
run is implicitly accepted. The registry is a proposal until the user decision.

| Category | Records | Scope |
| --- | ---: | --- |
| Full frozen-model selected queries | 43 | 9 explicit results: 7 existential witnesses and 2 counterexamples; also 32 timeouts and 2 errors. |
| Reduced C02 and negative-control checks | 4 | Separate model identities supporting the accepted argument/control; no direct full-model verdict. |
| Recovered C02 memory-stop attempt | 1 | Recorded runtime/working-set observation for this host/configuration only. |
| Joint-prerequisite metadata-only records | 3 excluded | No raw revalidation, numerical claim or P5 evidence from these rows. |

This is **48 proposed evidence records, not 48 successful verifications**.
The full-model hash remains
`592678ed678ce8f70cf278f542e48bd2bb739969b53a962423d3e63f91e3e1e2`.
Reduced/control identities remain distinct; static proof checks have no invented
model-checking run IDs. The source/generator aggregates and parameters/vector
remain frozen. Every numerical integration claim must resolve to its exact row.

## Proposed C02 restoration disposition

Attempt `001-29c3409912fe43029fa925b140dbf40a`, package
`p3-20260925-c02-24h-001`, has original raw files restored in PR #60.
The auditor checks hashes, inputs, raw version, actual manager, parameters/vector,
telemetry and byte identity to PR #53's supplied summary. Proposed decision:
supersede the old lost-archive exclusion for this one diagnostic record only.

Status stays `memory_limit`, verdict null. Its 8324.0300215 seconds and
8590032896 peak working-set bytes describe that recorded attempt; accepting them
would not create a controlled benchmark, successful C02 verdict or P4 scaling
boundary. The threshold is sampled, not a hard memory cap. Historical preparation
files remain unchanged; terminal session/result identify the fixed-manager run.
The first write-error attempt and software smoke are not added implicitly.

## Joint-probe raw gap

`archive-search.json` records the bounded search. Neither pinned read nor PR #59's
head contains the referenced archive/raw directory. Available path history has
no archive commit. No target was found in the workspace or /tmp; the known
D:/uppaal-handoffs directory is absent here. No claim is made about all machines.

Expected archive SHA256:
`3d00c5cd34ab59266a1dcc159ade2d5a7d75109ec4dd03df5da8fc515ae9c4c7`.
The three exact IDs remain in `excluded_runs`, with original metadata outcomes
unchanged. Prior user acceptance of the narrow joint-prerequisite review remains
historical fact; this proposal excludes those executions from the reproducible
core whitelist and from new numerical/P5 claims. Later recovery requires matching
original bytes and an explicit acceptance update. No verifier rerun is performed.

## Downstream effect if accepted

The collaboration contract separates P3 core (C01–C05) from P3 complete (C06 after
P4). Accepting this package would satisfy the P3 prerequisite for P5 acceptance.
It would not accept P5 scenarios themselves or bypass their causal-chain checks.

The seven full-model positive traces are witness fragments; two negative traces
can support failure-scenario fragments. P5 must establish the actual
PHY → MAC → SDN/RIC → SLA chain and preserve the exact formula/configuration.
A rollback-dispatch witness does not prove recovery completion; an ACK-timeout
witness does not prove later report delivery or successful ACK. Reduced-model
witnesses, excluded joint probes and inconclusive runs cannot establish successful
full-model scenarios. Registry `p5_use` marks these restrictions.

P4 may start from accepted Gate 1/P1/P2, independently of complete P3. P9a, P8,
Gate 2 and P9b still require their remaining accepted deliverables. D01 remains
deferred. This package changes no manuscript, model, generator or manifest.

## Reproduction

Python 3.12+; install project/PyYAML in an isolated environment for the full checks.
No command below invokes UPPAAL:

```sh
python3 -B evidence/verification/p3-20260926-core-acceptance/build_registry.py
python3 scripts/check_coordination.py
python3 scripts/check_coordination.py --audit-hashes --commit HEAD --output /tmp/p3-core-new-baseline-audit.json
python3 -m unittest discover -s tests -v
```

The builder repeats raw archive/recovery checks from PR #60, reduced/control
byte and verdict checks, and both pinned proof checks with their existing mutation
controls. It reproduces the proposed whitelist and validates decision restrictions.
`--write` regenerates the registry only; changing it requires deliberate review
and an updated registry hash in the proposal. Review and checks are recorded in
this directory before publication. The final acceptance action remains pending.
