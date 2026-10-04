# Handoff: MAC/SDN report status correction (#96)

- Issue: https://github.com/artmus208/uppaal_sdn_isac/issues/96
- Deliverable: truthful property/violation reports for unsuccessful MAC/SDN runs.
- Process: P0 software reliability; IDs: N/A, coordination-only.
- Owner: vadimnbkg; Integrator: artmus208; independent review pending.
- Base: `origin/read`, `f0fcd770e3e6b93f99868b9116e4f0929f60d0fa`.
- Branch: `codex/vadimnbkg/96-mac-sdn-report-status`; PR target: `read`.
- Implementation checkpoint: `44a19d102df401ccb0012a6ab481982f12558322`.
- Tested source commit: `286ca62e13793172329893c7fef26c5cbc18c4a4`.
  Later changes are confined to this evidence directory. The exact tested code
  hashes, commands, environment and log hashes are in [checks.json](checks.json).
- Retrieve from the canonical remote branch. The PR records the final HEAD and
  clean working-tree status after the evidence checkpoint.

## Result

Both public report generators now gate property results on the existing runner's
complete-run statuses and show the overall execution status. An aborted run with
partial positive or negative output yields `not_verified`. The output remains
available as explicitly labelled diagnostics. Uncertain query outcomes are
separated from actual violations, and empty results cannot imply no violations.
Raw result data, public function signatures, bundle structure and CSV columns
are preserved. Supplying an empty result dictionary now also produces an explicit
`violations.md` explaining that no verdict was established.

## Validation

Python 3.11.3, native Windows 10, MCP 1.30.0, PyYAML 6.0.3.

| Check | Result |
|---|---|
| Regression before correction | 9 tests, 38 failing subtests; exit 1 |
| Regression after correction | 9 tests passed across both MAC and SDN; exit 0 |
| Full native Windows suite | 218 tests: 210 passed, 3 failures, 3 errors, 2 skips; exit 1 |
| Same six problematic tests on exact base checkout | Same 3 failures and 3 errors; exit 1 |
| Coordination | exit 0 |
| Frozen baseline hash audit | 57 file hashes, zero file/aggregate mismatches; exit 0 |
| pip check, FastMCP construction, CLI example listing | exit 0 each |
| Diff whitespace check | exit 0 after diagnostic-log normalization |

The full-suite failures are not hidden or repaired outside scope:

1. Two `test_coordination_activation` cases use CP1251 to decode UTF-8 Git
   content and raise `UnicodeDecodeError`.
2. `test_family_baseline` cannot create a symlink: Windows error 1314.
3. `test_coordination.HashAuditTests.test_exact_bytes_and_committed_manifest`
   reports a fixture hash mismatch (the separate actual baseline audit passes).
4. `test_sdn_layer` expects POSIX `/tmp/...` separators from a Windows `Path`.
5. `test_verification_manager` expects the memory limit to stop a real child,
   but gets exit 0 instead of 2 on this host.

Two pre-existing POSIX-specific tests skip on Windows. The six failures/errors
were reproduced in an isolated checkout of the exact base commit; see
[baseline-windows-failures.txt](baseline-windows-failures.txt). No failing source
or test was changed. The initial sandboxed dependency installation stalled and
was interrupted; a bounded installation with network access succeeded, recorded
in [install.txt](install.txt).

## Reproduction and remaining work

Install the project and PyYAML in an isolated environment, then run the focused
command from README, `python -m unittest discover -s tests -v`,
`python scripts/check_coordination.py`, and the hash audit command from
`checks.json` with a fresh output filename. Run `python -m pip check`, construct
`build_mcp()`, and run `python -m uppaal_mcp.cli list-examples`.

Review only these allowed paths:

- `src/uppaal_mcp/mac/reports.py`
- `src/uppaal_mcp/sdn/reports.py`
- `tests/test_mac_sdn_report_status.py`
- `evidence/healthcheck/20261004-mac-sdn-reports/**`

Next: inspect PR CI and obtain independent software review. The reporting status
contract deliberately uses this repository's runner outcomes, not an invented
`success` alias. No native verifier probe or model-checking campaign was needed
or executed. No scientific requirement or gate is accepted by this handoff.
Dependencies: merged runner/parser; activated v2 decision in Issue #64,
issuecomment-5878071165. No dependencies on the active #89 or #95 workstreams.
