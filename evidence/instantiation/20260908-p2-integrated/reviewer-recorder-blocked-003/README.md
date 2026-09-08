# Issue #19: recorder regression harness blocker

Continuation date: 2026-09-08. Owner/account-id: `carwasher`.
Branch: `codex/carwasher/19-integrated-evidence`.
Starting HEAD: `3f70d714f8c697599295619bc51d89f98547a6d1`.
Base: `dc7eeb05f1fd3f2a4775428b1cd250363893128d` (`origin/read`).
GitHub Issue #19 remained open/claimed by carwasher; PRs #18 and #16 were
confirmed merged through GitHub before editing. The isolated clone was clean.

## Changes attempted

- `checks.py`: use `args.python.absolute()` in place of `.resolve()` to preserve
  the supplied virtual-environment executable symlink.
- `tests/test_sdn_layer.py`: add `IntegratedRecorderTests`, constructing a fresh
  symlinked venv and probing the selected interpreter/adjacent CLI's `sys.prefix`.
  Recorder child checks are replaced by probes; Git output is mocked.

These changes are **unvalidated**, not a completed recorder fix. The regression
harness failed before it could demonstrate the intended behavior.

## Executed check and failure

Working directory: `/tmp/uppaal-carwasher-19-evidence-20260908`.

```sh
.venv/bin/python -B -m unittest discover -s tests -p test_sdn_layer.py -k IntegratedRecorderTests -v
```

Exit code: 1. One test, one error, no skips. The exact console text returned by
the execution tool is transcribed in `console.txt`; stdout/stderr were not
captured separately by this attempted command. This is not a recorder bundle.

The test patches the shared `subprocess.check_output` module attribute with only
two Git responses. `platform.platform()` calls `platform.uname()`, whose lazy
processor lookup also invokes `subprocess.check_output`. That third call exhausts
the mock side effect and raises `StopIteration`. This is a newly introduced test
harness error, not a model defect or a recurrence of the historical nine imports.

The shell's subsequent `git diff --check`, staging and intended fix commit were
joined with `&&` and did not execute after the failed test. The later diagnostic
handoff commit preserves the attempted patch without claiming that it passes.

## Stop and next action

The user-selected continuation prompt explicitly says to stop and record a
blocker for a new test error. Work stopped at that condition. Permission is
needed to repair the test harness (isolate the Git mock from platform discovery),
then finish validating the executable-path behavior before any final evidence
run. No integrated source/model semantics were changed in this continuation.

The requested verifyta executable was observed as an existing file at
`/mnt/c/Program Files (x86)/UPPAAL-5.0.0/bin/verifyta.exe`. It was not invoked;
version, execution availability, license and compile diagnostics remain unknown.
No final `reviewer-run-003` bundle or audit was produced and no PR was opened.
The historical `reviewer-run-002` directory was preserved byte-for-byte.

Remaining work after authorization: correct and validate the regression harness;
commit the validated recorder/test changes; record focused/full software checks,
generation, real verifier diagnostics and static audit in a fresh directory;
update the final evidence index; submit a scoped draft PR to `read`.
Scientific P1/P2 acceptance, baseline supersession and Gate 1 remain pending.
