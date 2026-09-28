# Two-size SDN/ISAC family candidate

Issue [#66](https://github.com/artmus208/uppaal_sdn_isac/issues/66), P2. N=1 has
50 automata; N=2 has 99. UAV contexts share one queue-service budget: at most
one abstract unit per MAC epoch across the network. This is a runnable candidate,
not an accepted family or a P4 resource result.

From the repository root, Python 3.10+ (no third-party modules for the prototype):

```bash
python3 -B evidence/scalability/family-feasibility-66/generate.py
python3 -B evidence/scalability/family-feasibility-66/generate.py --check
python3 -B evidence/scalability/family-feasibility-66/check.py
```

The first command writes both `generated/n1` and `generated/n2`: XML, candidate
queries, parameters, instance vectors and exact-byte hashes. Input files are
hash-pinned in `inputs.json`; changes fail closed. All outputs stay inside this
Issue's directory. The source is the committed frozen XML, so generation needs
neither the old generator's Python dependencies nor a UPPAAL license.

[CONTRACT.md](CONTRACT.md) defines routing, arbitration, state/clock ownership,
N=1 correspondence, every semantic difference and open decisions. Static tests
are not model checking. The future property files have no verdicts. Tool-load
checks only establish parser/type/initial-state acceptance, not C01/C02 or progress.

Before P4: accept the shared-server/per-UAV-controller abstraction, agree the
size domain and query schema, then freeze a new baseline through P0/Gate 1.
Optional service permits starvation; there is no packet/interference model or
physical calibration. Frozen observer/admission limitations remain. Old P3
results do not transfer automatically; R03/R04/C06 are not closed.

Results: [checks/static.json](checks/static.json) records 160 N=1 and 12,000 N=2
allowed queue-step cases, 80 N=1 frozen-step comparisons and 11 rejected mutation
controls. These evaluate XML expressions locally; they are not model checking.
[Clean-tree reproduction](checks/clean-reproduction.json) regenerates all artifacts
from a Git archive without untracked inputs. Repository suite: 200 tests OK;
57 frozen file hashes and both aggregate hashes unchanged; smoke checks OK.

[UPPAAL evidence](checks/uppaal-published-005/runs.json) comes from published clean
source commit `a14b823de8415c6e73fd01607ce0a8343e2f2d09`, UPPAAL 5.0.0
(rev. 714BA9DB36F49691), June 2023, with a working license. Both XML compile and
both full query files parse. Only `E<> true` is executed (initial-state load);
model and query hashes, exact commands, per-run environment and raw logs are
in that record. Negative model and query controls are rejected. No scientific
property series was run. WSL-visible RAM is environment metadata, not native
Windows peak usage or a P4 measurement.

Optional reproduction of these short checks from a **clean committed tree**:

```bash
python3 -B evidence/scalability/family-feasibility-66/tool_check.py \
  --verifyta '/path/to/verifyta' --run-id reviewer-001
python3 -B evidence/scalability/family-feasibility-66/pack_logs.py
python3 -B evidence/scalability/family-feasibility-66/audit_artifacts.py
```

Use a fresh run ID. On WSL supply the `.exe` path under `/mnt/c/`; on Linux use a
licensed Linux verifyta. The artifact audit checks the published files, not newly
created reviewer runs against the original index. Each invocation has a 10-second
limit. The script checks compile-only behavior and then uses `--query-index 0`
with `E<> true` prepended, so future scientific queries are parsed but not run.

Failed attempts are retained: `uppaal-load-001` found UPPAAL's rejection of a
self-closing `<queries />`; `uppaal-load-002` hit the 10-second compile limit with
Cartesian input selection; staging inputs fixed it. `uppaal-load-003` established
that compile-only ignores external queries, which motivated the separate parser
control. Their local source commits are historical diagnostics, retained in the
owner-accessible full checkpoint bundle; authoritative final successful records
use the published source commit above. Large stdout files are lossless gzip;
`stdout_hash` hashes decompressed bytes and `stdout_storage_hash` hashes storage.

Handoff: [HANDOFF.md](HANDOFF.md). Acceptance and the new Gate 1 remain pending.
