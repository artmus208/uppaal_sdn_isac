# MAC queue capacity implementation — #43 / PR #44

The integrated candidate now records finite MAC queue occupancy instead of
independently sampling its class. The approved abstract tuple is
`K=4, L=1, M=2, H=4`; these are work units, not physical calibration.
The source implementation is at `a7f7fd0cf3fc8ddb365fa2e16f998a43543b68d7`,
based on `79f59d8b9d59375371bae6f5521e7d2619fcb2a0` (`read`).
Owner/runner: `vadimnbkg`. Independent acceptance remains pending.

## Behavior and limits

At each existing MAC load tick, optional service of old work precedes an
optional arrival. Service is available only in COMM/JOINT modes and is never
guaranteed. Queue classes derive from occupancy. ACK, QueueDraining and
resource rejection do not dequeue. No new clocks, packet objects, admission
policy or retry policy are introduced.

`q=K+1` is an absorbing overflow witness and sets a sticky flag. The transition
from a full queue to overflow remains enabled. Exact occupancy after overflow,
throughput and drain time are outside this abstraction. This deliberately
changes environment semantics; it is not a passive recorder or an equivalence
claim. Other sampled fields, tick offers/loss and recovery semantics remain.

## Recorded validation and diagnostics

New run: `queue-20260922-resume-20260923-001`, executed on 2026-09-23 from
the clean source commit above. All 19 recorded commands exited 0.
The software suite ran 175 tests with no failures or skips; coordination,
MCP construction, examples, dependency consistency and whitespace checks
also completed with exit 0.

UPPAAL: `5.0.0 (rev. 714BA9DB36F49691), June 2023`, actual version stdout
included. The 34 expected query verdicts comprise 33 focused queue diagnostics
and one full-composition `E<> true` engine-load check. In the fill/full-arrival
cases the capacity property is **NOT satisfied**, as intended; counterexamples
are saved. The deliberately clipped-at-K mutant loses overflow reachability.
Full-composition queue capacity, deadlock and bounded response were not checked.
No C01/P1/P2/Gate 1 acceptance or P3/P4 result is claimed.

Each entry in [results-index.json](results-index.json) records its own `run_id`,
`status`, exact `model_hash`, `query_hash`, `tool_version`, command, timestamp,
duration, query verdicts and log paths. `status=success` means the diagnostic
executed and matched its expectations, which include negative safety verdicts.
[run.json](run.json) records the clean commit, parameters, instance vector,
generator/source hashes, operating environment, CPU and RAM. Resource usage
and explored states not emitted by this runner are marked `not_available`.
[composition.json](composition.json) pins the full generated configuration.

## Integrity and reproduction

The lossless archive specified by [publication.json](publication.json) contains
all 83 original files: XML, queries, stdout/stderr, traces, command records and
SHA256SUMS. The four JSON summaries alongside this README are exact copies from
that archive. Every archived byte was compared with its original before
publication; no logs were edited. To audit without executing the verifier:

```sh
python3 evidence/instantiation/20260922-queue-implementation/audit.py
```

To inspect raw artifacts, extract into a fresh temporary directory:

```sh
mkdir /tmp/queue43-evidence-inspect
tar -xJf evidence/instantiation/20260922-queue-implementation/runs/queue-20260922-resume-20260923-001.tar.xz -C /tmp/queue43-evidence-inspect
```

To reproduce, use a clean checkout and isolated environment per CONTRIBUTING,
then run with a unique ID and an available licensed executable:

```sh
python -B evidence/instantiation/20260922-queue-implementation/check.py --run-id queue-REVIEW-NEW --verifyta /path/to/verifyta
```

The saved execution used WSL with `/mnt/d/UPPAAL/app/bin/verifyta.exe` through
Windows interop, outside the sandbox. Exact command arrays and per-command
limits are in [commands.json](commands.json). `.venv` dependencies are captured
in `dependencies.txt`. Extraction/audit does not require UPPAAL or a license.

## Continuation provenance and remaining work

The prior machine's final bundle (`92ce4fce...`, historical run
`queue-20260922-001`) was not available here. This package is a new execution
of the published source, not a restoration or validation of those unavailable
historical artifacts. It supplies independently inspectable evidence for #43.
Publication uses the existing `codex/vadimnbkg/43-mac-queue-capacity` branch and
PR #44 to `read`; source files were not changed during continuation.

Next: independent review and merge of #44. Recovery-attempt recording remains
a separate deliverable; #36 remains deferred. Gate 1 still requires final P1/P2
acceptance and a separately reviewed manifest freeze.
