# C01 structural deadlock obligations on the frozen model

PR #56 was accepted by the user and merged into `read` at
`7a4ac3c47329548612b0a563bf9cae20e3835384`. This report continues Issue #39/C01,
owner vadimnbkg, branch `codex/vadimnbkg/39-deadlock-structure`, from that base.
It is static proof support, not a new UPPAAL run or acceptance of C01/P3.

## Result

The exact frozen XML contains 50 templates/instances, 272 locations and 851
transitions. There are 50 committed locations, no urgent locations, no urgent
channel declarations, and 62 locations with invariants. `inventory.json`
records every committed/invariant location, its outgoing guards, updates,
synchronizations, target invariant and all syntactic receivers of each send.
Edge indices are zero-based within their template in the original XML.

Five committed observer locations have a sufficient local escape argument:

| Template | Committed locations | Guard partition |
| --- | --- | --- |
| phy_Template_ObsSenseReport | Observe_1 | phy_c_obs_sense <= phy_D_report / > phy_D_report |
| phy_Template_ObsFreshness | Observe_1 | phy_c_obs_fresh <= phy_D_sense / > phy_D_sense |
| phy_Template_ObsBeamRecovery | Observe_1, Observe_2, Observe_3 | phy_c_obs_beam <= phy_D_BM / > phy_D_BM |

For any legal global state containing one of these locations, one of its two
internal edges is enabled: the clock is real-valued and the bound is a literal
integer constant, so exactly one guard holds. Neither edge has selection,
synchronization or updates; both targets have no invariant. Other processes'
valuations and invariants remain unchanged. The source is committed, satisfying
the commitment restriction even if another process is also committed. There
are no channel/process priorities. Therefore such a state has an immediate
action successor and is not a deadlock. This says nothing about whether these
locations are reachable, whether the next state is a deadlock, or whether time
eventually advances. It is a source-based lemma, not a machine verification
verdict.

The conservative checker certifies only this narrow syntactic pattern (and an
unconditional no-update internal edge to an invariant-free target, if present).
The other **45 committed locations** remain unclassified by that checker;
this is not a claim that their exits are missing or unsafe. **All 62 invariant
locations** still need the global deadline argument. These counts are local
locations, not numbers of reachable global states or independent new tasks.

## What remains to justify the original formula

The [UPPAAL symbolic-query semantics](https://docs.uppaal.org/language-reference/query-semantics/symb_queries/#deadlocks)
defines deadlock by absence of an action successor after any admissible delay.
Merely permitting time to pass is insufficient. A complete argument must
cover reachable global states and eventual action availability, including
states outside the committed/invariant inventory.

The [UPPAAL transition semantics](https://docs.uppaal.org/language-reference/system-description/semantics/)
requires target invariants after updates and restricts transitions when a
process is committed. A broadcast send does not require a receiver, but enabled
receivers participate and their updates/target invariants must be considered.
A list of channel endpoints is not a proof that a synchronization can execute.

The inventory makes the remaining checks concrete:

1. **Boundary publication and delivery.** Inspect the committed sends in
   Boundary_E_PHY_INPUT.Publish, Boundary_E_MAC_LOAD.Publish,
   app_A_REQ.RequestReady, Boundary_E_SERVICE.Terminate and Boundary_B_KPI's
   publication chain against the enumerated receiver transitions. Guards are
   evaluated before updates; receiver participation and target invariants
   prevent treating every broadcast as automatically executable.
2. **Committed staging.** Establish valid updates and target invariants for
   the 24 PHY sample stages, admission/policy staging and KPI dispatch. For
   example, Boundary_B_ADMISSION.StageRequest has an unguarded internal edge,
   but its target OfferRequest has `x <= bus_D_bus`: the no-update escape
   checker deliberately does not infer the required clock invariant.
3. **Deadline exits and global coverage.** For all 62 invariant locations,
   cover the boundary valuations and all simultaneously active invariants,
   with valid synchronization/update successors. Then establish that states
   without an immediate action can delay to an action. Observer activity must
   not be mistaken for service progress or time divergence.

These are sub-obligations of existing C01, not new Issues. This report does not
silently remove observers, modify the model, add fairness, increase the run
budget or substitute a reduced query for `A[] not deadlock`. The original
error/timeouts remain unchanged. No deadlock witness or complete proof has
been obtained here; next technical work is the boundary synchronization and
staging proof using the source-linked inventory.

## Reproduce and review

Model: `evidence/governance/20260906-baseline/gate1-20260923/model.xml`.
SHA256: `592678ed678ce8f70cf278f542e48bd2bb739969b53a962423d3e63f91e3e1e2`.
Baseline: `reviewer-r1-gate1-20260923`; original query hash:
`a53c752ecabf84d28dc0ea1567c0589ffb632777a5ad7178f70be0d2d99e5334`.
No new verification run_id/status/tool result is created. Prior native evidence
uses UPPAAL 5.0.0 (rev. 714BA9DB36F49691), June 2023.

```sh
python3 evidence/verification/p3-20260925-deadlock-structure/audit.py
```

The checker pins model bytes and compares the reconstructed inventory exactly
with the saved JSON. Four in-memory negative controls remove one branch,
introduce a guard gap, add an update, or add a target invariant; each must lose
its local certificate. A positive control checks the unchanged source pattern.
No mutation is written to the frozen model or run through verifyta. It does
not evaluate general guards/functions or explore the state space. All update
and receiver records outside the five certificates are review inputs only.

Changes are limited to this new evidence directory. `checks.txt` records
commands and limitations. Acceptance requested is review of this inventory and
local lemma, not a new global verification claim or extension of the accepted
C02/attempts proof scope.
