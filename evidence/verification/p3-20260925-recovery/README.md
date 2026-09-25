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
