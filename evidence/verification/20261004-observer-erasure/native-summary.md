# Native experiment for Issue #116

Native tool: UPPAAL 5.0.0 (rev. 714BA9DB36F49691), June 2023.
Both runs use the exact 29-process diagnostic XML, BFS options `-o 0 -t 0`,
600-second time limit and 2048-MiB sampled memory stop. No retries.

| Query | Status | Verdict | Seconds | Peak MiB |
|---|---|---|---:|---:|
| completion-safety | timeout | none | 600.891 | 1424.49 |
| success | error | none | 70.844 | 284.71 |

Exact run IDs, execution commits, full commands, model/query hashes, verbatim
native version, result paths/hashes and trace inventories are in native-results.json.
Raw stdout/stderr, resource telemetry and version probes are retained under native/.

Run `observer-erasure-116-20261005-success-01` ended on a manager error, not a native property verdict.
Windows denied atomic replacement of status.json (WinError 5). A concurrent
file reader or another transient sharing/access conflict can cause this; the
specific holder was not identified. The owned native process was terminated.
No retry is allowed by this campaign. Runner repair is outside Issue #116 scope.

Only a complete explicit native verdict settles a query. Timeout or a resource
stop does not establish either the property or its negation. This experiment
does not measure speedup relative to a controlled full-model run. Direct results
apply to the diagnostic model; independent scientific acceptance of the
observer-erasure proof is still required for transfer to the 51-process input.
