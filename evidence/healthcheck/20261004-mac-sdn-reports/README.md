# MAC/SDN report status correction (#96)

Software regression evidence only; no UPPAAL model checking is performed.

Base: `read` / `f0fcd770e3e6b93f99868b9116e4f0929f60d0fa`.
Branch: `codex/vadimnbkg/96-mac-sdn-report-status`.
Owner: `vadimnbkg`; independent review pending.

Both report generators previously copied per-query results into property tables
without checking the overall run status. A failed run with a partial `satisfied`
line could consequently display a positive verdict. The violations report could
also display "No failed query was parsed" for a failed run with no results.

The regression suite exercises both public report generators and exporters,
including a real parser/summary path with synthetic aborted-run output. Raw
results remain available as diagnostics. No production model, frozen input,
manuscript or verifier process is changed by this task.

Reproduce the focused check after installing the project:

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests -p test_mac_sdn_report_status.py -v
```

Check logs and [HANDOFF.md](HANDOFF.md) are stored beside this file. Diagnostic
text logs use LF and may have trailing whitespace removed; they are software
test transcripts, not native verifier evidence.

Reporting semantics:

- No result supplied: `not_run`.
- Result supplied with any status other than the runner's `satisfied`,
  `not_satisfied` or `inconclusive`: `not_verified`, with overall status visible.
- For a completed run, retain explicit `satisfied`, `not_satisfied`, `maybe` and
  `inconclusive` query outcomes. An absent query remains `not_run`; an absent or
  unsupported query status becomes `not_verified`.
- A `not_satisfied` query is a violated property. `maybe`, `inconclusive` and
  unknown query statuses are unresolved, not violations.
- Query output from an unsuccessful run is shown only under a diagnostic heading
  in `violations.md`. Exported `results.json` and CSV columns are unchanged.

These reporting functions consume the existing runner status contract. They do
not independently authenticate input JSON, revalidate the entire run, establish
provenance or accept a scientific claim. PHY reports and standalone trace
classifiers are outside this Issue's write scope.
