# Owned Windows process memory — #113

Owner: vadimnbkg. Independent Reviewer/Integrator: artmus208/user-integrator.
Branch: codex/vadimnbkg/113-windows-process-memory. Target: read.
Base: 2f49676ad249fafa9fd36a245fc0340071ab623b.
Final tested source: 11877f8d95608b9a0e911db92031ab898e710823.
Published HEAD is recorded in Issue #113 and the PR. Local/publication histories
may have different commit IDs; their final trees are compared after fetch.
Complete owner-accessible bundle: /mnt/d/uppaal_mcp/113-windows-process-memory.bundle.

## Change and contract

Windows attempts now join a non-inheritable Job Object atomically at process
creation, before the suspended primary thread resumes. Only stdin/stdout/stderr
handles are inherited. KILL_ON_JOB_CLOSE is set; breakaway flags are absent.
Memory limits apply to the sampled sum of live members' WorkingSet, including
Python venv redirector descendants. Peak is the largest observed sum, not an OS
private-commit statistic or a sum of individual historical peaks. CPU uses job
accounting, including exited members. Existing metric keys remain compatible;
session hardware metadata describes the changed metric scope. Old evidence
keeps its original one-process meaning. Windows 10+ is required for JOB_LIST.

Memory/time/stop/monitor errors terminate and wait for only the owned job.
Closing the sole job handle also kills remaining members on owner exit. An
exited launcher does not hide live descendants. A leader observed to exit while
real descendants remain cannot donate its exit code to their later output:
that output is diagnostic-only, with error/null verdict absent another stop
reason. Ordinary complete positive/negative outcomes and continuation remain
supported. Native setup/monitor failures fail closed.

Two liveness races are covered independently: a lagging job ActiveProcesses
count must not classify a signaled leader as a live child, and leader exit
between consecutive liveness reads must not fabricate a descendant. Live
process handles, membership checks and ordered reads resolve both.
At terminal metric loss, <=10 ms of actual completion wait within the remaining
attempt deadline separates an exited process from an unmeasurable live one.
Only a completed process and the unchanged parser can produce a verdict.
The Linux process-tree scope is unchanged; this terminal race fix is shared.

## Reproduction

Install the project and PyYAML in a fresh environment. From a clean checkout:

```text
python evidence/healthcheck/20261004-windows-process-memory/run_checks.py --run-id review-new
```

Use native Windows Python on Windows; use Linux Python on Linux. Output must be
a new directory. --focused runs only the manager module. The recorder saves
source commit/hashes, Python/OS, commands, UTC start, durations, exit codes and
byte-preserved raw streams. It does not invoke a licensed verifier. Child
fixtures are ordinary Python programs with synthetic formula output.

Final check source hashes in linux-final-008/checks.json and
windows-final-006/checks.json must match the current implementation/test files.
Coordinator and frozen hash audit remain software/static checks. Frozen models,
queries, generators, manifests, manuscript and scientific verdicts are unchanged.

## Retained diagnostics and limitations

before/ copies the #111 unchanged-test contrast: venv memory test fails, base
Python succeeds. Its source and provenance are available at PR #112 / published
7c132eae47b82b60ba188f730ee9665dc3918350; production inputs equal this issue's base.

Earlier run directories are diagnostics, not substitutes for the final source.
Their checks.json and hashes state actual inputs. windows-final-001 retained a
150 ms test-startup/log race; only the fixture timeout became one second while
the fake child still sleeps three seconds. windows-final-002 retained a native
status.json PermissionError associated with the separate #51 work; no status
retry implementation was copied or silently claimed fixed here.
windows-final-003/004 ran on 6982198. The 004 checkout was rejected because raw
untracked logs collided with committed evidence, but the old shell continued.
windows-final-004-launch.stdout.txt preserves that error. Those results do not
validate the later handle fixes. Own logs were moved to native-retained in the
native clone, then set -e and an exact HEAD assertion preceded the final launch.

linux-terminal-metrics-diagnostic.stdout.txt saves the repeat control where an
actual exited negative-query fixture returned monitor_error/null with exit 0.
The negative-result race injection and live missing-metrics test now cover both
outcomes. Intermediate Linux full-suite failures and all successful runs remain
available. No retry was used to hide a failure; repeats follow recorded source,
fixture or provenance corrections.

Sampling can miss short memory peaks and count shared pages more than once.
The memory threshold is a sampled stop, not a hard allocation cap. An API error
prevents a verdict. No real verifier/GUI/version/help probe was executed, so no
claim about licensed verifier operation or a scientific gate is made.
Transient Windows status publication/read behavior remains a separately scoped
known issue even if the final full suite succeeds.

Write scope: verification_manager.py, windows_process.py,
tests/test_verification_manager.py, docs/verification-manager.md and this packet.
All packet bytes except artifact-hashes.json itself are hashed by that inventory.
Next: independent software review of the PR, then integration into read.

Windows final-005 retained two false detached-output failures on ordinary venv launches. Final fix allows at most 10 ms (bounded by the remaining timeout) for the entire job to complete after launcher exit before rejecting persistent descendants. This grace never extends the configured deadline. Final runs are linux-final-007 and windows-final-006; prior logs remain diagnostic.

Implementation references: https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects and https://devblogs.microsoft.com/oldnewthing/20230209-00/?p=107812/ . Atomic creation follows the established JOB_LIST approach in evidence/verification/uav-bounded-response-89/windows_native.py (unchanged).

Linux final-007 ran inside the execution sandbox: manager checks passed, but the MCP stdio integration smoke timed out (full-suite errors=1, skipped=8). linux-final-008 repeats outside that sandbox, matching the established Linux execution environment. Both runs preserve identical source hashes. Windows final-006: manager 20 passed/2 skipped; full suite 247 passed/4 skipped (251 total), exit 0.

Final acceptance evidence (software/static only): Linux final-008: manager 14 passed/8 skipped; full suite 243 passed/8 skipped (251 total), exit 0. Windows final-006: manager 20 passed/2 skipped; full suite 247 passed/4 skipped (251 total), exit 0. On both platforms coordination, frozen hash audit (57 matched inputs), pip check, dependency capture, MCP construction and CLI smoke all exit 0. Exact Python/OS/commands are in checks.json (Linux Python 3.14.4, Windows Python 3.14.5). Final working tree is clean after the packet commit; remote HEAD and tree comparison are recorded in Issue/PR.
