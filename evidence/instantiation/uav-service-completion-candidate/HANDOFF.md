# Issue #82 handoff

- Deliverable: full N=1 request-correlated UAV result/APP completion candidate.
- Owner: vadimnbkg. Proposed independent reviewer/Integrator: artmus208;
  appointment and acceptance remain external decisions.
- Branch: `codex/vadimnbkg/82-uav-service-completion`; PR target: `read`.
- Exact base: `91113a1b634f030c7e895f54f5c36a0b140d66eb`, merged PR #79.
- Write scope and all changed paths:
  `evidence/instantiation/uav-service-completion-candidate/**` only.
- Published exact HEAD is recorded in the PR handoff fields and canonical
  branch ref. Check it with `git rev-parse HEAD` after fetching that branch;
  the publication audit compares the entire Git tree with the checked package.
- Working tree at publication: clean. Original dirty owner checkout was
  preserved; implementation used `/tmp/uppaal-service-82`.

Inputs and decisions: PR #69/#73/#75/#79 merged; limited P1/P2 decision
PR73#issuecomment-5890790922; family P4 activation
PR75#issuecomment-5891123461; v2 activation #64. Baseline IDs/hash records
are in assignment.json and inventory.json. Optional unaccepted #81 supplied
diagnostic harness context only. This changed candidate is not activated or
frozen and does not close R02/R05/R06/R07.

Completion of preparation: deterministic full composition, exact causal
contract, queue/transport/sample correlation, explicit non-success outcomes,
strict clock boundaries, interface inventory, eleven unexecuted queries,
meaningful scoped regressions, healthy 100-step native witness, independent
100-step replay, two negative replay controls and retained failed cells.
README.md/results.json/PROTOCOL.md contain the evidence and its limits.
Checks: 12 scoped and 209 repository tests passed; coordination/MCP/CLI/version
checks passed. Initial sandbox failures and one incorrect version command
remain in the raw check logs. No exhaustive property verdict was obtained.

Obtain the result from the canonical GitHub branch and PR. Because shell Git
credentials were unavailable, the final checked tree was published through
GitHub Git-data operations; its commit identity can differ from local execution
checkpoint identities. Run source_commit values remain exact: the healthy
simulation used `cd40b51` (full identity in its provenance.json); replay used
`f6adba0aee8e037557020009fc43591d732f053d`. All nine historical source states
are independently hash-auditable from source-snapshots.zip. No source or
result hash is rewritten to match the publication commit.

A full checkpoint-history bundle, including the final canonical published
branch and the local execution-checkpoint branch, is saved on the owner's
persistent filesystem at:

```text
/mnt/c/Users/musta/Desktop/pySources/mcp_uppaal/evidence/instantiation/uav-service-completion-candidate/handoff/final.bundle
```

The adjacent publication.json records source checkpoint HEAD, published HEAD,
base, tree equality, bundle path and clean state. Earlier per-run full bundles
are preserved there as additional recovery points. They are outside the
temporary clone and ignored by Git. To recover history, clone final.bundle
into a fresh directory and switch to the named canonical branch; then check
HEAD against the PR/publication record before continuing. The original local
checkpoint ref is `codex/vadimnbkg/82-execution-checkpoints`.

Next step: independent review of Issue #82 acceptance criteria and evidence,
including sample-age/update abstraction, FIFO service and bounded protocol
amendments. Any new native campaign needs its own protocol/run IDs. Reviewer
decides acceptance; any frozen-baseline activation needs a separate governance
Issue and new Gate 1 decision. Production-generator integration and downstream
#80 verification require their own authorized scopes/dependencies. No adjacent
deliverable or manuscript change was made. Reproduction commands are in
README.md; raw traces can be extracted to fresh scratch without altering runs.
