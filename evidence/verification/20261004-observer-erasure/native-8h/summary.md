# Completed 8-hour / 7-GiB native campaign

Both sequential attempts ended at the sampled memory stop, before their 28800-second time limits. Neither formula has a native verdict.

Native version: UPPAAL 5.0.0 (rev. 714BA9DB36F49691), June 2023.
Execution commit: 2a8b967e4899639c0e1b2ceb21b89a0ecc7a0e9c. Fixed BFS options: -o 0 -t 0. Exact source queries and diagnostic model unchanged.

| Run | Status | Verdict | Seconds | Peak bytes | CPU seconds |
|---|---|---|---:|---:|---:|
| observer-erasure-116-20261005-completion-safety-04 | memory_limit | none | 6593.531 | 7518007296 | 6510.328 |
| observer-erasure-116-20261005-success-04 | memory_limit | none | 6762.453 | 7517257728 | 6678.047 |

The sampled aggregate working-set stop is 7516192768 bytes (7168 MiB); polling permits a small overshoot. Worker exit code 2 records an incomplete verification campaign, not a manager exception: both planned attempts produced memory_limit records. No trace, retry, duplicate attempt, manager repair or recurring status-write error occurred.

Results.json preserves full commands, native version, model/query hashes, execution commit and raw result hashes. Validation.json records input/runtime pins, all per-attempt hashes, historical evidence checks and telemetry reconciliation. Load telemetry is not an independently established number of explored states.

Direct scope is the 29-process diagnostic XML. No property was proved or refuted by these runs; transfer to the 51-process model still requires independent proof acceptance. Increasing only the timeout cannot remove the observed memory stop. Remaining work is independent review and an explicitly chosen next experiment, without automatic retries.
