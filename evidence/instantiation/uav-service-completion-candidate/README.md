# Request-correlated UAV completion candidate (#82)

APP completion now means receipt of its admitted request's actual PHY sample,
after queue insertion, eligible MAC service and attempted lossy transmission.
The result must satisfy stored strict UAV quality, sample age <5 and relative
request age <=40. Absolute time 40, termination, grants and command ACKs cannot
complete it. See [contract.md](contract.md) for assumptions and failure outcomes.

This separately identified candidate retains all 50 original N=1 automata and
adds one result job. It is prepared for independent P1/P2 review; no new Gate 1
decision or production integration has occurred. R02/R05/R06 remain supporting
requirements; R07 remains owned by #80.

## Result and its limits

`simulate-006` selected 100 real UPPAAL transitions through the full 51-process
composition. `replay-001` independently accepted the exported 101 states, full
locations/integer vectors, edge selections and consistent reachable DBMs.
The terminal APP location is Completed, all correlated IDs are 1, stored
Pd/false-alarm/miss/accuracy/coverage classes are 0, and outcome is success.
At actual receipt, global time is 15, request age is exactly 14 and sample
age is [4,5). The sample event occurred in (10,11]; clock differences are from
one consistent replay zone, not separately selected times. See
[completion-record.json](completion-record.json) and [replay-steps.csv](replay-steps.csv).

| Causal milestone | Replay state | Selected engine edges |
| --- | ---: | --- |
| APP service_request emission, relative clock reset | 4 | `16:2;26:0` |
| Matching accepted admission | 62 | `26:23;16:3` |
| Actual PHY measurement and sample-age reset | 84 | `3:25;50:2` |
| Result insertion into shared queue | 85 | `50:4;21:5` |
| Eligible MAC queue service dispatches the token | 96 | `21:1`, server selector 0 |
| Transmission attempt | 99 | `50:6` |
| Matching fresh APP receipt and completion | 100 | `50:7;16:12` |

The healthy path needs no PHY-command ACK: it uses the original eligible
COMM/JOINT service guard. ACK is retained as a separate command protocol.
The current global KPI can already be stale while this stored sample is fresh.

Both replay controls reject at state 100 after accepting 99 transitions:
wrong final received sample ID yields `discrete_state_mismatch`; requiring
measurement_age=0 yields `clock_zone_disjoint`. The model is unchanged.
`simulate-005` also reached real receipt with sample age exactly 5 and APP
correctly chose ServiceFailed. Its search exhausted the branch cap, so its
run status remains error rather than a positive goal claim.

This establishes one feasible healthy causal path. No exhaustive query has
been executed; success, completion safety, fairness, loss/timeout/cancel
reachability, deadline equality and global deadlock claims remain open.
All eleven queries and their hashes are in [inventory.json](inventory.json),
and every run has query_hash=null and property_verdict=null. Static guard
regressions are not model checking. No historical verification is transferred.

## Native campaign and failed cells

Run IDs have prefix `uav-completion-82-20261002-`. All nine native cells are
retained in [results.json](results.json), with exact per-cell source/model/tool
hashes, commands, environment, hardware, timing, memory samples and cleanup.
Protocol amendments record each specific diagnosed correction before launch;
no identical strategy retry or old-campaign budget transfer occurred.

| Cell | Actual status | Diagnostic/result |
| --- | --- | --- |
| simulate-001 | error | Java XML loader rejected location/transition order; 0 transitions |
| simulate-002 | error | Nested clock/boolean constraint rejected; 0 transitions |
| simulate-003 | schedule_exhausted | 35 transitions; incorrectly rewritten selector waypoint |
| simulate-004 | schedule_exhausted | 64 transitions; inherited idle KPI timer resets missing from selector |
| simulate-005 | error | 100-transition stale receipt diagnostic, followed by branch-cap exhaustion |
| simulate-006 | goal_reached | Healthy full causal path, 100 transitions |
| replay-001 | replay_complete | Independent replay, 100 transitions/101 states |
| negative-discrete-001 | rejected | Expected wrong-ID rejection at state 100 |
| negative-clock-001 | rejected | Expected disjoint-zone rejection at state 100 |

Total measured native wrapper wall time is 76.3003998 s of the fixed 600 s
aggregate cap. Each launch checked fresh available RAM >=3 GiB. Java heap was
512 MiB, owned-tree sampled stop 2 GiB, native watchdog 60 s, and all owned
process trees were reaped. The memory stop is sampled, not a hard allocation
limit. Actual monitor gaps are retained. Engine.getVersion recorded UPPAAL
5.0.0 (rev. 714BA9DB36F49691), June 2023; raw version strings remain per run.
See [PROTOCOL.md](PROTOCOL.md) and runs/*/provenance.json rather than inferred
tool versions. The nine-cell budget is exhausted; further native work requires
a separately recorded protocol and new unique run IDs.

## Reproduction and artifact storage

From the repository root, standard-library checks invoke no native engine:

```bash
python3 -B evidence/instantiation/uav-service-completion-candidate/generate.py --check
python3 -B -m unittest discover -s evidence/instantiation/uav-service-completion-candidate -p 'test_*.py' -v
python3 -B evidence/instantiation/uav-service-completion-candidate/audit.py
```

The transformer hash-checks the historical N=1 input
`evidence/scalability/family-series-68/generated/n1/model.xml` (SHA256
5234cb087e5274798926d516dedc77d1f9542ea7df59cec39f83859771ce1385).
Candidate XML SHA256 is
b8ab50e112b71491f8242789cc7906497baf8440c473d7a5a4d5214840187e02.
Generation inputs, parameters, instance order, changed interfaces and all
changed template edges are inventoried in parameters.json, instance-vector.json,
inventory.json and changes.json. Historical baseline manifest SHA256 is
5480bef5b00020735259f10eb43bdd9bc79ebc364a3bbcacad34c78fd0552cbf.

`raw-traces.zip` preserves byte-for-byte all XTRs, dense JSONL states, native
stdout and earlier model variants under their original relative paths.
`raw-index.json` records every member's size/SHA256. Extract into fresh scratch:

```bash
python3 -m zipfile -e evidence/instantiation/uav-service-completion-candidate/raw-traces.zip /tmp/c82-raw-review-new
```

`source-snapshots.zip` holds exact source blobs and raw Git commit objects for
every native source checkpoint, including the pinned read-only replay helper.
`source-index.json` maps each run to those objects. The audit checks commit
identity, all source/raw hashes, deterministic outputs, per-cell budget/cleanup,
every replay discrete state, causal order and receipt constraints. Source
checkpoint history is also retained in the owner-accessible full Git bundle
described in HANDOFF.md. `artifacts-sha256.json` seals the final tracked package.
`summarize.py` derives the review tables; `package_evidence.py --pack` refuses
to overwrite existing immutable archives. Do not regenerate historical runs.

## Validation

Scoped regression: 12 tests passed, covering the emitted guard against an
independent strict oracle, 243 quality tuples, correlation/defaults/duplicates,
missing stages, grant without receipt, failures/cancel, clock reset ownership,
freshness 5/10 and deadline 40 boundaries, queue updates, original templates
and failure exits. Full repository suite: 209 tests passed; coordination,
MCP construction, CLI examples and actual verifier version checks passed.
Commands, exit codes and raw logs are in checks/validation.json and checks/.

The first sandbox full-suite run had one MCP stdio startup timeout; the
targeted six startup tests and full suite passed outside the sandbox. The
first version command incorrectly used system Python and failed import; the
corrected sandbox invocation failed with WSL interop socket error, then the
same correct command outside sandbox returned the actual version, exit 0.
All three logs are retained. Offline Java XML load still reports inherited
duplicate auto edge-ID warnings; native execution/replay used ordered edge
indices and succeeded. These observations are not hidden or called query
verdicts. Candidate acceptance belongs to the independent reviewer.
