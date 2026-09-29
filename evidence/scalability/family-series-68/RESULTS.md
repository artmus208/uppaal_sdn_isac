# Recorded preparation outcomes

These are full-composition diagnostic runs, not a P4 resource series or Gate 1 decision.

Source commit: `2548ec82a8fa98b3e152641fbc7a5eda30e4e07c` (published, clean at campaign start).
Actual tool: **UPPAAL 5.0.0 (rev. 714BA9DB36F49691), June 2023**.

| N | Automata | Compile | Load/parse | Capacity | Each service i=0…N−1 | Joint encoded backlog | u0 queue safety | u0 queue full |
|---|---:|---|---|---|---|---|---|---|
| 1 | 50 | success | satisfied | timeout | timeout | satisfied | violated | satisfied |
| 2 | 99 | success | satisfied | timeout | timeout, timeout | satisfied | timeout | timeout |
| 3 | 148 | success | satisfied | timeout | timeout, timeout, timeout | satisfied | timeout | timeout |
| 4 | 197 | success | satisfied | timeout | timeout, timeout, timeout, timeout | timeout | timeout | timeout |

Total native verifier wall time, including metadata/compile/load: **721.877 s** / 1200 s.
Largest monitored native peak: **216,875,008 bytes** (max sampled private bytes / reported peak working set).
Timeout thresholds were 10 s for setup and 30 s for behavior; process cleanup is included in recorded wall time.
No automatic repeats or increased limits were used. Each invocation stayed within the user’s 60 s bound.

`success` in Compile denotes compilation only. Load/parse executes only `E<> true` after parsing all query text.
`satisfied` / `violated` are explicit successful scientific-query verdicts; `timeout` has no verdict.
Joint backlog includes the absorbing overflow sentinel; it does not prove all queues are pre-overflow.
The u0 invariant is exactly the original renamed C01-queue predicate. A violation is a negative result for that predicate.

## Traceable records

Every row below links the run index containing status, model_hash, query_hash, exact tool_version, commands, parameters/vector, raw logs and trace hashes.

- [`diagnostic-001-n1-parse-load`](checks/diagnostic-001/runs.json): status=`success`, verdict=`satisfied`; 0.532 s.
- [`diagnostic-001-n2-parse-load`](checks/diagnostic-001/runs.json): status=`success`, verdict=`satisfied`; 1.005 s.
- [`diagnostic-001-n3-parse-load`](checks/diagnostic-001/runs.json): status=`success`, verdict=`satisfied`; 1.659 s.
- [`diagnostic-001-n4-parse-load`](checks/diagnostic-001/runs.json): status=`success`, verdict=`satisfied`; 2.571 s.
- [`diagnostic-001-n1-shared-capacity`](checks/diagnostic-001/runs.json): status=`timeout`, verdict=`absent`; 32.130 s.
- [`diagnostic-001-n1-u0-service`](checks/diagnostic-001/runs.json): status=`timeout`, verdict=`absent`; 32.072 s.
- [`diagnostic-001-n1-joint-backlog`](checks/diagnostic-001/runs.json): status=`success`, verdict=`satisfied`; 1.565 s.
- [`diagnostic-001-n1-u0-queue-safety`](checks/diagnostic-001/runs.json): status=`success`, verdict=`violated`; 6.224 s.
- [`diagnostic-001-n1-u0-queue-full`](checks/diagnostic-001/runs.json): status=`success`, verdict=`satisfied`; 4.782 s.
- [`diagnostic-001-n2-shared-capacity`](checks/diagnostic-001/runs.json): status=`timeout`, verdict=`absent`; 32.054 s.
- [`diagnostic-001-n2-u0-service`](checks/diagnostic-001/runs.json): status=`timeout`, verdict=`absent`; 32.075 s.
- [`diagnostic-001-n2-u1-service`](checks/diagnostic-001/runs.json): status=`timeout`, verdict=`absent`; 32.042 s.
- [`diagnostic-001-n2-joint-backlog`](checks/diagnostic-001/runs.json): status=`success`, verdict=`satisfied`; 6.183 s.
- [`diagnostic-001-n2-u0-queue-safety`](checks/diagnostic-001/runs.json): status=`timeout`, verdict=`absent`; 32.051 s.
- [`diagnostic-001-n2-u0-queue-full`](checks/diagnostic-001/runs.json): status=`timeout`, verdict=`absent`; 32.065 s.
- [`diagnostic-001-n3-shared-capacity`](checks/diagnostic-001/runs.json): status=`timeout`, verdict=`absent`; 32.079 s.
- [`diagnostic-001-n3-u0-service`](checks/diagnostic-001/runs.json): status=`timeout`, verdict=`absent`; 32.063 s.
- [`diagnostic-001-n3-u1-service`](checks/diagnostic-001/runs.json): status=`timeout`, verdict=`absent`; 32.087 s.
- [`diagnostic-001-n3-u2-service`](checks/diagnostic-001/runs.json): status=`timeout`, verdict=`absent`; 32.096 s.
- [`diagnostic-001-n3-joint-backlog`](checks/diagnostic-001/runs.json): status=`success`, verdict=`satisfied`; 19.052 s.
- [`diagnostic-001-n3-u0-queue-safety`](checks/diagnostic-001/runs.json): status=`timeout`, verdict=`absent`; 32.066 s.
- [`diagnostic-001-n3-u0-queue-full`](checks/diagnostic-001/runs.json): status=`timeout`, verdict=`absent`; 32.100 s.
- [`diagnostic-001-n4-shared-capacity`](checks/diagnostic-001/runs.json): status=`timeout`, verdict=`absent`; 32.052 s.
- [`diagnostic-001-n4-u0-service`](checks/diagnostic-001/runs.json): status=`timeout`, verdict=`absent`; 32.074 s.
- [`diagnostic-001-n4-u1-service`](checks/diagnostic-001/runs.json): status=`timeout`, verdict=`absent`; 32.097 s.
- [`diagnostic-001-n4-u2-service`](checks/diagnostic-001/runs.json): status=`timeout`, verdict=`absent`; 32.093 s.
- [`diagnostic-001-n4-u3-service`](checks/diagnostic-001/runs.json): status=`timeout`, verdict=`absent`; 32.106 s.
- [`diagnostic-001-n4-joint-backlog`](checks/diagnostic-001/runs.json): status=`timeout`, verdict=`absent`; 32.070 s.
- [`diagnostic-001-n4-u0-queue-safety`](checks/diagnostic-001/runs.json): status=`timeout`, verdict=`absent`; 32.087 s.
- [`diagnostic-001-n4-u0-queue-full`](checks/diagnostic-001/runs.json): status=`timeout`, verdict=`absent`; 32.093 s.

## Open checks and readiness

21 behavioral attempts ended without a verdict. Their formulas remain open at the recorded model hashes and budget.
All four models compiling/loading and saved diagnostic outcomes make the package reproducible and reviewable.
They do not establish per-entity service reachability or the other timed-out predicates. In particular, service reachability is needed to substantiate that the common resource is exercised by every entity.
Before claiming that nonvacuity for P4, obtain an appropriate witness under a separately justified check, or record an Integrator disposition narrowing the experimental claim. Do not add fairness or alter the model silently.
Capacity has local structural support in CONTRACT.md, but a timeout is not a successful universal model-checking result.
Future checks should be justified by their contribution to the selected P4 curves; simply repeating this campaign is not authorized by this package.
