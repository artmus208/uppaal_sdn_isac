# Recovery-start reachability witness — P3 / Issue #39

Original full frozen-model query `E<> sdn_attempt_active` now has a positive
machine result. Run `p3-20260925-recovery-001-01-attempt-start`:
`status=success`, `verdict=satisfied`, exit 0, runtime 10.0101312 seconds,
peak native working set 186454016 bytes. This is an existential witness that
a recovery episode can start, not a guarantee that it finishes or succeeds.

- Model SHA256: `592678ed678ce8f70cf278f542e48bd2bb739969b53a962423d3e63f91e3e1e2`.
- Query SHA256: `b2bd4430e694dc28cbe282e253a50b0f2554b37b0901a0bb378cec8eda3757c4`.
- Actual tool: UPPAAL 5.0.0 (rev. 714BA9DB36F49691), June 2023.
- Clean published execution source/base read: `7a4ac3c47329548612b0a563bf9cae20e3835384`.
- Owner vadimnbkg; branch `codex/vadimnbkg/39-recovery-reachability`, target read.
- Baseline reviewer-r1-gate1-20260923, accepted Gate 1/P1/P2. Frozen inputs unchanged.

## Witness

The saved symbolic trace ends with matching `sdn_link_failure!/?` edges and
`sdn_A_REC_0.FailureDetected`. At its endpoint `sdn_attempt_active=1`, with
primary, rollback and total counters all zero. `audit.py` follows transitions
from the declared initial node instead of relying on XML node serialization
order, checks the terminal variable/location vectors and matching channel.
It checks the recorded witness endpoint; it is not an independent timed replay
or a replacement for the native verdict. No concrete timing is guessed from
symbolic zones, and trace length is not an explored-state count.

## Execution and evidence

```sh
python3 evidence/verification/p3-20260923/run.py \
  --run-id p3-20260925-recovery-001 --ids attempt-start \
  --search-order 2 --seed 20260925 --state-representation 1 \
  --trace-kind 0 --timeout-seconds 60 \
  --verifyta /mnt/d/UPPAAL/app/bin/verifyta.exe
```

Symbolic randomized DFS, exact compact DBM, explicit seed, some trace;
60-second and sampled 2-GiB limits, one native process. Use a fresh run ID for
any authorized reproduction. Complete raw logs, query, trace, config, native
result, version, hardware, baseline audit and SHA256SUMS are in
`evidence/verification/runs/p3-20260925-recovery-001.tar.xz`. Tracked metadata
and archive hash are in `evidence/verification/p3-20260923/p3-20260925-recovery-001/`.
`run.yaml` preserves actual OS/hardware, parameters/vector, source/generator
identity, exact command and full tool version. Native memory is sampled, not a
hard allocation cap; total explored states remain unavailable.

Audit without another UPPAAL execution:

```sh
python3 evidence/verification/p3-20260925-recovery/audit.py
```

Archive SHA256/raw hashes, frozen identity, extracted metadata copies, status,
trace presence and endpoint checks pass. Output is in checks.txt. Baseline
audit matches all 57 file hashes and both aggregates. Runner/application code
unchanged; full application checks are run by current-head CI, recorded in PR.

## Disposition and handoff

Previous attempt-start timeouts remain historical evidence; this new completed
positive run supplies the previously missing full-model nonvacuity witness.
PR #58's 38-execution index is an earlier immutable snapshot and is not edited:
with this additional run there are 39 executions, seven completed machine
results and five distinct satisfied formulas. Two formulas remain violated;
eight remain directly machine-inconclusive. Accepted proof scopes remain
separate from direct results. This report does not accept all P3/C01.

Next selected diagnostics remain primary/rollback/two-attempt reachability and
ACK-timeout reachability. Global deadlock stays temporarily deferred by the
user; no deadlock search or proof work was resumed. PR #57/#58 acceptance is
not inferred. No new Issue, model/query change, resource escalation, P4 work or
merge. All additions are within the unique evidence paths assigned in #39.

## Dispatch follow-up — run 002

User instructed «работаем» after the start witness. Same existing #39 and PR,
with execution source `bf1dc81db827e051d8e0d3b75222ee5f72b18a00` (clean published
checkpoint). Same frozen inputs, tool, seed, symbolic random DFS, exact compact
DBM and 60-second/2-GiB limits; three existing formulas executed sequentially.

| Property | Formula | Status/verdict | Runtime seconds | Peak working set bytes |
| --- | --- | --- | ---: | ---: |
| attempt-primary | E<> sdn_attempt_primary == 1 | timeout/null | 60.0960762 | 273403904 |
| attempt-rollback | E<> sdn_attempt_rollback == 1 | success/satisfied | 9.886706799999999 | 186241024 |
| attempt-two | E<> sdn_attempt_total == 2 | timeout/null | 60.0817084 | 263729152 |

Exact run IDs are `p3-20260925-recovery-002-01-attempt-primary`,
`p3-20260925-recovery-002-02-attempt-rollback`, and
`p3-20260925-recovery-002-03-attempt-two`. Their query hashes, model hash,
full actual version and all command/environment/hardware provenance are in
`evidence/verification/p3-20260923/p3-20260925-recovery-002/results.json` and
`run.yaml`. Complete archive:
`evidence/verification/runs/p3-20260925-recovery-002.tar.xz`; SHA256 recorded in
that group's `archive.json`. No verdict or trace is inferred from timeout.

The rollback witness ends at `sdn_A_REC_0.Rollback`, active=1, primary=0,
rollback=1, total=1. Its last recovery edge is directly FailureDetected to
Rollback, synchronizing on `bus_rollback_request!`. Thus rollback is possible
**without a preceding primary attempt**. This witness must not be presented as
successful primary recovery, rollback completion or a two-attempt episode.
Primary/two remain unresolved; timeout does not show either is impossible.

```sh
python3 evidence/verification/p3-20260923/run.py \
  --run-id p3-20260925-recovery-002 \
  --ids attempt-primary,attempt-rollback,attempt-two \
  --search-order 2 --seed 20260925 --state-representation 1 \
  --trace-kind 0 --timeout-seconds 60 \
  --verifyta /mnt/d/UPPAAL/app/bin/verifyta.exe
python3 evidence/verification/p3-20260925-recovery/audit-dispatch.py
```

As above, native reproduction requires a fresh run ID. The audit extracts the
archive, checks raw hashes, metadata copies, formula/result identities and
walks each successful trace from its initial node to check the actual query
counter at its endpoint. It does not perform independent timed replay. Output
is preserved in `checks-dispatch.txt`; baseline again matches 57 file hashes
and both aggregates. Full software suite is run by current-head CI; no runner
or application changes. Earlier raw evidence remains immutable.

Cumulative full-model evidence now has 42 executions, eight completed machine
results, six distinct satisfied formulas, two violated and seven directly
machine-inconclusive. Earlier index/counts describe their earlier checkpoints.
Accepted proof scopes stay separate. Remaining selected reachability gaps:
primary, two-attempt and ACK-timeout. Further identical primary/two repeats
are not scheduled automatically; a useful next diagnostic is the previously
selected ACK-timeout reachability, with a separate preserved run. Deadlock
remains deferred; no PR acceptance, merge, P3 closure or new Issue inferred.

## ACK-timeout follow-up

User instructed «Работай» after dispatch checks. Original selected formula
`E<> mac_phy_ack_timeout` now has a positive full-model result:
`p3-20260925-ack-timeout-001-01-ack-timeout`, status=success,
verdict=satisfied, native exit 0, runtime 10.1930517 seconds, peak native working
set 192172032 bytes. Clean published execution source:
`e5361bdbb7daa56a0b747345390689e533524f0e`.

Same full frozen model SHA256
`592678ed678ce8f70cf278f542e48bd2bb739969b53a962423d3e63f91e3e1e2` and actual
UPPAAL 5.0.0 (rev. 714BA9DB36F49691), June 2023. Individual query hash and full
version are in `evidence/verification/p3-20260923/p3-20260925-ack-timeout-001/results.json`.
That directory also retains run.json/run.yaml with source/generator identity,
parameters/vector, hardware/OS/environment and exact command. Complete raw
archive: `evidence/verification/runs/p3-20260925-ack-timeout-001.tar.xz`;
its SHA256 is in the group's archive.json.

The 134-transition symbolic witness ends at `mac_A_SCH_0.ScheduleFailure`:
ACK-timeout=1, PHY-command-pending=0, ACK-observer-active=0,
ACK-observer-late=0 and MAC-report-pending=1. This witnesses the timeout outcome
and closure of the observed ACK wait in this execution. It does not show that
a report has been delivered, that every wait ends, successful ACK delivery or
absence of deadlock. Trace length is not an explored-state count. Endpoint
inspection is not independent timed replay or a concrete timing measurement.

```sh
python3 evidence/verification/p3-20260923/run.py \
  --run-id p3-20260925-ack-timeout-001 --ids ack-timeout \
  --search-order 2 --seed 20260925 --state-representation 1 \
  --trace-kind 0 --timeout-seconds 60 \
  --verifyta /mnt/d/UPPAAL/app/bin/verifyta.exe
python3 evidence/verification/p3-20260925-recovery/audit-ack-timeout.py
```

Same symbolic randomized DFS/exact compact DBM/seed and 60-second/sampled
2-GiB limits. Use a fresh run ID for native reproduction. Extracted archive,
raw-file hashes, metadata copies, formula/result identity, trace and endpoint
checks pass; audit output in checks-ack-timeout.txt. All 57 frozen file hashes
and both aggregates match. Application/runner unchanged; current-head CI is
recorded in the PR, separately from the UPPAAL result.

Cumulative full-model evidence now: 43 executions, 9 completed machine results,
7 distinct satisfied formulas, 2 violated, 6 directly machine-inconclusive.
Earlier counts are historical snapshots. Among the selected reachability
formulas only **attempt-primary and attempt-two** remain unresolved. Existing
accepted attempt/protocol and scoped C02 proofs remain separate from native
results; deadlock remains temporarily deferred. No resource escalation, new
Issue, PR acceptance/merge or P3 closure is implied.

## Why the saved witnesses do not show a primary attempt

`diagnose-primary.py` evaluates the exact pinned recovery guards against the
FailureDetected states in the two saved witnesses. Reproduce with:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 evidence/verification/p3-20260925-recovery/diagnose-primary.py
```

Output is `primary-guard-diagnosis.json`. Both archives are hash-checked before
reading; earlier raw audits remain applicable. Exact function/guard syntax and
numeric enum definitions are checked before evaluating their transcription.
No general UPPAAL evaluator, symbolic replay or new verifier run is claimed.

| Witness state | Standby | Alternative | Telemetry | Policy | Both primary guards |
| --- | --- | --- | --- | --- | --- |
| recovery-001 / State128 | false | true | MISSING (2) | REJECT (5) | false |
| recovery-002 / State120 | false | false | FRESH (0) | REJECT (5) | false |

Primary dispatch requires either standby or an alternative **and** fresh
telemetry **and** a policy other than CONSTRAINED/REJECT. In the first witness
availability alone is insufficient; telemetry and policy both prohibit the
primary. In the second, fresh telemetry alone is insufficient; availability
and policy prohibit it. The direct rollback guard holds in both states.
These are observed local blockers, not the cause of the entire search timeout
and not an invariant over every reachable state. The stored policy is checked
at this state; we do not infer why a previous policy evaluation selected it.

Primary guards alone are not sufficient for a global transition. Channels
`bus_rec_policy_request` and `bus_rec_flow_request` are binary. The policy
receiver is Boundary_B_POLICY.Idle; the flow receivers are the five *_Idle
locations of Boundary_E_FAULT. Receiver availability, updates and target
invariants still have to hold. The XML contains selectable availability flags,
so their false initial values cannot establish permanent absence of a primary.

The next discriminating question is whether FailureDetected can coexist with
available standby/alternative, fresh telemetry, a permitted policy and a
compatible binary receiver. A new targeted reachability probe would need its
own query identity and explicit diagnostic scope; its witness would still need
to include the actual dispatch to close the original attempt-primary formula.
Alternatively, another bounded seed on the original formula could seek that
witness directly, with no assurance of success. Neither experiment is executed
or silently added here. Changing the frozen initial flags or forcing NORMAL
policy would change the model and cannot prove the original claim.

Synthetic guard checks confirm that fresh/permitted/alternative=true enables
the local alternative guard, and flipping either freshness or policy disables
it. These checks are not evidence that such a valuation is reachable. For
attempt-two, a primary dispatch must precede rollback in the same episode
under the accepted recorder invariant; direct rollback with total=1 does not
suffice. Global deadlock remains deferred. No resource increase or new Issue.
