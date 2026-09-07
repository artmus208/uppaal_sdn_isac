# CLI exit-status regression evidence

Issue: [#4](https://github.com/artmus208/uppaal_sdn_isac/issues/4). Process: P0 software reliability support.
Owner account: `carwasher`. Atomic IDs: N/A — coordination-only.
Base ref: `origin/read`; base commit: `11bd69bdca9a1209f820258b3732b3c865f79035`.
Target branch: `read`; independent maintainer review and acceptance remain pending.

The CLI previously printed operational failures as JSON and exited with code 0.
Every dispatch path now returns the shared JSON result's exit code, and module
execution propagates it through `SystemExit`. The installed console script uses
the same return value. JSON payloads are preserved.

## Exit contract

| Code | Meaning |
| --- | --- |
| 0 | Successful operation; `ok`, `satisfied`, `validated`, or `success` result; matched expected negative scenario or benchmark. |
| 1 | A completed unexpected `not_satisfied` verdict or a failed `ok` check/aggregate. |
| 2 | Tool/process failure, nonzero tool return code, `static_error`, timeout, missing tool, unknown/inconclusive/partial result, or other unrecognized status. |

Nested `result`, `results`, `runs`, and `query_results` participate in this
decision. Operational failures take priority over negative verdicts and over a
positive aggregate flag. A scenario with `ok=true` and a matching expected
`not_satisfied` outcome succeeds; its nested errors still produce code 2.

Validation commands expose their check outcome through top-level `ok` or
`status`. Descriptive validation metadata is preserved without assigning a
separate exit status: negative benchmark generation intentionally includes
invalid models. Benchmark suite `ok` flags identify whether those expected
results matched. Static-only `validated` with an empty `query_results` list is
code 0 and does not mean a property was model checked. An invalid standalone
`validate` check is code 1; a property-pack `static_error` is code 2 because the
requested property-pack operation cannot proceed.

## Checks and reproduction

All 86 unit tests completed without failures or skips, including 12 new CLI test
methods that execute real child processes. Backend fixtures inside those child
processes cover positive, negative, error, timeout, missing-tool, unknown,
inconclusive, partial, nested, and failed-aggregate responses while checking that
JSON is unchanged. Real module/installed-script invocations also exercise missing
tools, example listing, static-only property packs, and expected negative static
benchmarks for PHY/MAC/SDN. No licensed verifier is executed by these new tests.

The full unit suite, coordination check, `pip check`, `build_mcp()` smoke, example
listing, and wheel build each returned 0. The installed CLI's missing-tool
`version` check returned the expected 2 and retained its JSON diagnostic.
Wheel build warnings only report disabled byte compilation, consistent with
`PYTHONDONTWRITEBYTECODE=1`.

Raw stdout/stderr, exact command arrays, environment overrides, timings, software
versions, source hashes, and artifact hashes are in
[checks-20260907T000715Z/metadata.json](checks-20260907T000715Z/metadata.json).
The [unit-test log](checks-20260907T000715Z/unit-tests.stderr.txt) records all 86
tests. The evidence directory retains the assigned Issue date; this capture ran
on 7 September UTC after the session resumed.

To reproduce from a clean checkout on Windows with Python installed:

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -e . 'mcp>=1,<2' build
.venv/Scripts/python.exe evidence/healthcheck/20260906-cli/capture_checks.py
```

The capture script creates a new timestamped directory rather than replacing
existing logs. This run used Windows 11, Python 3.14.5, and MCP 1.29.1. It does not
reproduce the Ubuntu/Python 3.12 CI environment. MCP 1.x was explicitly
constrained because SDK compatibility is handled independently in Issue #3.
Exact working-file SHA-256 values describe the tested files; Git object IDs also
identify source contents after configured Git line-ending normalization. Scoped
`.gitattributes` preserves the exact raw log and JSON bytes when committed.

## Handoff scope and limits

Deliverable: CLI exit-status implementation, child-process regression tests, and
reproducible software evidence. Write scope and changed paths:

- `src/uppaal_mcp/cli.py`
- `tests/test_cli.py`
- `evidence/healthcheck/20260906-cli/**`

Inputs: the read-only scientific plan, collaboration contract, and active
candidate baseline; their hashes are recorded in the metadata. Dependencies:
none for this isolated software fix. Required gate: normal PR review. No
scientific gate or downstream workstream is declared accepted or unblocked.
Verification evidence: N/A; synthetic verdict fixtures and software checks are
not model-checking evidence. No manuscript, model, generator, runner, SDK
dependency, or manifest source is changed here. Runner result completeness and
SDK compatibility remain the responsibility of Issues #2 and #3 respectively.
