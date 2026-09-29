# Recovery and publication — 2026-09-29

Issue: #76. Owner/runner: vadimnbkg; reviewer/integrator: artmus208.
Deliverable: the completed bounded three-repeat verifier-cost report in
`../RESULTS.md`, with immutable campaign-001 and campaign-002 records.
Branch: `codex/vadimnbkg/76-family-cost-series`; target: `read`.
Base ref: `origin/read`; base: `c6b07b252f7d25e4879d49b9cb32bf381e9555fb`.

The Windows checkout `D:\uppaal_mcp` remains on `read` at the base commit
with pre-existing modified model/generated/text/fixture files and untracked
handoff files. None were reset, stashed, committed or overwritten. Recovery
uses the separate clean clone `/tmp/uppaal-p4-76`.

The original full `handoff/campaign.bundle` verifies and contains
`c79008d7f6c5f81193fb77c0d7c8035973aa0604`, including the completed series.
The recovered checkpoint `bd1098c960c0c0129d42b8c920773592f7cc4e0f`
adds recovery checks. Both are descendants of the authorized execution source
`877fa69a29e1732db2b4047eebdd99591b185c77`.

A native Windows CIM process query at `2026-09-29T20:49:18.1252245Z`
returned an empty array for Python/verifyta processes. The corresponding
WSL process check found none. Native interop first failed inside the sandbox
with `UtilBindVsockAnyPort: socket failed 1`; the read-only probe outside it
succeeded. No runner, control or verifier was launched during recovery.

Campaign-001 retains one generation error and 116 not-started cells.
Campaign-002 is completed: three generations, 12 compile, 12 load and
90 scientific attempts (18 success, 72 timeout). The exact common verifier
invocation budget, including prior metadata and monitor/termination overhead,
is `4984.3867605700125` seconds. Generation, host probes and Git checkpoint
time are separately scoped as described in the runner/report, not silently
added to scientific query times. No retry or additional budget is needed.

Recovery checks: evidence audit exit 0; 10 runner/evidence tests passed;
all entries in `artifact-hashes.json` match; report regeneration leaves the
Git tree unchanged; coordination and family historical-pin audits exit 0.
Previously retained full-suite evidence records 209 tests passed outside
the sandbox, and the earlier sandbox MCP timeout remains preserved.
All 1573 paths changed from base at bd1098c are within Issue write scope.
Raw logs/traces and prior error records remain byte-identical.

Publication is now successful. A normal fast-forward Git push using the
installed Windows credential helper published bd1098c to
`https://github.com/artmus208/uppaal_sdn_isac.git`; a subsequent `ls-remote`
returned the same full SHA. The local tree is
`7f79926b5231fa6f3380f0e75365eb4ce653ed7e`.
The earlier authentication/publication blocks recorded in `recovery.json`
and `publication-status.json` are historical, not current blockers.

This document's subsequent checkpoint is also to be published to that branch;
the PR records its exact final HEAD. The original bundle is retained untouched.
Next step: independent review/acceptance of the PR to read. R03/R04/C06,
service reachability and gate decisions are not automatically closed.
