# C01 follow-up and P3 disposition — Issue #39

Owner: vadimnbkg. Branch: `codex/vadimnbkg/39-c01-followup`, target `read`.
Base and execution source: `152d167165f0ff07a801d85a8671b6cd6bb96b54`
(accepted PR #53 merge). Write scope: `evidence/verification/**` only.
Frozen baseline: `reviewer-r1-gate1-20260923`; no model/query/parameter changes.

## Recorded acceptance context

The user accepted the PR #53 review and the pinned C02 safety-transfer argument,
with ACK-or-timeout completion within three abstract time units on time-divergent
executions. The narrow exception to the earlier reduced-harness transfer rule is
recorded in [#39](https://github.com/artmus208/uppaal_sdn_isac/issues/39) and
[PR #53](https://github.com/artmus208/uppaal_sdn_isac/pull/53).
This does not establish unconditional completion, absence of deadlock/Zeno,
successful PHY delivery, or a time-divergent continuation from every request.

The supplied attempt `001-29c3409912fe43029fa925b140dbf40a` has lost its raw
archive, as confirmed by the user. Its copied result/audit remain historical
diagnostics only; its runtime, memory and resource-limit figures are excluded
from accepted experimental evidence and C05/C06 quantitative conclusions.
Earlier historical integration wording quoting those figures is superseded by
this disposition. The C02 argument uses the separately retained reduced-model
evidence and pinned-source reasoning, not that lost attempt.

## Authorized execution

Run `p3-20260925-c01-001`: exact full-model queries `C01-deadlock`,
`C01-attempts`, and `attempt-protocol`. DFS (`-o 1`), some diagnostic trace
(`-t 0`), 300 seconds per query, sequential execution, existing sampled 2 GiB
working-set stop. The 50 ms polling threshold is not a hard allocation cap.
No automatic resource increase or model reduction is authorized here.

The source tree was clean at launch. Frozen-input audit, actual tool version,
Windows hardware, native commands and all stdout/stderr/trace bytes are retained
under the unique run ID. Pending execution is not a verification result.

Reproduction from the execution source, using a fresh run ID and matching tool:

```sh
python3 -B evidence/verification/p3-20260923/run.py \
  --run-id NEW-UNIQUE-RUN-ID \
  --ids C01-deadlock,C01-attempts,attempt-protocol \
  --search-order 1 --trace-kind 0 --timeout-seconds 300 \
  --verifyta /mnt/d/UPPAAL/app/bin/verifyta.exe
```

New runs require review; this continuation does not accept P3 or the P4-dependent C06.

## Observed C01 follow-up results

| Property | Status | Verdict | Seconds | Peak working set, bytes |
|---|---|---|---:|---:|
| C01-deadlock | timeout | none | 300.067225 | 290000896 |
| C01-attempts | timeout | none | 300.096745 | 543559680 |
| attempt-protocol | timeout | none | 300.121803 | 503463936 |

The exact per-query run IDs, model/query hashes, actual tool version, commands,
source commit, Windows hardware and limits are in
[run.yaml](../p3-20260923/p3-20260925-c01-001/run.yaml) and
[results.json](../p3-20260923/p3-20260925-c01-001/results.json).
The complete raw archive is
[the run tar.xz](../runs/p3-20260925-c01-001.tar.xz), with its hash in
[archive.json](../p3-20260923/p3-20260925-c01-001/archive.json).
No runtime failure or timeout is counted as a property verdict. No total
explored-state count is supplied by this tool; progress Load is not substituted.

## C01–C05 disposition

| ID | Evidence and remaining scope |
|---|---|
| C01 | Queue overflow has a retained full-model counterexample (q=5 at K=4). Deadlock and attempt limits are tracked above; no positive result is inferred from timeout. Recorder protocol correctness is a separate obligation. |
| C02 | User accepted the PR #53 pinned safety-transfer argument and time-divergent completion scope. Reduced machine result is separate from the inconclusive direct full-model runs. Unconditional ACK completion remains violated. |
| C03 | Full-model machine verdicts and inconclusive runs are retained individually in results-index.json; reduced results have their own identity. |
| C04 | Original queue and unconditional-completion counterexamples remain in p3-20260923-003.tar.xz; the reduced negative control retains its own trace. No counterexample is inferred from timeout. |
| C05 | Complete raw archive and per-run native hardware/provenance are preserved for this continuation. The lost-archive attempt is explicitly excluded. Short reduced runs have unavailable memory samples, not zero consumption. |

Four full-model reachability formulas were satisfied in the September 23 runs;
these witnesses do not replace universal safety checks. Attempt-start/primary/
rollback/two and ACK-timeout reachability still lack a conclusive full-model
result in the preserved series. The C02 scope exception does not authorize
transferring other reduced models. P3 core acceptance remains separate; C06
additionally requires P4.

## Audit and handoff

Extract the raw archive into a separate directory and run:

```sh
python3 -B evidence/verification/p3-20260923/audit.py /PATH/p3-20260925-c01-001
```

See checks.txt for actual validation commands and outputs. No production or
runner code was changed, and no new full application-suite run is claimed.
Exact published HEAD and PR reference are recorded in Issue #39.
