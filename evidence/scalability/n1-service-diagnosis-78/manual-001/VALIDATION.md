# Validation and handoff

Issue: #78, manual trace predicate comparison and timeout audit supplement.
Branch: `codex/vadimnbkg/78-manual-trace-audit`.
Parent checkpoint: `f10767d75604241d9ddc07ed9c4ff94ffd0cb2f7`.
Original Issue base: `8237e8c2bec41aa1bb943cc33be1ac9586d03759`.
No production model changes or new scientific verifier executions.

Static checks: `audit_manual.py` reproduced audit.json byte-for-byte; package
audit.py matched the updated artifact index; coordination and family baseline
checks exit 0. New paths are confined to #78 scope. Authored-file whitespace
check exit 0. Whole diff whitespace check exit 2 because the unchanged input
GUI XML retains original Windows CRLF; do not normalize evidence bytes.

Repository tests: first invocation without installed package could not import
uppaal_mcp (38 tests, 17 errors). With PYTHONPATH=src, 209 tests ran in 66.019 s,
with 2 failures and 2 errors: missing installed CLI entry point and missing mcp
SDK. Full suite is therefore NOT reported as passed. Raw logs are retained;
these environment limitations do not replace the successful scoped static audit.

Transport: full Git bundle exported into a unique directory under
`D:\uppaal_mcp\evidence\scalability\n1-service-diagnosis-78\handoff\manual-audit-20260930`.
The adjacent HANDOFF.json gives the exact final HEAD, tree status, bundle hash,
base and next step. Origin in the temporary clone is a local repository;
no claim of GitHub publication, PR update or independent acceptance is made.

Next step: review the audit and approve/reject the exact proposed-run.json
protocol before any new model-checking execution, as required by Issue #78.
The protocol is prepared but not run; a timeout would still leave no verdict.
