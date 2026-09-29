# Handoff — Issue #70

- Deliverable: fixed ten-query service reachability diagnostic on unchanged #69 inputs.
- Owner / account-id: vadimnbkg; independent reviewer/integrator: artmus208 / user-integrator.
- Branch: `codex/vadimnbkg/70-service-reachability`.
- Assigned base ref: `codex/vadimnbkg/68-family-series`.
- Base commit: `a51a77e7852aee514bb0217a17d970fcf94cb704`.
- Scientific source HEAD: `ecf08b52dadce0d5413307775f6b1d36cd13fabb`, published and clean at launch.
- Exact final artifact HEAD is recorded in Issue #70 after publication; a commit cannot embed its own SHA.
- Scope: `evidence/scalability/service-reachability-20260929/**` only.
- Final working tree: clean after evidence/report commit; runtime caches ignored.

## Outcome

All ten queries were attempted once and timed out with no verdict or witness.
Total recorded verifier/metadata wall time: 322.12842336000006 s / 420 s.
Largest native observed peak: 1,058,213,888 bytes / 2 GiB.
The 30 s timeout threshold excludes about 2 s of recorded shutdown/cleanup;
actual end-to-end times are retained per invocation. No limits were increased.
Read RESULTS.md, checks/audit.json and runs/service-002/runs.json for each exact
run_id/status/model_hash/query_hash/tool_version and raw evidence.

The metadata-only stop in service-001 is preserved. No scientific query was
launched there. Its successful version output was reused without another
--version call. Short metadata memory is explicitly unavailable; scientific
monitoring remains mandatory. Monitor normal/timeout/memory controls passed.
The controls' prepublication source e36ce14940a72d21cb5792a3dc8a9ba7b4ca1744 is
retained in the full checkpoint bundles; scientific source is publicly available.

## Checks and reproduction

```sh
python3 -B evidence/scalability/service-reachability-20260929/runner.py pins
python3 -B evidence/scalability/service-reachability-20260929/audit.py --self-test
```

These are read-only audits, not new UPPAAL runs. The audit checks ten records,
82 pinned input hashes and four rejected evidence mutations. Full repository
unit tests, coordination and MCP/CLI smoke commands/results are retained in
checks/validation.json and their raw logs. Scope comparison uses the assigned
base commit above; historical/model/query files have no changes.

## Durable transport and next step

Canonical published branch in `artmus208/uppaal_sdn_isac` is the primary transport.
Direct HTTPS git push has no credentials in this environment; GitHub Git-data
publication is checked against the exact local Git tree and fetched back.
Owner-accessible full history bundles are under:
`/mnt/d/uppaal_mcp/evidence/scalability/service-reachability-20260929/handoff/`.
The final complete bundle is `final.bundle`; earlier source, controls, stopped
preflight and running-campaign checkpoints remain available there.

PR #69 is still open. A PR from this branch to `read` would currently include
its 400 inherited dependency files outside #70's scope. Therefore do not open
that PR until #69 is merged; no out-of-scope replacement or merge is performed.
Issue #70 carries the exact final branch/HEAD and ready handoff meanwhile.

Next: independent review of this diagnostic, merge/accept the parent candidate
as appropriate, then open the scope-clean #70 PR to read. The unresolved service
nonvacuity needs a separately justified witness task or an explicit Integrator
claim-scope disposition before corresponding P4 claims. Gate 1, full P4, old P3
transfer and R03/R04/C06 closure are not claimed. No automatic further attempts.
