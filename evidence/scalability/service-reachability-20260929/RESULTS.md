# Outcomes — Issue #70

All ten scientific attempts ended with `status=timeout`, no property verdict and no witness trace. Service reachability remains open for every entity. This is not evidence of unreachability.

Scientific source commit: `ecf08b52dadce0d5413307775f6b1d36cd13fabb` (published and clean at launch).
Candidate model/query commit: `a51a77e7852aee514bb0217a17d970fcf94cb704`.
Actual tool: **UPPAAL 5.0.0 (rev. 714BA9DB36F49691), June 2023**.

Aggregate verifier/metadata wall accounting: **322.128423 s** / 420 s, including the retained initial version call. Peak native memory across scientific cells: **1,058,213,888 bytes** / 2 GiB.

Each process was stopped at the 30 s timeout threshold; recorded end-to-end duration includes shutdown/cleanup (about 32 s). Every process was reaped. No memory-limit cell, retry, seed sweep, model/query change or limit escalation occurred.

| run_id | status | verdict | wall seconds | native peak bytes |
|---|---|---|---:|---:|
| `service-002-n1-u0-service` | timeout | absent | 32.148250 | 248950784 |
| `service-002-n2-u0-service` | timeout | absent | 32.122248 | 365244416 |
| `service-002-n2-u1-service` | timeout | absent | 32.110746 | 360591360 |
| `service-002-n3-u0-service` | timeout | absent | 32.196705 | 646529024 |
| `service-002-n3-u1-service` | timeout | absent | 32.226043 | 645189632 |
| `service-002-n3-u2-service` | timeout | absent | 32.194091 | 645103616 |
| `service-002-n4-u0-service` | timeout | absent | 32.225037 | 1042599936 |
| `service-002-n4-u1-service` | timeout | absent | 32.188705 | 1058213888 |
| `service-002-n4-u2-service` | timeout | absent | 32.258331 | 1020739584 |
| `service-002-n4-u3-service` | timeout | absent | 32.243658 | 1057501184 |

Every row resolves through [runs.json](runs/service-002/runs.json) to model_hash, query_hash, exact tool_version, source commit, parameters/vector, actual command, per-run hardware/available RAM, raw stdout/stderr and native memory samples. [audit.json](checks/audit.json) repeats the minimum identity/hash/version tuple per row. Trace availability is explicitly `not_produced`.

Host: Windows 11 Pro build 26200, AMD Ryzen 5 1400, 8 logical CPUs; full measurements and timestamps are in each hardware record. The search was random depth first, seed 20260929, exhaustive symbolic exploration, compact DBM, on the unchanged full models. This is a diagnostic campaign, not a resource comparison against #68 or a P4 series.

## Preserved setup failure

`service-001` stopped in tool metadata: `--version` exited 0 but was too short for memory sampling. Its monitor error and raw files remain unchanged. That version output was reused, never rerun. `service-002` executes each of the original ten scientific queries exactly once. Metadata memory is unavailable; scientific memory monitoring remains mandatory. The driver initially reported a missing result file across the WSL boundary; the subsequently visible monitor result supplies the actual zero-sample failure.

## Disposition

The alternative traversal did not resolve the service-nonvacuity blocker within the agreed budget. No successful verification claim, shared-resource-use claim, fairness/useful-departure claim, new Gate 1, P4 readiness or R03/R04/C06 closure follows. [NEXT.md](NEXT.md) states the return conditions: a separately justified full-model witness task or an explicit Integrator decision narrowing the experimental claim. Automatic further attempts are out of scope.
