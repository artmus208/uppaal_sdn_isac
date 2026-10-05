# User-authorized 30-minute experiment

Native version: UPPAAL 5.0.0 (rev. 714BA9DB36F49691), June 2023.
Exact diagnostic XML and accepted queries unchanged. Sequential BFS runs,
1800-second timeout per attempt, 2048-MiB sampled memory stop.

| Run | Status | Verdict | Seconds | Peak MiB |
|---|---|---|---:|---:|
| observer-erasure-116-20261005-completion-safety-02 | memory_limit | none | 971.813 | 2048.82 |
| observer-erasure-116-20261005-success-02 | memory_limit | none | 1064.141 | 2048.20 |

Results.json supplies exact result bindings, commands, execution commits,
native versions and trace inventories. Raw logs, telemetry and version probes
are preserved per run. A memory stop can occur before the time limit; it
does not prove or refute a property. Direct scope is the 29-process diagnostic
composition; full-model transfer needs independent proof acceptance.

The previous status-file write error did not recur; no repair was activated.
