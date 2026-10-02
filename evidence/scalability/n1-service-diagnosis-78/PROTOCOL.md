# Proposed distinguishing experiment — NOT AUTHORIZED / NOT EXECUTED

Issue #78. This is a concrete follow-up to the static report; #76 permission does
not apply. Approval must explicitly name this protocol and its limits. A timeout
leaves its question open. The completed diagnostic report does not depend on
approval or a positive result.

## Exact object and questions

Original full N=1 XML (50 automata), no harness, restriction, observer addition,
regeneration or XML edit:
`evidence/scalability/family-series-68/generated/n1/model.xml`, SHA256
`5234cb087e5274798926d516dedc77d1f9542ea7df59cec39f83859771ce1385`.
Baseline `uav-family-r1-20260929`, manifest SHA256
`5480bef5b00020735259f10eb43bdd9bc79ebc364a3bbcacad34c78fd0552cbf`.
Query bytes/hashes and exact argument arrays: [protocol.json](protocol.json).

Three one-query invocations, once each, in this order:

1. `d1-kpi-consumed.q`: `E<> u0_mac_A_SCH_0.SelectMode`.
   Separates successful tick/KPI ordering from the missing-notification/fallback
   explanation. A positive verdict proves only this intermediate state. A complete
   negative verdict blocks the downstream service path, because every assignment
   selecting COMM/JOINT passes through SelectMode.
2. `d2-service-ready.q`: `E<> (shared_load.Sample_1 && u0_mac_queue_q > 0 && u0_mac_queue_q <= u0_mac_queue_K && (u0_mac_scheduleMode == u0_mac_SCH_COMM || u0_mac_scheduleMode == u0_mac_SCH_JOINT))`.
   Combines healthy backlog, service-compatible mode and the actual pre-arbitration
   committed location. A positive verdict localizes the remaining question to
   the internal service transition; separate witnesses for q and mode would not.
3. `d3-useful-grant.q`: `E<> (shared_load.Publish_0 && family_grant_0 && !u0_mac_queue_overflow_seen)`.
   Observes the immediate post-update state after an abstract service subtraction
   outside the absorbing overflow branch. It does not prove packet delivery,
   a net occupancy decrease (simultaneous arrival is possible), ACK, fairness or SLA.

Do not rerun known queue-arrival/queue-full controls or the original service query.
The saved controls already establish arrivals and multiple epochs. Search order
is breadth-first (`-o 0`) to inspect short prefixes instead of repeating the two
previous DFS orders. Large branching can still exhaust the budget; BFS is not a
promised remedy. Fixed seed 78 is recorded, not tuned. Settings remain symbolic
exhaustive exploration 0, compact representation 1, `-S 1`, `-n 0`; `-t 0` asks
for a diagnostic trace, not a shortest/fastest optimal trace.

## Commands, host and accounting

Proposed Windows host, read-only measurement in
[checks/host-proposal.json](checks/host-proposal.json): Windows 10 build 19045,
Intel Core i5-8300H, 8 logical CPUs, 17,033,019,392 bytes native RAM. This differs
from #70/#76 Ryzen host. Do not pool costs. Snapshot available RAM is not a
prelaunch guarantee.

Executable: `C:\Program Files (x86)\UPPAAL-5.0.0\bin\verifyta.exe`.
Binary SHA256: `4c8af2716ff61f3cf35c6d1dc408ccf306d44bb22478e104548a8f0f7a3febe5`.
No verifier version probe was run for #78. Capture actual `--version` and `--help`
after approval, each at most 10 seconds; require the reported version and options
to agree with the pinned historical version before scientific execution. A
failure stops the protocol, with raw output; never substitute a version string.

For each query, resolve ROOT to the clean published checkout and OUT to the unique
`evidence/scalability/n1-service-diagnosis-78/runs/diagnostic-001/<query-id>/`.
Convert paths to Windows form with `wslpath -w`; use the verifier installation
folder as process cwd. The exact command schema is:

```text
verifyta.exe -q -s -u -o 0 --exploration 0 --state-representation 1 -S 1 -n 0 -r 78 -t 0 -f OUT/trace ROOT/evidence/scalability/family-series-68/generated/n1/model.xml ROOT/evidence/scalability/n1-service-diagnosis-78/queries/QUERY.q
```

Wrap each scientific command with the unchanged native Windows monitor
`evidence/scalability/family-series-68/monitor.ps1` (hash in protocol.json), using
its existing `-ConfigPath` interface; JSON fields are `mode=run`, executable,
arguments and Windows argument string, cwd, `compile_only=false`,
`timeout_seconds=30`, `memory_limit_bytes=2147483648`, `sample_interval_ms=50`,
and unique stdout/stderr/samples/result paths under OUT. Invoke:

```text
powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File ROOT/evidence/scalability/family-series-68/monitor.ps1 -ConfigPath OUT/run.config.json
```

One child at a time. Scientific search limit **30 seconds per query**; sampled
stop at **2 GiB**, not a hard allocation cap. Fresh native probe before every
launch must show **at least 3 GiB available RAM**. Total **300 seconds wall time**
from first executable control/metadata action to final cleanup, including host
probes, harmless monitor controls, metadata, search, output drain and cleanup.
At least 65 seconds must remain before any scientific launch (30 search, 20
wrapper watchdog, 10 cleanup, 5 accounting); reserve does not enlarge the cap.
At most three scientific runs, no repeats, no seeds/strategy sweeps, no automatic
resumption. Normal/timeout/memory harmless child controls and cleanup checks are
required before scientific launch. Reuse the existing monitor implementation;
prepare and test the scoped execution driver before launching any scientific cell.
No compile/load rerun is required; parsing occurs in each exact scientific command.

Before launching: publish a clean execution checkpoint, bind its exact commit,
query hashes and approved protocol, check XML/manifest/binary/monitor hashes,
capture environment without credentials, remove inherited UPPAAL feature flags,
and ensure durable output/checkpoint transport. Any change to the approved model,
queries, strategy, limits, host or stop policy requires a new decision.

## Stop and interpretation rules

Stop globally on a successful negative verdict for D1 or D2 (downstream necessary
condition absent). A negative D2 excludes D3 only: the added q<=K restriction
does not rule out the original grant query through absorbing q=5. Also stop on missing/extra verdict on apparent success, parser/license/tool
error, hash drift, monitor/accounting failure, output-storage failure, insufficient
RAM, or exhausted total budget. Preserve cells not started and exact reason.
Timeout/memory-censored D1 or D2 has **no verdict**; the next independent query
may proceed only within the same approved cap and fresh resource checks. Stop
normally after D3. Do not infer falsity from censoring.

Every invocation retains run_id, execution status, exact source/model/query/
generator hashes, parameter and instance-vector refs, actual tool version,
command/env/cwd, native OS/CPU/RAM/probe time, UTC times, runtime, sampled private
bytes/working set/overshoot/gaps, explicit per-query result, raw stdout/stderr and
trace paths/hashes. Extract state counts from raw logs when present; otherwise
use `not_available`. Trace parsing or a manual schedule is not a new verdict.
A positive D3 requires a saved explicit machine result and a trace audit of the
original full model; no modified-model transfer is involved. Author acceptance
and R03/R04/C06 closure remain outside this protocol.
