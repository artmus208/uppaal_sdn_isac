# Fail-closed runner — issue #2

This deliverable addresses [issue #2](https://github.com/artmus208/uppaal_sdn_isac/issues/2)
on `codex/carwasher/2-runner-status`, based on `origin/read` commit
`11bd69bdca9a1209f820258b3732b3c865f79035`. Owner: `carwasher`.
Dependencies: none for this software reliability fix. Independent review is pending.
Atomic IDs: N/A — coordination-only. No scientific gate or reviewer requirement is closed.

The runner now rejects nonzero process exits and explicit error diagnostics before
combining query verdicts. It requires one result per submitted query, preserves
reported formula indices, and rejects missing, duplicate, extra, or inconsistent
results. Raw stdout/stderr and parsed partial results remain available. ANSI output,
complete negative and inconclusive verdicts, and headerless output retain support.
Diagnostic matching distinguishes errors from paths, trace identifiers, and warnings.

Only `src/uppaal_mcp/verifyta.py`, `tests/test_verifyta_parser.py`, and this evidence
directory change. The active baseline is read-only `reviewer-r1-candidate`, still
unfrozen; its hash is recorded in the metadata.

## Final diagnostic evidence

[Run d metadata](run-20260907-d/metadata.json) records the tested source byte hashes,
base commit, Python environment, package versions, and outcomes. The code was tested
before commit; the metadata explicitly identifies a worktree snapshot by its hashes.
[Exact commands](run-20260907-d/checks.json) link every command to raw stdout/stderr.
The scoped `.gitattributes` preserves the captured evidence bytes in Git.

| Check | Result | Log |
| --- | --- | --- |
| Focused runner/parser tests | 22 tests, no failures or skips; exit 0 | [stderr](run-20260907-d/focused-tests.stderr.txt) |
| Full suite | 92 tests, no failures or skips; exit 0 | [stderr](run-20260907-d/full-tests.stderr.txt) |
| Coordination check | exit 0 | [stdout](run-20260907-d/coordination.stdout.txt) |
| MCP construction | `FastMCP`; exit 0 | [stdout](run-20260907-d/build-mcp.stdout.txt) |
| Example listing | exit 0 | [stdout](run-20260907-d/list-examples.stdout.txt) |
| Dependency consistency | exit 0 | [stdout](run-20260907-d/pip-check.stdout.txt) |

All seven original synthetic healthcheck cases match their expected classifications:

| Synthetic case | Expected and observed runner status |
| --- | --- |
| Complete two-query control | `satisfied` |
| Error after first successful query | `error` |
| Incomplete output with exit zero | `error` |
| Error text after success with exit zero | `error` |
| Error without outcomes | `error` |
| Timeout after first successful query | `timeout` |
| Missing executable | `tool_not_found` |

[Machine-readable synthetic results](run-20260907-d/synthetic_runner_results.json)
retain each mocked subprocess input and full runner response. These statuses are
software test observations. No model checking was performed, and these artifacts
are not verification evidence.

Additional regressions exercise duplicate/missing/extra indices, orphaned headers,
embedded queries and query files, comments, repeated identical formulas, ANSI lines,
headerless output, uncertain verdicts, error precedence over complete output, and
benign error names in paths, traces, and warnings.

## Reproduction

From a separate checkout of this branch, using Python 3.10 or newer:

```powershell
python -m venv .venv
.venv/Scripts/python.exe -B evidence/healthcheck/20260906-runner/reproduce.py --install --output-dir evidence/healthcheck/20260906-runner/reviewer-run-001
```

Use a new output directory for each attempt; the script refuses existing output
paths. The explicit `mcp>=1,<2` installation is for this independent base. Package
dependency policy is owned by issue #3; `pyproject.toml` is unchanged here.
The recorded environment is Windows 11, Python 3.14.5, MCP 1.29.1; it does not
reproduce the Ubuntu/Python 3.12 CI environment.

## Limitations and retained earlier attempts

The current query reader counts non-comment query lines; this change does not add
a multiline query grammar or support new statistical output formats. Without
formula headers, the runner can check result count but cannot independently
identify a duplicated result that replaces a missing one. Raw evidence remains
necessary when evaluating any downstream verification claim.

The default executable path still returns JSON `tool_not_found` with the existing
CLI exit zero behavior: `[WinError 2] Не удается найти указанный файл`.
[Recorded result](run-20260907-d/version-default.stdout.txt).
An explicit `D:/UPPAAL/app/bin/verifyta.exe --version` probe returns the observed
banner `UPPAAL 5.0.0 (rev. 714BA9DB36F49691), June 2023`;
[recorded result](run-20260907-d/version-explicit.stdout.txt).
These are availability probes, not model checking. CLI status and local-path fixes
are outside issue #2 and remain separate deliverables.

Earlier attempts are preserved: [run a](run-20260906-a/bootstrap-failure.txt) records
the editable-install import bootstrap issue; [run b](run-20260906-b/metadata.json)
passed the initial implementation; [run c](run-20260907-c/focused-tests.stderr.txt)
caught an overbroad error regex incorrectly rejecting a warning. Run d above is the
final corrected source snapshot and supersedes those attempts for acceptance.

MAC/SDN property reports can still display individual parsed verdicts independently
of an overall failed run. This adjacent reporting issue is outside the assigned
write scope; the runner retains partial outcomes as diagnostic information.
