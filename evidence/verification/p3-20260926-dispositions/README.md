# P3: dispositions and queue-safety diagnosis

Issue [#39](https://github.com/artmus208/uppaal_sdn_isac/issues/39), owner
vadimnbkg; base `read/6304dd83da71bb2b22fe829f60c32d1832d40aaf`.
Branch `codex/vadimnbkg/39-p3-dispositions-20260926`. Write scope is this
directory only. Gate 1/P1/P2 and the earlier scoped proof decisions remain intact.

The user authorized author review and merge in this session. The review is
explicitly author review, not independent approval. This deliverable records
evidence and proposed scientific dispositions; it does not accept P3, pass
Gate 2, waive an unresolved requirement, or resume deferred deadlock work.
No verifier was run and no model, query pack, generator or manuscript changed.

## Current disposition matrix

| Requirement | Evidence available | Disposition for this report | What still needs a decision/work |
| --- | --- | --- | --- |
| C01: global deadlock | Direct timeouts and a native crash; limited structural proof support, PRs #56/#57 | Unresolved; temporarily deferred by user | No deadlock-free claim; resume only on instruction or explicitly dispose of the unmet requirement |
| C01: queue bound | Full-model negative result and raw counterexample; exact diagnosis below | Checked and **violated**, not satisfied | Accept this as a reported limitation/negative finding, or authorize a separate revised model contract and baseline; neither scientific choice is silently made here |
| C01: attempt bounds/protocol | Direct model checks inconclusive; separate concrete-XML inductive argument accepted in PR #55 | Preserve accepted proof scope: primary<=1, rollback<=1, total<=2 and recorder discipline per episode | No inference of successful recovery, termination or global deadlock freedom |
| C02: bounded response | Full-model direct checks inconclusive; reduced-model safety result and pinned transfer/time-divergence argument accepted in PR #53 | Preserve the accepted scoped argument: ACK-or-timeout within 3 abstract units on time-divergent executions | No positive direct full-model verdict; no unconditional completion, guaranteed ACK delivery or existence of a time-divergent continuation from every request |
| C03: actual model-checking results | 43 raw-audited selected-query executions from 12 archives | Evidence available for acceptance, including negative and inconclusive results | P3 core acceptance remains a separate explicit decision |
| C04: counterexamples | Both distinct negative formulas have retained raw traces; queue and unconditional ACK-completion reports | Evidence available for acceptance | Use the exact trace scope; symbolic traces are not concrete physical timelines |
| C05: reproducibility/resources | Version, configuration, instances, runtime, peak memory and hardware retained for the 12 audited archives | Partial evidence readiness; explicit artifact gap below | Recover joint-probe raw archive or explicitly restrict accepted evidence; separately decide whether to reinstate recovered C02 resource evidence |
| C06: practical verifiability/state explosion | Baseline run costs and inconclusive results only | Pending P4 | Requires accepted scaling series and qualified interpretation; neither a timeout nor one memory stop proves a general scaling boundary |

Supporting reachability obligations remain separate: native start, direct rollback
and ACK-timeout witnesses exist; primary dispatch and two-attempt reachability
remain inconclusive. The accepted joint-prerequisite decision is narrower than
receiver readiness or dispatch. The latter two receiver probes are timeout/null.

`audit.json` contains every indexed run's exact `run_id`, `status`, `verdict`,
`model_hash`, `query_hash`, actual full `tool_version`, command, timestamps,
resources and raw/metadata references. Selected formulas and supplemental probes
are not conflated. The recovered manager attempt is also kept separate from the
43 selected-query executions, avoiding changes to historical totals/acceptance.

## What the queue counterexample actually establishes

Frozen model SHA256:
`592678ed678ce8f70cf278f542e48bd2bb739969b53a962423d3e63f91e3e1e2`.
Run `p3-20260923-003-02-C01-queue`, status `success`, verdict `violated`;
query SHA256 `694501c262583dfe43e22a907f10080795fd63b8bc534a11cd9338c84a704051`;
actual UPPAAL `5.0.0 (rev. 714BA9DB36F49691), June 2023` (full banner in JSON).
Query: `A[] !mac_queue_overflow_seen`.

The archived witness has five load transitions with `arrival=1`, `service=0`.
Occupancy changes `0 -> 1 -> 2 -> 3 -> 4 -> 5`, capacity `K=4`; the last change
sets the sticky overflow flag. Four matching PHY ACK transitions on the same
path do not change occupancy. `audit.py` derives these facts from the archived
trace, checks them against the frozen transition syntax and emits exact state
and edge references. This is a witness audit, not a new independent timed replay.

This behavior matches the accepted queue semantics:

- [Original queue contract](../../instantiation/20260922-queue-abstraction-contract/README.md):
  optional service even in communication modes, arrival independent of deferred
  admission work, no drop policy, ACK is not a dequeue event.
- [Implementation](../../instantiation/20260922-queue-implementation/README.md)
  and frozen `Boundary_E_MAC_LOAD`: `next=q-service+arrival`, one writer, explicit
  `K+1` overflow witness; the guard allows service zero in every mode.
- [Accepted P1/P2 scope](../../governance/20260910-p1-p2-review/final-20260923/README.md):
  queue implementation/ranges accepted, full-model non-overflow left to P3.

Thus the implementation is not shown to violate its queue contract; the
**universal non-overflow property is false for the accepted environment**.
Checking a requirement and obtaining a counterexample is useful verification
evidence, but it does not establish that the system meets that requirement.
This is one aggregate abstract MAC queue, not every physical network buffer.

Recommended disposition: retain the negative finding on the current baseline
and qualify the article's queue-safety claim. Do not introduce service fairness,
capacity clipping, dropped arrivals or ACK-as-service merely to turn this result
positive. If universal non-overflow is essential, first specify a justified
admission/service envelope, then authorize P2/model work and a new baseline.
Even eventual service fairness alone does not bound the finite arrival burst
before the first service. No such redesign or scientific waiver is authorized
by merging this evidence report.

Suggested integration wording (proposal, not a manuscript edit):

> The aggregate MAC queue bound is violated under the accepted nondeterministic
> load/service abstraction: a retained full-model counterexample reaches the
> overflow witness after five arrivals without service at capacity four.
> Successful control ACKs on that path do not constitute data service.
> The model therefore supplies a negative queue-safety result, not a guarantee
> of loss-free operation under unconstrained arrivals and optional service.

## Recovered C02 evidence

The earlier Issue #39/PR #53 disposition excluded attempt
`001-29c3409912fe43029fa925b140dbf40a` because its raw archive was unavailable.
This session found the original tracked package in owner-local branch/bundle
at commit `93f8dfee5ff08d73d4ad6e289b6d418bd747a662`.

`recovered-c02.tar.xz` exports **exact committed blobs** from that checkpoint;
it does not copy potentially changed working files. `recovery-provenance.json`
records the source path, commit and archive hash. `recovered-manager.py` preserves
the actual manager source from `48ee12bd24bed28163bd4fd40729c79392bebff9` as a
historical artifact, not a replacement for the current application module.

The audit checks all five attempt artifact hashes, input hashes, raw version,
session/queue hash, manager hash, parameters/vector, monotonic telemetry and
measured peak. The original result is byte-identical to PR #53's supplied
`full-run-result.json`. Terminal status remains `memory_limit`, verdict null.
The restored record reports 8324.0300215 seconds and 8590032896 peak working-set
bytes; these are **recovered diagnostic values, not reinstated accepted resource
results**. Query hash is
`cec919bc6e2d960160976799d3d52ff4f25eea9f136f7b0231c02cec13f162db`, full model
hash as above, actual tool `UPPAAL 5.0.0 (rev. 714BA9DB36F49691), June 2023`.

Historical preparation files inside the export still say `not_started` and
identify the older manager. They are preserved unchanged. Terminal attempt
`result.json`, `memory-limit-report.json` and its session identify the later
execution. The package contains the first write-error attempt and software smoke
as historical context; this audit does not count them as new baseline results.
No new attempt was run. The original exclusion decision is not rewritten:
restoration makes reconsideration possible, but never supplies a satisfied C02
verdict or a P4 benchmark.

## Newly identified joint-probe artifact gap

At the pinned base, metadata for `p3-20260925-primary-joint-001` references
`evidence/verification/runs/p3-20260925-primary-joint-001.tar.xz`, SHA256
`3d00c5cd34ab59266a1dcc159ade2d5a7d75109ec4dd03df5da8fc515ae9c4c7`.
Neither that archive nor its raw directory is present in the committed tree.
The named archive was also not found in the current workspace or `/tmp` search.
No claim is made that no other machine or storage has a copy.

All three metadata records remain indexed with `raw_audited=false`; the native
joint-prerequisite success is **reported by saved metadata**, not independently
revalidated here. The user's accepted joint-prerequisite review is preserved.
Evidence availability and acceptance history are different facts. Existing
`p3-20260925-primary-joint/audit.py` expects an absent raw directory and cannot
be reproduced from this checkout. Recover the original matching archive or
explicitly limit its evidentiary use; do not invent raw output or rerun solely
to replace the historical execution.

## Reproduction and next work

From a clean checkout, Python 3.12 or later:

```sh
python3 -B evidence/verification/p3-20260926-dispositions/audit.py
python3 scripts/check_coordination.py
python3 scripts/check_coordination.py --audit-hashes --commit HEAD --output /tmp/p3-new-baseline-audit.json
python3 -m unittest discover -s tests -v
```

Install the project and PyYAML in an isolated environment for the application
suite and baseline audit. `audit.py` itself uses only the standard library,
performs no network access and invokes no verifier. `--write` regenerates only
this report's `audit.json`. Commands/results and author review are recorded in
`checks.txt` and `author-review.md`.

Next within P3: resolve the explicit queue disposition, restore/dispose of the
joint raw-artifact gap, then continue the selected receiver/primary/two-attempt
diagnostics. Deadlock remains deferred. The collaboration contract distinguishes
`P3_core_evidence_accepted` (C01–C05, unlocks P5 acceptance) from `P3_complete`
(adds C06 after P4). Neither milestone is claimed by this report or its merge.
