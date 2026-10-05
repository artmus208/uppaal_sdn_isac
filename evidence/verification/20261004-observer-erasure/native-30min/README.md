# Authorized 30-minute rerun

User authorization: 2026-10-05, rerun both formulas with a 30-minute limit;
if the manager's status-file write failure recurs, repair and rerun the
affected formula with the same limit. Issue #116 records this amendment.

Exact model and accepted queries are unchanged. Each initial run uses suffix
02; a conditional repair rerun uses suffix 03 and preserves the failed run.
Timeout: 1800 seconds per formula. Sampled memory stop: 2048 MiB.
Native Windows verifier, BFS options -o 0 -t 0; sequential owned workers.
Historical native/ and its summaries remain unchanged.

Monitoring consumes worker stdout without opening hot status.json files via
PowerShell. Any necessary repair is confined to a campaign save adapter with
bounded retries for Windows sharing/access failures, fault-injection tests
and explicit source hashes. Persistent errors remain fatal and recorded.
No production manager, model, query, manuscript or manifest is changed.

Direct results apply only to the 29-process diagnostic model. Full-model
transfer remains conditional on independent acceptance of observer erasure.
