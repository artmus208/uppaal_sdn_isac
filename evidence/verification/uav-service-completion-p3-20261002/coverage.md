# C01–C05 coverage/gap index

Actual outcomes: all 11 timeout/null; no property was established by this series.
No requirement is automatically closed by publishing this campaign.

| ID | Accepted input/evidence relationship | Remaining gap |
|---|---|---|
| C01 deadlock | deadlock.q is full-composition A[] not deadlock; consult its recorded status/verdict. | Only status=success with explicit verdict resolves this query; timeout/memory/error remains open. |
| C01 queue bounds | No accepted query explicitly asserts all queue bounds. Enqueue existential input only exercises one event. | Machine queue-bound obligation remains uncovered. K=4 assumption/static typing is not a proof. |
| C01 recovery-attempt bounds | No accepted formula checks all recovery-attempt counters. | Structural recovery-attempt obligation remains uncovered. |
| C02 bounded response | success/deadline-equality are existential; completion-safety is conditional terminal safety. | No universal bounded-response formula with trigger/end/reset and progress assumptions is present. Requires separate accepted query/disposition. |
| C03 model checking | results.json indexes all 11 statuses; only per-query success and explicit verdict is direct machine evidence. | Inconclusive/unexecuted queries stay open; exact model only N=1, 51 processes. |
| C04 diagnostic evidence | Raw traces/stdout/stderr/telemetry listed and hashed in results.json; trace command is -t 0 -X. | A trace establishes only its own query/run. Absent trace remains visible; no inferred counterexample from timeout. |
| C05 provenance | Per-run source commits, full commands/flags, exact model/query/tool/executable hashes, vector/parameters and native measurements. | Unavailable metrics remain null. Sampled WorkingSet is not hard allocation accounting. Independent audit/review required. |

admitted/measurement/enqueue/attempt/success/loss/timeout/cancel are separate
existential non-vacuity or outcome diagnostics. A successful witness is no
universal service promise. deadline-equality diagnoses a possible successful
receipt at request age=40; it does not eliminate the permitted timeout alternative.
completion-safety can be vacuous if Completed is unreachable: consult success.
A[] not deadlock is neither time divergence nor fairness nor eventual completion.
Three structural obligations and bounded response are not replaced by a count of
11 query files. New formulas require separate disposition. C06 depends on P4;
R07/P5 #80 and manuscript remain outside this deliverable.
