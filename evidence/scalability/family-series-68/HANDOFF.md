# Handoff — P2 family-series-68

- Issue: https://github.com/artmus208/uppaal_sdn_isac/issues/68.
- Deliverable: four-size generator/models, composition checks, bounded behavior
  evidence and proposed P4 measurement protocol, all in this directory.
- Owner/account-id: `vadimnbkg`; independent reviewer/integrator: `artmus208` /
  user-integrator. No author acceptance or Gate 1 decision.
- Branch: `codex/vadimnbkg/68-family-series`; target: `read`.
- Base ref/commit: `read`, `54531a34e612c8f056984531a63acb939e6af877`.
- Published clean source checkpoint used by every verifier invocation and the
  archive reproduction: `2548ec82a8fa98b3e152641fbc7a5eda30e4e07c`.
- Final exact artifact HEAD is recorded in the PR handoff; the canonical named
  branch contains that checkpoint and the source commit above as its ancestor.
- Original checkout and `promts/29.09.2026.md` remain unchanged by this task.

## Checks and evidence

All four models reproduce, compile and load; N1/N2 XML/inherited query bytes
match #67. There are 62 detected structural mutations, dependency-checked local
queue-step cases, 70 byte-reproduced generated artifacts from a full Git archive,
200 repository tests, coordination/MCP/CLI smokes and native Windows monitor
controls. Exact commands/outcomes are in `checks/validation.json` and linked
reports. `RESULTS.md` contains actual scientific verdicts and timeouts, without
promoting initial-state load or a timeout to a scientific claim.

Raw monitor fields, exact source inputs, commands, model/query hashes, actual
tool version, parameters/vector, raw output, traces and memory samples are
retained. `audit_artifacts.py` checks their consistency and the artifact index.
The tested raw-output bug and sample-gap bug in the first harmless monitor
control are preserved; the corrected controls passed before verifier launch.

Historical monitor-control source `c696d1133be64af5d420b4e157f2b6e72db9f1ab`
is in the owner-accessible prepublication bundle. Its runner, monitor and test
source files are byte-identical to those at published `2548ec82…` (Git diff
exit 0). These controls do not execute verifyta and are not scientific results.

## Durable transport

Canonical branch:
https://github.com/artmus208/uppaal_sdn_isac/tree/codex/vadimnbkg/68-family-series.
Git SSH push was unavailable (`Host key verification failed`); publication used
the GitHub Git-data API, checked identical tree hashes and fetched the resulting
commits back. Local prepublication checkpoints were preserved before updating
this task's own branch ref to the identical published tree. No force push to a
shared branch, unrelated reset or stash was used.

Owner-accessible workspace:
`/mnt/c/Users/musta/Desktop/pySources/mcp_uppaal/.worktrees/68-family-series`.
Full bundles inside `evidence/scalability/family-series-68/handoff/` are ignored
by Git and retained on the owner's disk: `source-before-publication.bundle`,
`documentation-checkpoint.bundle`, `reproduction-checkpoint.bundle`, and final
`final.bundle`. The final published source/artifact branch is the preferred
transport. Final working tree is checked clean after publication; local ignored
environment/reproduction scratch and bundles are outside the tracked diff.

## Next step and scope limits

The artifact package is ready for independent review. P4 readiness is conditional:
service reachability for every entity is still unestablished at the diagnostic
budget. Review all open formulas in RESULTS.md and record a justified follow-up
or explicit claim/dependency disposition. Then accept the family/query/protocol
scope and freeze a new baseline through a separate P0/Integrator Gate 1 decision.
Old P3 evidence retains its original scope; no transfer, R03/R04/C06 closure,
Glonina comparison, full P4 series or manuscript work is performed here.
