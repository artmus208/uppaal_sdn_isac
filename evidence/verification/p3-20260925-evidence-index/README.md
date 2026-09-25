# P3 evidence consolidation after temporary deadlock deferral

Existing Issue #39, C03–C05; owner vadimnbkg. Base `read`:
`7a4ac3c47329548612b0a563bf9cae20e3835384` (accepted PR #56 merge).
Branch `codex/vadimnbkg/39-p3-evidence-index`. Scope: this directory only.

## User decision and limits

On 2026-09-25 the user instructed «тогда скипай его пока, работаем дальше».
Further global deadlock work is temporarily deferred. `C01-deadlock` remains
unproved; old error/timeout results remain unchanged. No new deadlock searches
or structural proof continuation are performed here. Historical records remain
in the index for completeness. This does not permanently waive the requirement,
accept P3, change Gate 1, or authorize a positive statement in the manuscript.
PR #57 is preserved separately and remains unmerged/pending review; this request
is not its acceptance. The decision is recorded in Issue #39.

This deliverable consolidates already retained results, counterexamples and
resource provenance. No UPPAAL query, model generation or model modification
is performed. The lost-archive attempt remains excluded. No new Issue is created.

## Full frozen-model results

The nine complete archived groups contain **38 distinct query executions** of
15 formulas: 6 success, 30 timeout, 2 error. At the formula level, four have a
positive machine result, two have a negative result and nine remain machine-
inconclusive. Repeated attempts and intermediate progress archives are not
counted as new properties or extra executions. A success can be a satisfied
or violated formula; it means a completed machine result, not universal safety.

| Formula | Direct full-model result | Current disposition |
| --- | --- | --- |
| C01-deadlock | inconclusive | Temporarily deferred by user |
| C01-queue | violated | Retained queue-overflow counterexample; no safety claim |
| C01-attempts | inconclusive | Separate concrete-XML inductive proof accepted in PR #55 |
| attempt-protocol | inconclusive | Separate concrete-XML inductive proof accepted in PR #55 |
| C02-ack-elapsed | inconclusive | Scoped safety-transfer argument accepted in PR #53 |
| queue-nonempty | satisfied | Reachability witness |
| queue-full | satisfied | Reachability witness |
| queue-overflow | satisfied | Reachability of the safety violation |
| attempt-start | inconclusive | Recovery-start nonvacuity still unresolved |
| attempt-primary | inconclusive | Primary-dispatch nonvacuity still unresolved |
| attempt-rollback | inconclusive | Rollback nonvacuity still unresolved |
| attempt-two | inconclusive | Two-attempt nonvacuity still unresolved |
| ack-start | satisfied | ACK-start reachability witness |
| ack-timeout | inconclusive | Timeout-event reachability still unresolved |
| ack-unconditional-completion | violated | Retained noncompletion trace; distinct from scoped C02 |

Each row in `results-index.json` carries its exact formula and query hash,
run_id/status/verdict/model_hash/tool_version, source commit, runtime, peak
memory, trace paths and references to raw logs, archive and full metadata.
`run.yaml` supplies source/generator hashes, parameters, instance vector,
actual hardware/OS/environment and command/options. Neither a proof acceptance
nor deferral overwrites a machine verdict.

Full model SHA256:
`592678ed678ce8f70cf278f542e48bd2bb739969b53a962423d3e63f91e3e1e2`.
Baseline: `reviewer-r1-gate1-20260923`. Actual native version retained per run:
UPPAAL 5.0.0 (rev. 714BA9DB36F49691), June 2023.

## C04 counterexamples

Both full-model negative results are in
`evidence/verification/runs/p3-20260923-003.tar.xz`:

| Run ID | Exact trace path inside archive | Interpretation |
| --- | --- | --- |
| p3-20260923-003-02-C01-queue | p3-20260923-003/02-C01-queue-trace1.xml | q reaches 5 at K=4; optional service allows arrivals without dequeue. ACK does not dequeue. |
| p3-20260923-003-14-ack-unconditional-completion | p3-20260923-003/14-ack-unconditional-completion-trace1.xml | Time-stopped observer loop with ACK active; not a refutation of the accepted time-divergent scoped C02 argument. |

The exact formulas, identities and per-run provenance are in the index and
linked metadata. Trace integrity/presence and machine verdicts are audited;
semantic interpretations above are carried from the preceding P3 report,
not claimed as newly replayed or newly independently reviewed.

Reduced C02 results and the invariant-removal negative control remain in
`evidence/verification/p3-20260924-c02-reduced/`. They have different model
hashes and are not mixed into the full-model table. PR #53 accepts only the
pinned elapsed-safety transfer and ACK-or-timeout completion within three
abstract units on time-divergent executions; it does not establish unconditional
completion, successful PHY delivery, deadlock/Zeno freedom or the existence of
a time-divergent continuation from every request.

## C05 evidence coverage and exclusions

The audit opens every indexed archive, checks its SHA256, extracts it into a
fresh temporary directory, checks raw-file hashes and formula identity/status,
and compares archived run.json/run.yaml/results.json byte-for-byte with the
tracked metadata copies. Every group retains hardware, OS, tool version,
parameters/vector and source/generator identity. Counterexample traces exist
and are nonempty. The archive manifest list is read from the pinned repository;
missing expected groups or an unexpected execution count fails the audit.

Memory is a sampled native working-set metric, with the documented 50 ms
sampling/stop limitations. No total explored-state count is available; null
is preserved and progress Load is not substituted. Unavailable memory samples
in the separate reduced package are not zero memory consumption. No scalability
conclusion is inferred from timings or from the number of attempts.

Excluded from the quantitative full-model table:

- Intermediate progress archives: partial duplicates of final groups.
- p3-20260923-001: incomplete preflight with no formula execution.
- Supplied attempt 001-29c3409912fe43029fa925b140dbf40a: raw archive lost by user
  confirmation; historical summary only, not accepted timing/memory evidence.
- Reduced C02 and negative-control models: separate identities and claim scope.

## Remaining work after deferral

The next unresolved diagnostic inside existing P3 is **recovery-start
reachability** (`attempt-start`), followed by primary/rollback/two-attempt
reachability and ACK-timeout reachability. These are already selected formulas,
not newly added tasks. The accepted attempt-bound proof does not demonstrate
that a recovery episode actually occurs. No repeat budget is silently increased
by this consolidation, and no claim of successful recovery is inferred.

C03–C05 now have one reproducible evidence index for review. C01 queue safety
still has a negative result requiring an explicit limitation/repair disposition;
repairing the frozen model is outside this scope. C06 still depends on accepted
P4 evidence. The temporary deadlock deferral therefore does not by itself
close all of P3 or lift downstream acceptance dependencies.

## Reproduction

```sh
PYTHONDONTWRITEBYTECODE=1 python3 evidence/verification/p3-20260925-evidence-index/build.py
```

This audits all nine archives and compares the reconstructed index exactly with
the committed JSON. `--write` regenerates only that new index. The script imports
the existing raw-evidence auditor and does not execute verifyta. `checks.txt`
records performed checks. The user decision, current branch/HEAD, CI and handoff
are recorded in Issue #39 and the evidence PR; no producer self-acceptance.
