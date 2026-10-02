# Engine-directed replay of the manual N=1 service trace (Issue #78)

The actual UPPAAL engine accepted all 68 transitions (69 saved states) of the
manual service-before-overflow XTR against the unchanged full N=1 baseline:
50 processes, 255 integers and 70 clocks. At the last transition queue=1 becomes
queue=0, family_grant_0=1, scheduleMode=JOINT (3), and overflow_seen remains 0.
The reachable final DBM has #time exactly 10: internal upper bound 21 (<=10)
and lower bound -19 (<=-10). APP service_request_pending remains 1; this is
not evidence of APP completion or SLA satisfaction.

| run_id suffix (prefix n1-service-78-replay-001-) | Engine outcome | Accepted transitions | Native seconds | Sampled tree peak bytes |
|---|---|---:|---:|---:|
| replay | replay_complete | 68 | 7.8550762 | 834637824 |
| negative-discrete | rejected: discrete_state_mismatch at state 68 | 67 | 7.6436788 | 830955520 |
| negative-clock | rejected: clock_zone_disjoint at state 68 | 67 | 7.7941471 | 824565760 |

The negative controls change the expected final grant or require shared_load.tick=1
where the service transition resets it to 0. Both are rejected by successor/zone
matching, rather than accepted merely because a saved state exists.

## Scientific meaning

This is directed symbolic simulation from the engine's genuine initial state.
Every saved edge, integer/location vector and clock zone is checked against
successors from the reachable restricted prefix. The feasible intersection is
carried forward; no saved discrete state is imported as a fresh initial state.
It establishes a feasible service path under this semantics. It is neither an
exhaustive search nor a fresh verifyta verdict for `E<> family_grant_0`.
`property_verdict` is deliberately null. The earlier D1/D2/D3 timeouts and their
cause remain unresolved. Acceptance of R03/R04/C06 remains with the reviewer.

## Provenance and limits

- Executed source commit: 3e927608fde7cfe0b0363105ca29412d7d5c4363.
- Input checkpoint: b403fd3903b1d9f925cb51382ba5433810612f99.
- Original scientific base: 8237e8c2bec41aa1bb943cc33be1ac9586d03759.
- Model SHA256: 5234cb087e5274798926d516dedc77d1f9542ea7df59cec39f83859771ce1385.
- Input XTR SHA256: 8186e1b68324ba288abe6249abdc73fa771400d95414d4bf77d2d1f9fdfbfcf7.
- Related historical query SHA256: 5aeca4a4152577404ee725b1b2c2c697bdb02803c291742ce01c73b9a0d6c789 (not executed here).
- Actual engine response: UPPAAL version 5.0.0 (rev. 714BA9DB36F49691), June 2023; the full server response is preserved in every result.json.

Commands, binary/source hashes, Java/OS/CPU/RAM details, stdout/stderr,
process identities, sampled process-tree memory and termination evidence are
in native-002/provenance.json and each cell's monitor/hardware/CSV files.
All owned children were reaped. Bound: 60 seconds/cell, 2 GiB sampled tree,
300 seconds accumulated native execution. Actual accumulated native cost was
29.063496 seconds, including 2.2721119 seconds of a failed readiness attempt.
This sum excludes the development pause between campaigns; it is not one
continuous elapsed wall interval. Memory sampling cannot capture every transient.

native-001 retains the initial UNC model-loader failure (zero transitions),
its actual version probe and cleanup. The loader was fixed and offline-tested
before native-002; no further engine run was made. Loader warnings about duplicate
auto-generated edge IDs are retained verbatim in stderr; input model bytes were
not edited. Transition ordering and the compiled successor graph are checked
by the replay itself.

## Reproduction

Read-only audit (Python standard library, no UPPAAL):

```bash
PYTHONDONTWRITEBYTECODE=1 python evidence/scalability/n1-service-diagnosis-78/replay-001/inspect_replay.py
PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s evidence/scalability/n1-service-diagnosis-78/replay-001 -p 'test_*.py' -v
```

The audit checks the independent child-package inventory, lossless archives,
executed source/input hashes, all accepted prefix records, endpoints, negative
controls, native termination and budget accounting. It does not rerun the engine
and cannot replace independent engine reproduction. Historical parent audit
results describe their pinned checkpoints, not this added child package.

For a new engine experiment, use a separate clone, Windows UPPAAL 5.0.0 and
JDK 17, and a newly agreed run ID/output directory. run_replay.py records exact
native commands and refuses to overwrite the retained native-002 evidence.
The fixed protocol is in PROTOCOL.md. Do not delete evidence to force a rerun.

Dense reachable XTRs are archived with xz, and step logs with gzip, losslessly.
lossless-archive.json retains original uncompressed sizes and SHA256 values.
Decompress with Python lzma/gzip (or xz/gzip) to inspect/import the engine-derived
restricted prefixes. These files are generated witnesses, not the original
manual XTR. The original manual file remains unchanged.

## Validation

209 repository tests passed outside sandbox, plus 4 child-package corruption
checks and Java offline DBM/XTR/model-load controls. Coordination, family baseline
with historical pins, MCP build, CLI list-examples and pip check exited 0.
The first sandboxed suite had one MCP stdio initialization timeout; its original
logs are retained. The isolated MCP test (6 tests) and full suite then passed
in the same unsandboxed environment. No production fix or extra engine replay
was performed. Exact commands, exits and raw logs are under checks/.
