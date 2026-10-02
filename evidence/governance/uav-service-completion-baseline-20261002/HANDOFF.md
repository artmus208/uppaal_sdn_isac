# Durable handoff — Issue #84

Deliverable: exact UAV N=1 / 51-process APP-completion baseline decision package.
Atomic requirement: N/A — coordination-only; R07 remains Issue #80.
Owner: vadimnbkg. Proposed independent reviewer/Integrator: artmus208.
Target: read. No author self-approval, merge or Gate acceptance.

Workstream branch: `codex/vadimnbkg/84-uav-completion-baseline`.
Base ref: origin/read. Base/input commit:
`61386aa358805082b705dcd00c8cbfde5fb98248`.
Audited implementation checkpoint: `8912a2ca2c2d67c2224893bb473d9fab88075ccc`.
Final HEAD is the exact branch SHA in the PR and owner-side
`handoff/publication.json`, written after final commit/publication. Resolve it before
continuation; do not infer HEAD from this earlier content checkpoint. The handoff
metadata avoids a self-referential final commit hash inside its own Git blob.
Working tree at handoff: clean in isolated `/tmp/uppaal-baseline-84` clone;
the user's original checkout retains its pre-existing untracked files.

Package: `evidence/governance/uav-service-completion-baseline-20261002/`.
Canonical source: published workstream branch / PR to read when present.
Full owner-side backup:
`/mnt/c/Users/musta/Desktop/pySources/mcp_uppaal/evidence/governance/uav-service-completion-baseline-20261002/handoff/final.bundle`.
This bundle includes the workstream branch and the restored original execution ref:
`codex/vadimnbkg/82-execution-checkpoints` at
`956243275584a3dd1cef9f98ef500da5d7b344c9`.
It contains complete histories, not just diffs or selected source ZIP entries.
Owner-side review files are extracted from the exact final content checkpoint;
the bundle/remote ref is the Git source of truth.

## Restore and reproduce

```bash
git clone /path/to/final.bundle /tmp/baseline84-review
cd /tmp/baseline84-review
git switch codex/vadimnbkg/84-uav-completion-baseline
git rev-parse HEAD
git status --short --branch
python3 -B evidence/instantiation/uav-service-completion-candidate/generate.py --check
python3 -B evidence/instantiation/uav-service-completion-candidate/audit.py
python3 -B evidence/governance/uav-service-completion-baseline-20261002/check.py --source-history
python3 -B -m unittest discover -s evidence/governance/uav-service-completion-baseline-20261002 -p 'test_*.py' -v
```

For a canonical remote clone without execution history, fetch the checkpoint ref
from this full bundle first:

```bash
git fetch /path/to/final.bundle refs/heads/codex/vadimnbkg/82-execution-checkpoints:refs/remotes/baseline84/execution-checkpoints
```

Read README.md and proposed-integrator-decision.md; inspect decision-pins.json,
inventories and the proposed patch. Run normal CONTRIBUTING checks with an installed
MCP SDK/CLI. Do not rerun the engine or reuse exhausted candidate budgets.

## Checks and limitations

Exact commands, logs, exit codes and hashes: `check-results.json` and `checks/`.
Static audit pins 192 files, 51 process bindings, all eleven query formulas/hashes,
all nine native cells, raw engine version strings and original execution-tree
membership. Twelve proposal controls (including model/parameter/vector/query drift,
real old PR81 trace attribution, fake freeze/activation and checkpoint relabelling)
and twelve original candidate controls check their respective obligations.

Initial full 209-test sandbox run failed with MCP stdio timeout and two missing CLI
entrypoint failures. The first outside retry removed the timeout but retained the
CLI setup failures. Initial offline install lacked setuptools; cached build wheels
then enabled installation from a separate exact source-copy staging directory.
Dependencies were reused read-only through an isolated venv; current checkout src
was explicit PYTHONPATH. The final installed-outside suite passed all 209 tests with no skips; earlier failures
are retained, not relabelled as successes.
No new UPPAAL execution or version/license probe. Historical engine simulation/replay
has null query_hash/property_verdict; all eleven query verdicts remain open.

## Exact current gate state and next action

New Gate 1: pending independent decision. Operational scope: inactive.
Baseline frozen/activated: false. Operational manifests remain unchanged.
Prepared patch is applicable but not installed. Historical default/P4 policy retained.
No P3_core_evidence_accepted, R07 closure, universal completion/SLA/fairness/deadlock claim.

Next action is independent review and explicit A: new P1/P2 applicability;
B: exact inputs/query-selection/Gate 1; separate phase-two scope/patch authorization.
Only then continue this Issue with approved operational changes, checkpoint and
independent PR to read. C activation requires actual accepted merge and a distinct
Integrator decision with real merge SHA and UTC time. D retains open verification
claims. Use the concrete draft decision, not a recollection of this chat.
