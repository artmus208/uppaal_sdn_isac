# Coordination fixture portability — #99

Issue: <https://github.com/artmus208/uppaal_sdn_isac/issues/99>.
Process: P0 software reliability; atomic IDs: N/A — coordination-only.
Owner: vadimnbkg. Integrator: artmus208. Independent reviewer: unassigned.

The native Windows suite failed because the hash-audit fixture inherited
`core.autocrlf=true` during `git add`, and activation tests decoded UTF-8 documents
using the system `cp1251` locale. The fixture now sets its own `core.autocrlf=false`
before staging. Both test modules explicitly read/write UTF-8. Assertions check
the committed LF/CRLF bytes and ensure each migration mutation changes its input,
including the Cyrillic conditional-ownership label. Existing rejection checks,
the production checker, frozen inputs and model generation are unchanged.

## Revisions and scope

- Base ref: `origin/read`.
- Exact base: `f0fcd770e3e6b93f99868b9116e4f0929f60d0fa`.
- Branch: `codex/vadimnbkg/99-coordination-portability`; PR target: `read`.
- Implementation checkpoint: `4073325888c60185d1b857f6f9daf20574116a6f`.
- Final packaging HEAD and publication status are recorded in the linked Issue/PR.
- Write scope: `tests/test_coordination.py`, `tests/test_coordination_activation.py`
  and `evidence/healthcheck/20261004-coordination-portability/**`.
- Dependencies: merged coordination code and
  [v2 activation](https://github.com/artmus208/uppaal_sdn_isac/issues/64#issuecomment-5878071165).
  This task does not consume pending work in #89, #95 or #96.
- Baseline: `manifests/baselines/reviewer-r1.yaml`,
  `reviewer-r1-gate1-20260923`, SHA256
  `d542e617148169361b96126d55bba91079fe5c8ac3cfe6d67e27755fae3a46f7`.
  Current plan/contract and checker hashes are in `comparison.json`.

## Results

Native Windows 10, Python 3.11.3, MCP 1.30.0, PyYAML 6.0.3.
Child processes used `PYTHONUTF8=0`; `child-locale.log` records `cp1251` and UTF-8
mode disabled. User/system Git configuration was not changed. Temporary global
config files isolate the three matrix settings; their contents are recorded.

| Check | Before | After |
|---|---|---|
| Focused, native Git settings | 13 tests, 1 failure + 2 errors | 13 passed |
| Focused, inherited autocrlf=false | 13 tests, 2 errors | 13 passed |
| Focused, inherited autocrlf=true | 13 tests, 1 failure + 2 errors | 13 passed |
| Focused, inherited autocrlf=input | 13 tests, 1 failure + 2 errors | 13 passed |
| Full suite | 209 tests: 201 passed, 3 failures, 3 errors, 2 skipped | 209 tests: 204 passed, 2 failures, 1 error, 2 skipped |
| Structural coordination | exit 0 | exit 0 |
| Committed baseline audit | 57 hashes, zero file/aggregate mismatches | same |
| FastMCP construction / CLI examples / pip check | exit 0 each | exit 0 each |

The remaining three failures are identical to failures recorded before the fix:

1. `test_family_baseline.FamilyBaselineTests.test_paths_and_symlink_escape_rejected`:
   Windows symlink creation lacks privilege (`WinError 1314`).
2. `test_sdn_layer.IntegratedRecorderTests.test_windows_compile_only_forwards_flag_and_translates_paths`:
   mocked WSL invocation expects POSIX separators on a Windows `Path`.
3. `test_verification_manager.ManagerTests.test_memory_limit_measures_real_child`:
   expected queue exit 2, observed 0.

They are outside this Issue's scope. The two existing skips remain visible in
the full logs. No full-suite pass or POSIX execution is claimed.
No licensed verifier, version probe, simulation or model checking was run.

## Reproduce

From the repository root, using a fresh output path:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -e . PyYAML
.venv\Scripts\python.exe -B evidence/healthcheck/20261004-coordination-portability/run_checks.py --output .venv/coordination-review --full
git diff --check f0fcd770e3e6b93f99868b9116e4f0929f60d0fa...HEAD
```

The runner records every command, environment override, exit code, duration and
raw combined stdout/stderr hash. It exits nonzero if any software check fails;
thus the saved before and after runs both return 1 because of the full suite.
Omit `--full` for the focused matrix only. Git commands reporting an absent
configuration value are diagnostic and do not determine the runner exit code.
Native non-UTF-8 Windows is required to reproduce the original locale failure;
setting `PYTHONUTF8=0` alone does not create that locale on a UTF-8 POSIX host.

`before/checks.json` pins test bytes equal to the exact base. The after run began
before its implementation checkpoint completed: its recorded starting HEAD is
therefore the earlier harness commit. `comparison.json` independently matches
the tested SHA256 values against the exact committed test blobs at `4073325`,
checks all saved log hashes, and lists removed/remaining failure IDs. No test
source changed while that run was executing. Later changes only package evidence.

Raw logs retain their original CRLF bytes through scoped Git attributes; the
`cr-at-eol` whitespace attribute permits their original line endings in diff
checks. This does not disable whitespace checks for source files. Baseline
audits read committed blobs, so checkout newline conversion cannot fake a match.

## Next step

Publish the branch and open a PR to `read` once publication is permitted, then
have an independent maintainer review the two test changes and reproduce the
matrix. Exact source/log hashes and unchanged scientific inputs can be checked
without a licensed verifier. The author does not accept this PR or any gate.
