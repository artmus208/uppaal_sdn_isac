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

Results and final audit will be appended after execution completes. New runs
require review; this continuation does not accept P3 or the P4-dependent C06.
