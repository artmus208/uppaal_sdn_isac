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

Check logs and the final handoff are stored beside this file.
