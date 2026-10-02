# Operational handoff — Issue #84

- Deliverable: exact approved UAV completion baseline operational selection.
- Owner: vadimnbkg. Atomic reviewer requirement: N/A — coordination-only.
- Branch: `codex/vadimnbkg/84-uav-completion-operational`; target `read`.
- Base ref: `origin/read`; base commit: `efb6d6c0d936c2c62fbf902e383a144e6b616a0a`.
- Head: canonical branch ref and PR metadata carry the exact final commit;
  owner-side `handoff/operational-publication.json` pins it without a self-referential commit field.
- Scope: new baseline manifest; collaboration-v2 new selection block only;
  unique Issue #84 evidence directory. Open-issue scope audit found no overlap.
- Dependencies: proposal PR #85 merged at the base SHA; explicit independent
  A/B/D acceptance and operational scope in Issue comment 5946722646.
- Approved patch SHA256: `00ec9a8f4755df1a3db8285d41a959bebaf8adb5da9c6831acdebe6f1b95bd9d`.
- Installed manifest SHA256: `4b4bf71f55767123cc5934074024179289fa5ad3355fa4c0e37385e8261ef98d`.
- Scientific input commit remains `61386aa358805082b705dcd00c8cbfde5fb98248`.
- Checks: exact snapshot, full proposal seal, input/source-history audit,
  generation reproduction, candidate audit/12 controls, coordination,
  historical family, 57 historical hashes, MCP/CLI smoke and full 209-unit suite.
  Actual command exit codes and stdout/stderr hashes: `check-results.json`.
- Verification evidence: N/A — no new native runs; all 11 verdicts remain open.
- Limitations: installed preparation snapshot flags are immutable and do not
  replace the authoritative independent Issue decision. Activation C is pending.
- Next: independent operational acceptance and merge into read; then prepare
  activation record with actual merge SHA/time and manifest hash. A separate
  explicit activation decision remains required. Do not close R07 or accept P3.
- Durable retrieval: canonical remote branch plus owner-side
  `handoff/operational-final.bundle`, retaining native execution source history.
- Reproduction commands and context: `README.md`. Historical inputs,
  `current.json`, manuscript and the old P4 policy are unchanged.
