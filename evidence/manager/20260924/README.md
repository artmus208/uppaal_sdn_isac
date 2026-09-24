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

`native-smoke.py <new-output-dir> <verifyta.exe>` uses native Windows Python and
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
