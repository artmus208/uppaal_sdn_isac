# P2: preserve unrestricted diagnostics and identify provenance/scope blockers

Prepared draft body only; do not open until Integrator resolves the inherited
out-of-scope diff. Published `6604af0` rejects its pinned AGENTS.md before model
generation. Outside sandbox, MCP initializes and real verifyta version/help work;
the current full suite still fails on that source-pin mismatch.

- Issue: #19 (keep open); Process: P2; IDs R01/R02/R05/R06.
- Deliverable: integrated single-UAV software/static evidence and review handoff.
- Owner: artmus208, explicit user-authorized handoff recorded in #19.
- Branch: `codex/artmus208/19-native-evidence-handoff`; target: `read`.
- Base ref/commit: origin/read / `dc7eeb05f1fd3f2a4775428b1cd250363893128d`.
- Current read: `426cf570138231765b21d518f9d20289e2b11b63`.
- Tested head: `6604af040b16c9c3c0e6ceb78b7f52df7172f185`.
- Handoff head: exact published SHA in the final #19 handoff comment; obtain
  with `git rev-parse origin/codex/artmus208/19-native-evidence-handoff`.
- Write scope: src/uppaal_mcp/integrated/**; tests/test_sdn_layer.py;
  evidence/instantiation/20260908-p2-integrated/**.
- This continuation changes only the evidence directory. Full inherited diff
  additionally includes AGENTS.md, promts/08.09.2026-11.03.md and
  promts/08.09.2026-issue19-recorder-continuation.md: PR blocked.
- Baseline: manifests/baselines/reviewer-r1.yaml, reviewer-r1-candidate,
  SHA256 89b8d6f520546c873649643b3cf90fd80f58e4458a443832369e3d1d28bf719a;
  frozen:false, Gate 1 pending.
- Dependencies: published P0 candidate; merged PR #16 and #18 confirmed via
  GitHub. No scientific acceptance inferred from merges.

Artifacts: evidence/instantiation/20260908-p2-integrated/README.md contains all
seven criterion mappings. reviewer-run-003 retains historical generated XML,
query/composition maps, focused results (19 tests exit 0) and static audit exit 0.
reviewer-unrestricted-004-20260908 contains checks.json, raw logs, dependency
freeze, provenance-audit.json, collector and SHA256SUMS. Its README records exact
reproduction commands and limitations. Audit shows implementation/test bytes
unchanged from `2dc471d`; historical raw logs match recorded hashes.

New check outcomes: fresh isolated install exit 0 outside sandbox; focused exit
5 (zero tests, class setup error), generation exit 1, full suite exit 1 (127 tests,
one setup error, no skips). MCP stdio test completes. Pip consistency, versions,
coordination, YAML, MCP construction, examples, diff-check and real verifyta
version/help exit 0. Historical regeneration audit exit 1. Compile-only exit 1:
XML absent after generation failure. New model audit unavailable for that reason.
Actual tool output is UPPAAL 5.0.0 rev. 714BA9DB36F49691, June 2023.

Verification evidence: N/A, status not_run, no new model_hash/query_hash because
generation failed; no model-checking verdict or license availability claim.
Software/static evidence does not close scientific P2 criteria.

Reviewer reproduction: fetch the handoff branch and verify its SHA, read both
run READMEs and decisions.md; verify SHA256SUMS; inspect provenance-audit.json.
Resolve AGENTS.md pin drift and full PR scope with the independent Integrator
before a new generation/full-suite/audit run in a unique directory. Do not waive
behavioral regressions or silently replace the specification inventory.

Acceptance checklist: all seven criteria have artifacts/results or explicit
blockers in README; final successful reproduction, scoped PR, independent
scientific review and Gate 1 remain incomplete. No downstream scientific
workstream is unblocked. No merge is requested in this blocked state.
