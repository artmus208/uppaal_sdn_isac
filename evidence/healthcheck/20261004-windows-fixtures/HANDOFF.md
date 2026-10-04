# Windows regression fixtures — Issue #100

Process P0, N/A — coordination-only. Owner: `vadimnbkg`; Integrator:
`artmus208`. Independent reviewer is unassigned; author acceptance is not claimed.
User requested another independent task after the published #95/#97 handoff.
Issue: <https://github.com/artmus208/uppaal_sdn_isac/issues/100>.

Branch: `codex/vadimnbkg/100-windows-fixtures`; target: `read`.
Base ref: `origin/read`; exact base: `f0fcd770e3e6b93f99868b9116e4f0929f60d0fa`.
Tested implementation checkpoint: `7af79847b4bba6046b33d71f2ed83de5c41198ff`.
The final evidence commit is recorded in the PR, avoiding a self-referential hash.
The named branch is published to the canonical GitHub remote. Final handoff
requires a clean worktree and matching remote HEAD; those checks are in the PR.

## Changes and scope

- `tests/test_coordination.py`: set fixture-local `core.autocrlf=false` before
  staging. Previously a commit-only override came after CRLF bytes were normalized
  by `git add`, invalidating exact-byte audit assertions. No global config edits.
- `tests/test_family_baseline.py`: separate invalid-path checks from the actual
  symlink test. Only Windows error 1314 (missing symlink privilege) skips the
  latter. All other errors still fail; real symlink rejection is exercised on Linux.
- `tests/test_sdn_layer.py`: use `PurePosixPath` for the emulated WSL input, so a
  Windows host does not supply backslashes to the POSIX path-conversion assertion.
- Evidence: this directory only. Production source and all frozen inputs remain
  unchanged. #89/#90, #95/#97, #96 and the #51 manager/status work do not overlap.

Dependencies: existing merged fixtures; v2 activation
<https://github.com/artmus208/uppaal_sdn_isac/issues/64#issuecomment-5878071165>.
Current pointer, v2 scientific plan/contract, CONTRIBUTING guides and historical
baseline were read; this task changes neither governance nor scientific gates.

## Results

Native Windows, Python 3.11.3 in the existing worktree `.venv`:

| Check | Before | After |
| --- | --- | --- |
| Coordination module | 6 tests, 1 failure | 6 passed |
| Family baseline module | 9 tests, 1 error | 9 passed, 1 privilege skip |
| SDN module | 33 tests, 1 failure, 1 skip | 32 passed, 1 POSIX-only skip |

Splitting the path and symlink cases increases the suite by one test; it does not
skip the invalid-path assertions. Isolated global Git configurations with
`autocrlf=true`, `input`, and `false` each pass all six coordination tests.

Full Windows suite: **210 tests, 206 passed, 1 failure, 3 skips**, exit 1,
81.683 seconds of unittest execution. The remaining failure is
`test_verification_manager.ManagerTests.test_memory_limit_measures_real_child`
(`0 != 2`), already reproduced on the base during #95. The manager and its test
are byte-identical to the base (audited here). This task neither fixes nor skips
that separate issue. Two existing POSIX-only skips and one new, narrowly scoped
symlink-privilege skip account for all three skips.

Ubuntu/WSL, Python 3.12.3: **18 targeted tests passed**, including real symlink
escape rejection and both recorder tests. An initial broader run tried the whole
SDN module: 29 tests ran, but `IntegratedCandidateTests.setUpClass` failed because
Linux Git cannot resolve this Windows-managed worktree's `C:/.../.git/worktrees/...`
pointer. Its failure log is retained as `linux-fixtures`; the successful
`linux-targeted` run covers the changed tests without that unrelated generator
setup. No Linux full-suite pass is claimed. The initial sandbox WSL enumeration
returned `Wsl/EnumerateDistros/Service/E_ACCESSDENIED`; approved execution worked.

Coordination static check, exact-commit baseline audit (57 file hashes and both
aggregates), `pip check`, MCP construction, CLI examples and real `verifyta
--version` all returned exit 0. Version output is saved, not manually supplied.
These are software/static checks, **not model-checking evidence**.

## Reproduction and evidence

Every check has a `checks/<label>.json` with the exact argv, cwd, source commit,
working-tree status, timestamps, duration, exit code and hashes of its stdout and
stderr files. Logs normalize CRLF to LF; both original and stored hashes are
recorded. Failed runs are retained. `record.py` refuses reused output labels.

From the repository root (use a fresh label for every repeated check):

```powershell
.venv\Scripts\python.exe evidence/healthcheck/20261004-windows-fixtures/record.py new-full .venv\Scripts\python.exe -m unittest discover -s tests -v
.venv\Scripts\python.exe evidence/healthcheck/20261004-windows-fixtures/audit.py
```

Focused native commands use `-p test_coordination.py`, `-p test_family_baseline.py`
or `-p test_sdn_layer.py` with unittest discovery. The Linux command is
`wsl -d Ubuntu -- env PYTHONPATH=src:tests PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_coordination test_family_baseline test_sdn_layer.IntegratedRecorderTests -v`.
The global-Git matrix is fully recorded in `checks/git-defaults.json`; it points
`GIT_CONFIG_GLOBAL` at temporary files without changing the user's settings.

Next step: independent review and integration decision. The known manager memory
failure remains visible for separately coordinated follow-up under #51.
