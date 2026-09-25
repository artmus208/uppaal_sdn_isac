# C02: audit of reduction and reviewer requirement

Issue #39, P3/C02 supplementary evidence. Owner: vadimnbkg. Base ref read,
base commit ac2d6d31682df7957cabc58ff58d4267dcd56f08. Branch
codex/vadimnbkg/39-c02-abstraction-audit. Target read. Only this new directory
is written; models, manifests, previous runs and manuscript remain unchanged.

This is an **author-side audit**, not independent acceptance. The author helped
construct the reduction. PR #50 was merged, but that does not itself record
acceptance of the proof or C02. No new verifier execution is performed here.

## Findings and decision

1. **No defect found in the pinned safety-transfer argument.** All five boundary
   transitions and the waiting invariant are retained. Hidden environment
   constraints are relaxed, and hidden steps can stutter. The concrete predicate
   is preserved by the stated relation. This finding is limited to the exact XML
   hashes below; it is not certification of a general slicing algorithm.
2. **The elapsed-safety result is weaker than unconditional bounded completion.**
   `A[] (!late && (active imply age <= D))` does not force active to become false.
   Both a blocked deadline and an infinite zero-time loop can preserve this
   predicate. The reduced model explicitly permits stuttering. Existing full-model
   machine evidence already gives a negative verdict for unconditional completion.
3. **Successful ACK is not the original reviewer's explicit requirement.**
   Reviewer 2 asks for one bounded-response property on the actual XML models,
   not specifically guaranteed successful PHY delivery. The accepted project
   contract allows ACK **or timeout**. The requirement-fit gap is the unqualified
   eventual-outcome claim, not merely the inclusion of timeout as an outcome.
4. **Conditional completion requires an explicit scope and acceptance decision.**
   Safety plus the unchanged active-age clock entails ACK-or-timeout by D on any
   execution whose accumulated time is unbounded. This does not establish that
   every request state has such a continuation, eliminate deadlock/Zeno behavior,
   or turn the negative unconditional leads-to result into a positive one.
5. Full-model direct C02 remains **inconclusive**, now including memory_limit at
   8 GiB. Enlarging a resource budget cannot resolve the semantic distinction.

Recommended next step: an independent reviewer audits the safety simulation and
accepts/rejects the explicitly time-divergent completion argument and its adequacy
for C02. Do not mark C02 closed automatically. If unconditional completion is
required, the current behavior must be addressed in a separately authorized
model/progress contract, with new baseline approval where needed. No arbitrary
fairness scheduler or deletion of observer loops is justified by this audit.

## Exact sources of intent

- Original [reviewer DOCX](../../../rewievs/18100004273%20-%20Comments%20for%20authors.docx),
  Review 2, embedded `word/media/image3.png`: “one bounded-response property on
  the actual XML models”. Read visually, not inferred from our decomposition.
  Document and image hashes are in `reviewer-source.json`.
- [Scientific manifest](../../../manifests/v1.md), line 50 and P3 minimum set:
  at least one bounded-response check; lines 62ff bind C01–C05 to the frozen
  configuration. Reduction is an argument about that configuration, not a new
  baseline substituted without explanation.
- [Manuscript](../../../levels_tex/samplepaper.tex), lines 245–250:
  `request_k => eventually_[<=D_k] outcome_k`. No time-divergence qualification
  appears in that paragraph. Manuscript editing belongs to integration, not here.
- [Accepted ACK contract](../../instantiation/20260919-core-check-contract/README.md),
  lines 80–100: start is actual dispatch, end is matching ACK or ScheduleFailure;
  unconditional completion is a separate diagnostic; conditional time-divergent
  completion needs separate accepted reasoning. The audit does not invent a new
  outcome or silently narrow that contract.
- UPPAAL [query semantics](https://docs.uppaal.org/language-reference/query-semantics/symb_queries/)
  distinguish invariant state safety from eventual/leadsto path requirements.

The observed age bound is in **3 abstract model time units**, not milliseconds
or wall-clock seconds. The frozen instance vector has no physical time scaling.

## Checked premises and local proof

Pinned full-model SHA256:
`592678ed678ce8f70cf278f542e48bd2bb739969b53a962423d3e63f91e3e1e2`.
Reduced-model SHA256:
`536233940526a1716006d6769c84c9faf6dc3d7bf0e6ffa0981aa60b56a49241`.
Exact C02 query SHA256:
`cec919bc6e2d960160976799d3d52ff4f25eea9f136f7b0231c02cec13f162db`.

`check_premises.py` is independent of the reduction generator and matches explicit
expected syntax against the actual XML. It checks unique scheduler instantiation,
initial location/recorders, all retained-variable declarations and assignments,
absence of local shadowing/reference-argument writes, ordinary clock rates,
all 17 scheduler edges, the five boundary edges, copied guards/updates/invariant
and both abstract stutter edges. Results: `premises.json`.

Zero-based scheduler transition indices and concrete XML locations:

| Cases | Retained effect | Proof role |
|---|---|---|
| Initial Idle | active=false, late=false, clocks initially 0 | Base case |
| 2, 4 outside WaitPHYAck | functional ACK clock reset | Irrelevant while inactive |
| 5 ApplySchedule -> WaitPHYAck | both clocks=0, active=true | Start and clock equality |
| 6, 7 WaitPHYAck -> Idle/Failure | active=false, age<=3 | On-time end |
| 9, 10 WaitPHYAck -> Idle/Failure | active=false, late=true, age>3 | Late-end branches retained |
| 15 WaitPHYAck self-loop | policy only | Clock/recorder values unchanged |
| Other scheduler/environment edges | no retained active/late writes | Stuttering or inactive-clock freedom |

Source references: full XML lines 353, 359–360, 418–419, 2880 and
2904–2975; the prior complete textual inventory is in the reduced package.
Other templates read the retained fields but do not write them. Global function
bodies have no retained-field references. Only one scheduler instance exists.

Let x be mac_c_phy_ack, y be mac_c_obs_ack, a be active and l be late.
Induction over concrete steps establishes a iff the scheduler is in WaitPHYAck.
On entry x=y=0. During that episode both advance equally and neither resets;
therefore x=y. The waiting invariant x<=3 gives y<=3. The only assignments setting
l=true occur on waiting exits guarded by y>3, which cannot be taken under those
premises. Thus l remains false. This is a local proof argument about the concrete
XML, supported by syntactic premise checks; it is not a new model-checking run.

For the abstraction relation, retain a,l everywhere and both clock values only
while waiting. All concrete non-wait locations map to Inactive; their clock
values are unconstrained by the relation because the query ignores them there.
Concrete delays while waiting obey the same invariant; inactive delays have no
abstract invariant. Entry restores equal clock values, exits retain the same
predicate updates and guards, and other actions stutter. Removing synchronization,
other invariants and urgency only permits more abstract actions/delays. Every
concrete finite reachable prefix therefore has a predicate-preserving abstract
prefix. This is the direction required for transferring universal state safety.
No reverse equivalence, trace lifting, liveness, or fairness preservation is claimed.

For **conditional completion**, suppose an episode starts at elapsed time t0
and never ends on a time-divergent execution. The observed clock does not reset
while active, so eventually y>3, contradicting the safety bound. Hence an end
occurs no later than t0+3 on each such execution, and every end is an ACK or
ScheduleFailure by the transition inventory. This implication quantifies only
over time-divergent executions. It does not demonstrate their existence from
every request, and does not exclude finite deadlock or infinite time-stopped paths.

## Existing machine evidence and its limits

Complete records, including actual full tool version, are linked here:

- [Reduced runs](../p3-20260924-c02-reduced/runs/p3-20260924-c02-reduced-001/results.json):
  `p3-20260924-c02-reduced-001-C02`, status=success, verdict=satisfied;
  exact reduced model/query hashes above. Tool UPPAAL 5.0.0
  (rev. 714BA9DB36F49691), June 2023. Activity/deadline witnesses and the
  invariant-removal negative control are separate records with separate hashes.
- [Full-model diagnostic records](../p3-20260923/p3-20260923-003/results.json):
  `p3-20260923-003-14-ack-unconditional-completion`, status=success,
  verdict=violated, same full model hash above; query hash
  `3f406107b55e4e196c2416c16e0573e3b362e2ff0396ab3ac696b183e252d249`;
  UPPAAL 5.0.0 (rev. 714BA9DB36F49691), June 2023.
  The earlier saved trace/report identifies a time-stopped observer loop.
- The same full records show actual `ack-start` nonvacuity (run
  `p3-20260923-003-12-ack-start`, success/satisfied, query hash
  `3d5b58517dd881b78d198f47d517e391ca4234b2cec59701834a6ad2cd6d29e6`,
  same full model and tool version). Full-model timeout reachability remains
  timeout; an abstract deadline witness does not establish that concrete outcome.
- `full-run-result.json` is a byte-for-byte copy of the supplied later attempt
  `001-29c3409912fe43029fa925b140dbf40a`: status=memory_limit, verdict=null,
  8324.0300215 seconds, peak 8590032896 bytes, threshold 8589934592 bytes,
  same full-model/C02 hashes above and actual version in that file. No verdict.
  `full-run-audit.json` records all five checked raw-file hashes, source path,
  representative telemetry and CPU/wall ratio. Full raw telemetry/stdout remain
  in the user's supplied worktree; this report is not a replacement raw archive.

## Suggested wording for the later integration response (not applied)

We evaluated the MAC dispatch-to-ACK-or-timeout contract on the frozen XML
configuration. Direct exhaustive verification reached the 8 GiB resource limit
without a verdict. A property-specific abstraction was model-checked for elapsed
safety; we provide its transition mapping and predicate-preserving simulation
argument. Subject to review of that argument, elapsed safety entails completion
within three model time units on time-divergent executions. Unconditional
completion is not claimed: a separate full-model query has a counterexample.

This wording is a proposal for independent review, not a declaration that the
reviewer's requirement is already satisfied. If the desired claim includes all
executions, report the negative result and resolve the progress semantics first.

## Reproduction and handoff

```sh
python3 -B evidence/verification/p3-20260925-c02-audit/check_premises.py
python3 -B evidence/verification/p3-20260924-c02-reduced/build.py --check
python3 -B evidence/verification/p3-20260924-c02-reduced/audit.py evidence/verification/p3-20260924-c02-reduced/runs/p3-20260924-c02-reduced-001
```

All three checks complete successfully. The premise audit rejects three in-memory
mutations: removed waiting invariant, external clock reset, and missing active
clear on an exit. It is a pinned syntactic checker, not a parser for arbitrary
UPPAAL programs or an automated theorem prover. No production software changes;
full application tests are not rerun for this report-only/static-check addition.
Final publication ref and exact HEAD are recorded in Issue #39 / follow-up PR.
Next: independent acceptance/rejection of the argument and precise C02 scope.
