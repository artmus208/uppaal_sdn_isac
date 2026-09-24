# Verification manager software evidence — Issue #51

Owner vadimnbkg. Base read / a0679c24c4ea11aa7ef12b392c45c2d63df84340.
Branch codex/vadimnbkg/51-verification-manager, target read. Production manager
source checkpoint be6dc22f62e8195bc99177f65c34d2567b34821f is published.
This is software tooling evidence, not closure of any scientific reviewer ID.
Frozen model/manifests and #39 artifacts are unchanged.

Commands (from isolated checkout, Linux Python):

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -m unittest discover -s tests -p test_verification_manager.py -v
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -m unittest discover -s tests -v
```

Windows tests use native Python 3.13.2 with checkout/src on sys.path and the same
unittest file. The separate-process control test sets PYTHONPATH for its child.
Tests use a fake verifier subprocess with real allocations/delays, so measured
limits and process lifecycle are exercised rather than mocked implementation.
Only the unavailable-metric failure test deliberately mocks metrics.

`native-smoke.py <new-output-dir> <verifyta.exe> <manager-source-commit>` uses native Windows Python and
actual UPPAAL on a tiny one-clock fixture. One invariant property and one negative
property exercise genuine verdict parsing, traces, telemetry and continuation.
The model is a software fixture, not the frozen research baseline. Per-attempt
hashes, tool version, command and raw logs are retained under native-001/.
The exact manager source commit and smoke script hash are recorded separately.

Known limits: native process suspension/checkpointing and GUI deferred by scope;
pause is between formulas. Sampling is not a hard allocation cap. Forced manager
termination may leave a child alive; known live orphan PIDs block continuation,
and users must inspect processes after a hard crash. See user documentation.
Expected preflight time is up to 20 seconds; control is polled after preflight.

Next: independent code review and merge decision. The author does not accept
this result. Local clean/dirty status and final published HEAD are in PR handoff.

## Final checks and interpretation

Final manager/test source: published bdcab48a149c4e13c8e7f748bf57877cb53deac9.
Linux full suite: 193 tests OK, 44.555 seconds. Windows native suite: 13 discovered,
12 pass and one deliberately skipped POSIX flock failure-injection test, 12.178s.
The same unsupported-lock regression executes and passes on Linux. Raw test logs
are included. Initial focused suite (before lock correction): 12 pass.

Native-001 failed before starting verifyta: Windows OS byte-range locking is not
supported by the WSL UNC filesystem on this host. Raw failure and initialized
queue are preserved; they contain no verification claim. Final manager rejects
UNC queue storage and distinguishes unsupported locking from an active worker.

Native-002 ran on the local Windows temp drive with Python 3.13.2 and actual
UPPAAL 5.0.0 (rev. 714BA9DB36F49691), June 2023. Both formulas completed with
expected positive/negative verdicts; memory peaks 17043456 and 17170432 bytes.
Exact run IDs, hashes, full version and timings are in native-002/smoke.json and
attempt result.json files. Continuation created no new attempts and preserved
existing attempt bytes. It is software smoke, not a research-baseline result.

The copied snapshot preserves all original absolute runtime paths; create a new
queue to reproduce, rather than trying to run this archived Windows queue at a
different path. `python -B evidence/manager/20260924/audit.py` verifies raw hashes,
model/query identities, actual version, verdicts and memory samples.

Baseline audit: 57 file hashes and both aggregates match, no baseline changes.
Default whitespace checking flags CRLF native output and generated verifier trace
formatting. Raw output is preserved for hash integrity. Code/docs check excludes
only evidence logs/native snapshots. Test log hash-mismatch fixture messages are
expected test output, not failures of the actual baseline audit.

Native smoke reproduction on the tested host (PowerShell; fresh output folder):

```powershell
& 'C:\Users\musta\AppData\Local\Programs\Python\Python313\python.exe' `
  evidence\manager\20260924\native-smoke.py `
  "$env:TEMP\uppaal-manager-new-smoke" `
  'C:\Program Files (x86)\UPPAAL-5.0.0\bin\verifyta.exe' `
  bdcab48a149c4e13c8e7f748bf57877cb53deac9
```

Do not reinterpret this smoke as a completed C02 or a 24-hour run: neither was
started by this tooling task. Implementation and use guide:
[verification-manager.md](../../../../docs/verification-manager.md).
