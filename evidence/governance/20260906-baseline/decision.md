# Issue #6: accepted governance procedure

- Issue: https://github.com/artmus208/uppaal_sdn_isac/issues/6
- Decision: https://github.com/artmus208/uppaal_sdn_isac/issues/6#issuecomment-5572059620
- Date: 2026-09-07; maintainer confirmation recorded through `artmus208`.
- Proposal author: `carwasher`; implementation owner/account-id: `artmus208`.
- Atomic IDs: N/A — coordination-only.
- Base ref: `origin/read`; base commit: `11bd69bdca9a1209f820258b3732b3c865f79035`.
- Branch: `codex/artmus208/6-baseline-governance`; target: `read`.
- Implementation acceptance: independent review pending; no scientific gate accepted.

The maintainer accepted the procedure proposed in `governance-proposal.md` at
`0e237aa8bfd87a79c86459af14db521f44092bbc` and activated Issue #6's write scope:
`manifests/baselines/reviewer-r1.yaml`, `manifests/collaboration-v1.yaml`,
`scripts/check_coordination.py`, `tests/test_coordination.py`, and
`evidence/governance/20260906-baseline/**`.

1. Preserve the historical dirty candidate and its original hashes. Select an
   exact clean source commit only after intended model/generator changes are
   accepted; then record explicit candidate supersession. No such replacement
   commit is selected by this implementation.
2. Pin source/generator and per-configuration model/query hashes to that commit.
   Keep `frozen: false` until accepted scientific P1/P2 inputs and independent
   Gate 1 acceptance supply the integrated model, interface contract, parameters,
   instances, queries and working verifier.
3. Store P3 runs under `evidence/verification/runs/<run_id>/` and P4 runs under
   `evidence/scalability/runs/<run_id>/`. Each future Issue reserves unique run IDs.
   Existing evidence stays in place.
4. Audit all stored file and aggregate hashes separately from structural checks,
   distinguishing checkout bytes from exact committed blobs.
5. Preserve the historical WSL license failure. The native Windows availability
   reported in PR #10 is dated diagnostic evidence from another environment,
   pending independent review; it is neither a new local measurement nor model
   checking. Do not overwrite historical baseline tool availability with it.

The historical baseline is byte-identical to the Issue base. Updating hashes
alone cannot replace scientific acceptance. Implementation review must be
independent of its owner; this policy decision does not approve the resulting PR.
