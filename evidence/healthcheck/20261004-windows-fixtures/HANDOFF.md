# Symlink and WSL test fixtures — Issue #100

Process P0, N/A — coordination-only. Owner: `vadimnbkg`; Integrator:
`artmus208`. Independent reviewer is unassigned; author acceptance is not claimed.
Issue: <https://github.com/artmus208/uppaal_sdn_isac/issues/100>.

Branch: `codex/vadimnbkg/100-windows-fixtures`; target: `read`.
Base ref: `origin/read`; exact base: `f0fcd770e3e6b93f99868b9116e4f0929f60d0fa`.
Exact execution checkpoints are recorded in each check JSON. The final evidence
commit is recorded in the PR, avoiding a self-referential hash. The named branch
is published to the canonical GitHub remote. Final handoff requires a clean
worktree and matching remote HEAD; those checks are reported in the PR.

## Changes and scope

- `tests/test_family_baseline.py`: separate invalid-path checks from the actual
  symlink test. Only Windows error 1314 (missing symlink privilege) skips the
  latter. All other errors still fail; real symlink rejection is exercised on Linux.
- `tests/test_sdn_layer.py`: use `PurePosixPath` for the emulated WSL input, so a
  Windows host does not supply backslashes to the POSIX path-conversion assertion.
- Evidence: this directory only. Production source and all frozen inputs remain
  unchanged. Other active workstreams, including #89/#90 and #99, do not overlap
  this final diff.

Dependencies: existing merged fixtures; v2 activation
<https://github.com/artmus208/uppaal_sdn_isac/issues/64#issuecomment-5878071165>.
Current pointer, v2 scientific plan/contract, CONTRIBUTING guides and historical
baseline were read; this task changes neither governance nor scientific gates.

## Final checks

Tested final implementation: `e226496d3724935fe89d05fa00b47794ddb8a06c`.
`final-full-suite`: **210 tests, 205 passed, 2 failures, 3 skips** on native
Windows/Python 3.11.3 (exit 1, 68.043 seconds of unittest execution).
Both changed modules have no failures: 41 passed and 2 expected skips across
their 43 cases. The third skip is the unchanged POSIX-only manager lock test.

The two remaining failures are `HashAuditTests.test_exact_bytes_and_committed_manifest`
(reserved by #99) and `ManagerTests.test_memory_limit_measures_real_child`
(separate manager issue). Both reproduce on the base; their source/test files
are byte-identical to it. They are neither suppressed nor included in this fix.

`final-linux-targeted`: **all 12 tests passed**, no skips, on Ubuntu/WSL with
Python 3.12.3, including actual symlink rejection and both recorder tests.
Final scope/log integrity audit and whitespace check pass. Review and integration
remain pending; there is no claim of an entirely passing Windows suite.

## Retained preliminary checks and scope correction

The initial issue claim also covered the Git fixture in `test_coordination.py`.
A second live Issue search discovered concurrent earlier reservation #99.
That edit was removed and the file restored byte-for-byte to the exact base;
#99 owns coordination Git/UTF-8 fixture work. The final audit checks this equality.
Earlier commits/logs are retained as historical evidence, not final-scope claims.

Initial native Windows checks, Python 3.11.3 in the worktree `.venv`:

| Check | Before | After at preliminary checkpoint 7af7984 |
| --- | --- | --- |
| Coordination module (now excluded) | 6 tests, 1 failure | 6 passed |
| Family baseline module | 9 tests, 1 error | 9 passed, 1 privilege skip |
| SDN module | 33 tests, 1 failure, 1 skip | 32 passed, 1 POSIX-only skip |

Splitting path and symlink cases increases the suite by one test; it does not
skip invalid-path assertions. At this preliminary checkpoint, the full Windows
suite had 210 tests: 206 passed, 1 failure, 3 skips (exit 1, 81.683 seconds).
The failed memory-limit test (`0 != 2`) is unchanged from the base. Git fixture
checks under temporary global `autocrlf=true/input/false` also passed at that
checkpoint; that fix belongs to #99 and is absent from the final diff.

Ubuntu/WSL, Python 3.12.3: the initial targeted run passed 18 tests, including real
symlink escape rejection and both recorder tests. An earlier broader run tried
the whole SDN module: 29 tests ran, but `IntegratedCandidateTests.setUpClass`
failed because Linux Git cannot resolve this Windows-managed worktree's
`C:/.../.git/worktrees/...` pointer. Its log is retained as `linux-fixtures`.
No Linux full-suite pass is claimed. Initial sandbox WSL enumeration returned
`Wsl/EnumerateDistros/Service/E_ACCESSDENIED`; approved execution worked.

Coordination static check, exact-commit baseline audit (57 file hashes and both
aggregates), `pip check`, MCP construction, CLI examples and real `verifyta
--version` all returned exit 0. These unaffected checks remain valid after
removing the fixture change; version output is saved, not manually supplied.
These are software/static checks, **not model-checking evidence**.

## Reproduction and evidence

Each check has `checks/<label>.json` with exact argv, cwd, source commit,
working-tree status, timestamps, duration, exit code and hashes of stdout/stderr.
Logs normalize CRLF to LF; original and stored hashes are recorded. Failed runs
are retained. `record.py` refuses reused output labels.

From the repository root (use a fresh label for every repeated check):

```powershell
.venv\Scripts\python.exe evidence/healthcheck/20261004-windows-fixtures/record.py new-full .venv\Scripts\python.exe -m unittest discover -s tests -v
.venv\Scripts\python.exe evidence/healthcheck/20261004-windows-fixtures/audit.py
```

Focused native commands use `-p test_family_baseline.py` or `-p test_sdn_layer.py`
with unittest discovery. The final Linux command is
`wsl -d Ubuntu -- env PYTHONPATH=src:tests PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_family_baseline test_sdn_layer.IntegratedRecorderTests -v`.

Next: independent review and integration decision.
The known manager memory failure remains visible for separately coordinated
follow-up under #51; the coordination fixture failure belongs to #99.
