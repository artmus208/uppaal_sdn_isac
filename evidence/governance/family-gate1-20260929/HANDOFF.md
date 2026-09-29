# Handoff — Issue #72

Deliverable: P0 proposal for a family Gate 1 decision, exact input pins and
query-evidence dispositions. Owner/account-id: vadimnbkg. Independent
reviewer/integrator: artmus208 / user-integrator. Atomic IDs: N/A — coordination-only.

- Branch: `codex/vadimnbkg/72-family-gate-proposal`.
- Base ref: `origin/read`; base commit: `52c5c8d94122f5fbd2a7b689fd9e764583de3226`.
- Final published HEAD: recorded in Issue #72 / PR after publication.
- Target: `read`. Final working tree clean after publication; no model checking run.
- Write scope: `evidence/governance/family-gate1-20260929/**` only.
- Inputs: selected current plan/contract/historical baseline, #68 candidate,
  #70 diagnostics and their separate user/Integrator acceptance decisions.

Completed: proposal distinguishes the accepted historical Gate 1 from the
proposed finite-family baseline; four model/generator/parameter/vector sets and
30 exact P4 queries are pinned. All 36 existing scientific attempts are indexed
without changing raw records or inferring verdicts. The Russian draft separates
family freeze, optional claim narrowing, manifest activation and P4 execution.
P1/P2 applicability to this family requires an explicit independent decision.
All new acceptance/authorization flags remain false.

Checks: deterministic proposal regeneration, 107 exact input hashes against the
accepted base, 30-query/36-attempt coverage and eight rejected negative controls.
Full repository tests, coordination and MCP/CLI smokes: see checks/validation.json
and logs. These checks are static validation, not new model checking.

Read-only reproduction:

```sh
python3 -B evidence/governance/family-gate1-20260929/build_packet.py --self-test
```

No manifests, source, model/query bytes, earlier evidence or manuscript changed.
No Gate 1, claim narrowing or P4 execution was accepted by the author.

Durable transport: canonical published branch and full owner-accessible bundle
`/mnt/d/uppaal_mcp/evidence/governance/family-gate1-20260929/handoff/final.bundle`.
Earlier source/proposal checkpoints are retained in the same directory.
Direct HTTPS push is unavailable in this environment; GitHub Git-data publication
is checked against the local Git tree and fetched back before handoff.

Next: independent review of this proposal and explicit A/B decisions in
DECISION-DRAFT.md. If accepted, assign manifest-specific activation scope and
resolve P1/P2 applicability; then record the actual new Gate 1. Future P4 still
requires its own Issue and execution authorization. No automatic new attempts.
