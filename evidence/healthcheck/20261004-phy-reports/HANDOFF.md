# PHY reports after unsuccessful verification — Issue #105

Owner: `vadimnbkg`; Integrator: `artmus208`; independent reviewer unassigned.
Process P0, atomic IDs N/A — coordination-only. No scientific acceptance claimed.
Issue: <https://github.com/artmus208/uppaal_sdn_isac/issues/105>.

Branch `codex/vadimnbkg/105-phy-report-status`, target `read`, base ref `origin/read`.
Exact base: `f0fcd770e3e6b93f99868b9116e4f0929f60d0fa`.
Implementation checkpoint: `805e4dc5c23cf2f24beb64b139afe1249429600f`.
Final published HEAD, clean worktree and remote equality are reported in the PR.
The branch is published to the canonical GitHub remote; final evidence is packaged
in a subsequent commit without further implementation changes.

## Behavior

A failed run containing a parsed `satisfied` formula previously put `satisfied`
in both the PHY property table and `properties.csv`. A timeout with only positive
partial output also produced `no failed parsed query` in `violations.md`.

Property Markdown and CSV now share these rules:

| Input | Property cell |
| --- | --- |
| No result object supplied | `not_run` |
| Error, timeout, static-only, missing/unknown overall status | `not_verified` |
| Completed runner status (`satisfied`, `not_satisfied`, `inconclusive`) | Explicit recognized query outcome |
| Completed run, missing query | `not_run` |
| Completed run, unknown query outcome | `not_verified` |

Overall status appears in the property report. Violations separate explicit
negative results from unresolved formulas; unsuccessful-run output is a labelled
diagnostic table without property-fix suggestions. Empty supplied results now
get a violations report explaining that no verdict was established. Positive
absence statements apply only to returned results.

Public signatures, CSV columns and the exported original results JSON/trace are
preserved. This uses the existing VerifytaRunner status contract; it does not
authenticate arbitrary result dictionaries or independently verify their provenance.

## Scope and dependencies

Only `src/uppaal_mcp/phy/reports.py`, new `tests/test_phy_report_status.py`, and this
evidence directory change. #96/#98 owns MAC/SDN reports; #104 owns the PHY cache
and usage guide. Neither pending change is required here. #89/#90, generators,
models, manuscript, existing tests and manifests remain unchanged.

Current pointer/plan/contract, CONTRIBUTING guides, baseline and
[v2 activation #64](https://github.com/artmus208/uppaal_sdn_isac/issues/64#issuecomment-5878071165)
were checked. Dependencies are the already merged runner and reporting API.
No scientific gate is changed by this software task.

## Checks

Native Windows, Python 3.11.3, UTF-8 mode, MCP 1.30.0, PyYAML 6.0.3:

- `before/`: 10 new tests produce 24 failing assertions/subtests against the exact
  base reporting code. `focused-after/` and `after/`: all 10 tests pass. They cover
  both report formats, no/empty/unknown/static-only results, positive/negative/
  uncertain outcomes, actual runner behavior with mocked subprocess output and
  export preservation. No verifier executable is invoked by these regressions.
- Full suite: **219 tests, 213 passed, 3 failures, 1 error, 2 skips**, exit 1;
  70.940 seconds of unittest execution. The four failures are the base Git fixture,
  Windows symlink privilege, emulated WSL path separator and manager memory-limit
  assertion. The same failures were reproduced on exact base files in
  [#95 evidence](https://github.com/artmus208/uppaal_sdn_isac/blob/e9567c667c7f8c05d90ae4c990fe466e0df66803/evidence/literature/20261004-i02-extensions/checks/base-targeted-complete.stderr.txt).
  Their test files and the manager are byte-identical to the base (see audit).
  Fixes #99/#100 are separate, pending PRs; no full Windows-suite pass is claimed.
- Coordination, 57 baseline file hashes and both aggregates, `pip check`, FastMCP
  construction and CLI examples: exit 0. Scope/source/log audit and whitespace
  checks pass. Licensed verifier execution and model checking are not required.

`checks.json` records exact commands, environment, starting HEAD, source hashes,
exit codes, durations and log hashes. Log CRLF is normalized to LF with original
and stored hashes retained. Scoped `.gitattributes` preserves unittest's trailing
spaces in captured text logs; normal source/doc checks remain enabled.

The first implementation commit attempt stopped on those captured trailing
spaces. The full batch had already started before the commit was retried, so its
starting HEAD is the test checkpoint. `audit.py` binds every tested source hash
to the exact implementation blobs above and proves those bytes remain unchanged.
The baseline audit itself ran after that implementation commit. Subsequent edits
only package this handoff, audit and logs.

## Reproduce

Install the project and PyYAML in a worktree-local virtual environment, then run:

```powershell
.venv\Scripts\python.exe evidence/healthcheck/20261004-phy-reports/run_checks.py --output .venv/phy-report-review --full
.venv\Scripts\python.exe evidence/healthcheck/20261004-phy-reports/audit.py
```

The output directory must be new. Omit `--full` for only the focused regressions.
The runner preserves failed checks and continues through the independent smokes.
All results here are software/static evidence, not model-checking verdicts.

Next: independent software review and integration decision. CI status and its
exact published HEAD are recorded in the PR/Issue after GitHub completes the run.
