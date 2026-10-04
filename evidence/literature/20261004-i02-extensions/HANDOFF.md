# P6 / I02 handoff — Issue #95

- Issue: <https://github.com/artmus208/uppaal_sdn_isac/issues/95>.
- Deliverable: quantitative-extension literature supplement, two new BibTeX
  entries, English replacement paragraph and an offline provenance/citation audit.
- Owner: `vadimnbkg`; independent reviewer remains to be appointed by Integrator
  `artmus208`. No author acceptance of I02 or scientific gate is asserted.
- Base ref: `origin/read`.
- Exact base: `f0fcd770e3e6b93f99868b9116e4f0929f60d0fa`.
- Branch: `codex/vadimnbkg/95-i02-extensions`.
- Literature/checker checkpoint: `2c03ea7bd85c37c151a25254fea07b6ee2281de8`.
  The subsequent packaging commit adds these handoff/check records; its exact
  HEAD is recorded in the PR. Use the published branch and verify `git rev-parse
  HEAD` against the PR before continuing.
- Durable remote: `git@github.com:artmus208/uppaal_sdn_isac.git`.
- Target: `read`. Write scope: `evidence/literature/20261004-i02-extensions/**`.
- Dependencies: P0 candidate already merged; [v2 activation
  #64](https://github.com/artmus208/uppaal_sdn_isac/issues/64#issuecomment-5878071165).
  The prior literature notes are in merged PR #94. No #89 result is required.

## Reviewable output

Read README.md for the source/claim table, application inferences and insertion
anchor. sources.json records inspected versions and support locations.
references.bib adds only `behrmann_priced_2001` and
`kwiatkowska_digital_clocks_2006`; reuse `uppaal_smc_2015` from the existing
integration bibliography. proposed-text.tex is a non-standalone prose snippet.

The supplement distinguishes symbolic universal checks, minimum-cost paths,
probabilistic bounds over schedulers and statistical estimates. It identifies
the strict-freshness and synchronization obligations for a future translation.
It supplies no new verifier or simulation evidence, model edits or manuscript
build. P9a/P9b decide whether to incorporate the paragraph and rebuild the
current manuscript; the packaged and root TeX revisions differ at this base.

## Reproduction

From a clean checkout of the published branch, use Python 3.10+ and a private
virtual environment. This check used Windows 10, Python 3.11.3, MCP 1.30.0,
PyYAML 6.0.3 and bibtexparser 1.4.4. Installation was:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -e . PyYAML 'bibtexparser<2'
$env:PYTHONUTF8='1'
$env:PYTHONDONTWRITEBYTECODE='1'
.venv\Scripts\python.exe -B evidence/literature/20261004-i02-extensions/check.py
.venv\Scripts\python.exe -B scripts/check_coordination.py
.venv\Scripts\python.exe -B scripts/check_coordination.py --audit-hashes --commit HEAD --output "$env:TEMP/i02-baseline-audit-new.json"
.venv\Scripts\python.exe -B -m unittest discover -s tests -v
.venv\Scripts\python.exe -B -c "from uppaal_mcp.server import build_mcp; print(type(build_mcp()).__name__)"
.venv\Scripts\python.exe -B -m uppaal_mcp.cli list-examples
git diff --check f0fcd770e3e6b93f99868b9116e4f0929f60d0fa...HEAD
git diff --name-only f0fcd770e3e6b93f99868b9116e4f0929f60d0fa...HEAD
```

Use a nonexistent output path for the baseline audit; never overwrite a prior
record. The checker prints JSON and does not overwrite committed artifacts.
It compares the local inputs with exact base Git blobs. A changed input is a
reason to review/rebase this supplement, not to silently update a pinned hash.

## Check records

- `checks/artifact-audit.json`: citations resolve, new keys are unique, 13 local
  inputs match the base, and four strict-freshness guards exist. SHA256 values
  cover the five delivered source files. This is a static check.
- `checks/baseline-audit.json`: 57 baseline file hashes, zero file or aggregate
  mismatches, using exact Git blobs at the literature checkpoint.
- `checks/commands.json`: exact executed commands, package/environment versions
  and exit codes; per-command stdout/stderr are adjacent.
- Software-check records use LF line endings. `checks/newline-normalization.json`
  records original captured-byte and stored-file hashes; only CRLF was converted.
- Full software suite: **209 tests in 86.679 seconds; 203 successful, 3 failures,
  1 error, 2 skipped; exit 1**. The skipped cases are POSIX-only lock/symlink
  checks. See `checks/unittest.stderr.txt` for the complete output.
- The same three failures and one error reproduce on exact base files exported
  into a separate temporary directory: `checks/base-targeted-complete.json` and
  its stdout/stderr. They are outside this literature write scope:

  | Test | Observed failure at both revisions |
  |---|---|
  | `HashAuditTests.test_exact_bytes_and_committed_manifest` | Temporary Git fixture reports `mismatch` where the test expects `match`. |
  | `FamilyBaselineTests.test_paths_and_symlink_escape_rejected` | Windows symlink creation fails with `WinError 1314` (privilege not held). |
  | `IntegratedRecorderTests.test_windows_compile_only_forwards_flag_and_translates_paths` | Windows backslashes differ from the expected POSIX path in the mocked WSL call. |
  | `ManagerTests.test_memory_limit_measures_real_child` | Queue returns 0 where the memory-limit test expects 2. |

  The first targeted baseline export omitted `CONTRIBUTING-v2.md`; that setup
  failure is retained in `checks/base-targeted.*`. The completed export includes
  every family input pin and reproduces the original symlink error. No root-cause
  repair or platform setting change was made. Integrator triage is still needed.
- Both smoke checks pass (exit 0): `FastMCP` construction and CLI example listing.
- Artifact, coordination and baseline audits pass (exit 0). These and the smoke
  checks do not turn the full test suite into a pass.
- `git diff --check` passes and all changes remain in the declared scope.

The initial sandboxed dependency installation stalled while fetching build
dependencies and was interrupted. Retrying with network permission into the
same private `.venv` succeeded. No system Python packages were changed.

## Remaining step

Independent source/wording review, appointment of the reviewer, and a P9a/P9b
integration decision remain. These checks cannot decide scientific acceptance,
prove model behavior, validate stochastic input data or verify final typesetting.
The ongoing #89 work, #91 figures and #92 manuscript ownership remain separate.
