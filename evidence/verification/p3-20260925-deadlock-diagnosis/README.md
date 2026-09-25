# Bounded diagnosis of the native deadlock-search failure

Existing Issue #39 / C01, owner vadimnbkg, PR #56 to `read`. User instructed
«работать». This continuation adds evidence only; it does not accept C01/P3.
Base `read`: 66c0f1f706993170ff3165c77188fe00eb1e700b. Branch:
`codex/vadimnbkg/39-deadlock-search`. All three controls executed sequentially
from clean published source 0a5dca04cfe37f5d7dae533c43ef6c49deca2fd5.

## Findings

The prior error did **not reproduce in these three 60-second controls**.
Every control ended with `status=timeout`, `verdict=null`, empty stderr and
no trace. This establishes neither a repair nor deadlock freedom.

All run IDs below have prefix `p3-20260925-deadlock-diag-` and suffix
`-01-C01-deadlock`. Complete IDs and records are in `comparison.json`.

| ID middle | Search | State representation | Runtime seconds | Peak working set bytes | Result |
| --- | --- | --- | ---: | ---: | --- |
| 001 | Random DFS (2) | Exact DBM (0) | 60.0599937 | 263421952 | timeout/null |
| 002 | Random DFS (2) | Compact DBM (1) | 60.044329999999995 | 204857344 | timeout/null |
| 003 | DFS (1) | Exact DBM (0) | 60.0588203 | 184070144 | timeout/null |

All use seed 20260925, some trace (`-t 0`), 60 seconds, and the existing
sampled 2 GiB working-set stop. Random DFS explicitly selects symbolic
exploration 0; deterministic DFS uses its default symbolic mode, as documented in the saved tool help. Both representations are exact; no approximate search.
001 repeats the original search options with a shorter limit and fresh
output paths. 002 changes representation; 003 changes order and omits the
redundant exploration option. These are single observations, not a statistical
reliability or performance comparison. Fixed seed did not make the observed
process failure reproducible; its reason remains unknown.

## Original Windows failure

`windows-event.json` projects relevant fields from Application event 1000
at 2026-09-25T09:55:38.9170381Z. EventData ProcessId `0x168c` = 5772 matches
the native PID of `p3-20260925-deadlock-001-01-C01-deadlock`; its timestamp
falls within that run. Faulting application/module: `verifyta.exe`;
exception `c0000005`; module offset `00000000003a72dc`.
Computer/account identifiers and unrelated events are omitted from the
projection. The application event records a fault location, not a stack trace.

Microsoft documents [0xC0000005 as an access violation](https://learn.microsoft.com/en-us/shows/inside/c0000005).
The event and exit code cannot distinguish invalid read/write/execute or
identify the triggering model transition. There is no exception context,
call stack or crash dump in this package. No particular model construct,
search setting or library is established as the root cause.

## Identity and reproduction

Original full frozen formula: `A[] not deadlock`.

- Model SHA256: `592678ed678ce8f70cf278f542e48bd2bb739969b53a962423d3e63f91e3e1e2`.
- Individual query SHA256: `a53c752ecabf84d28dc0ea1567c0589ffb632777a5ad7178f70be0d2d99e5334`.
- Tool: UPPAAL 5.0.0 (rev. 714BA9DB36F49691), June 2023.
- Frozen baseline: reviewer-r1-gate1-20260923. Each raw baseline audit matches
  all 57 file hashes and both aggregates.

Each result supplies complete run_id/status/model_hash/query_hash/tool_version,
exact native command, limits, PID, timestamps, memory and log paths. Per-run
`run.json`/`run.yaml` retain actual hardware, environment, parameters, instance
vector and tool version output. Archives are under `../runs/`; corresponding
metadata and archive hashes under `../p3-20260923/<run-id>/`.

Commands executed from the clean source above (fresh run IDs required to rerun):

```sh
python3 evidence/verification/p3-20260923/run.py \
  --run-id p3-20260925-deadlock-diag-001 --search-order 2 \
  --state-representation 0 --seed 20260925 --trace-kind 0 \
  --ids C01-deadlock --timeout-seconds 60 \
  --verifyta /mnt/d/UPPAAL/app/bin/verifyta.exe
```

002 uses `--search-order 2 --state-representation 1`; 003 uses
`--search-order 1 --state-representation 0`. Raw directories were moved intact
outside the clone between controls so each started from the same clean commit,
then restored for packaging and moved back to `/tmp/<run-id>-raw`.

Audit without another verifier run:

```sh
python3 evidence/verification/p3-20260925-deadlock-diagnosis/audit.py
```

The audit independently extracts each archive, checks raw hashes, metadata
copies, native results/commands, fixed inputs and the planned option matrix.
Application/runner code did not change in this continuation. The 193-test
result at the execution source remains in the preceding report; full local
suite was not repeated for evidence-only additions. See `checks.txt`.

## Disposition

The bounded diagnosis is complete; original error and all three timeouts remain
inconclusive. No automatic longer repeat, tool upgrade, frozen-model edit,
new Issue or gate acceptance. PR #56 remains for evidence review. A further
native-failure investigation needs a captured exception context/stack if the
failure recurs; current observations do not supply one. The remaining C01
obligation is a justified global deadlock conclusion, not merely a process
that runs until timeout. Previously accepted attempts/protocol and scoped C02
arguments are unchanged.
