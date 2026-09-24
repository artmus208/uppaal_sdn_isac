# C02 property-specific abstraction (Issue #39)

Experimental P3 evidence, owner vadimnbkg, continuation base
c110112ff9502bffe5a3708a496b3bbe307c7f3c; original task base
adea99b05195191eec115621613d4190eba06bf0, branch
codex/vadimnbkg/39-core-verification, target read, PR #50.
Write scope: evidence/verification/**. Gate 1 dependencies accepted in #6/#48.
The frozen model, generators, manifests and earlier evidence are unchanged.

## Construction and review obligations

`build.py` rejects any full-model bytes except SHA256
592678ed678ce8f70cf278f542e48bd2bb739969b53a962423d3e63f91e3e1e2.
It constructs one process, two locations, two clocks and two Boolean recorders.
`source-audit.json` lists every textual reference to retained variables and maps
all five scheduler edges crossing the WaitPHYAck boundary to abstract edges.
Their guards and retained assignments are copied, including BOTH late branches;
no late branch is deleted on the assumption that C02 holds. The WaitPHYAck
invariant is copied verbatim. All synchronization requirements are removed.
All other locations collapse to Inactive. Hidden transitions are represented by
unguarded stuttering self-loops. C02.q has exactly the original query bytes/hash.
This is a reviewed, pinned construction, not a general-purpose slicing algorithm.
The reference inventory is a review aid, not a semantic proof checker.

## Timed simulation argument (requires independent review)

Relate concrete and abstract reachable states as follows:

- Abstract WaitPHYAck iff the unique concrete MAC scheduler is in WaitPHYAck;
  otherwise abstract Inactive. Both Boolean recorders agree everywhere.
- In WaitPHYAck both clock values agree across the models. In Inactive neither
  clock is constrained by the relation: the query ignores clocks when inactive.

Initial states are related: scheduler Idle, both recorders false. Inspection of
all pinned-source references establishes that only the scheduler writes these
recorders/clocks; declarations initialize them. Other templates only read them.
The scheduler has one entry and four exits, and its WaitPHYAck self-loop updates
only policy variables. Thus active is equivalent to the scheduler waiting,
independently of whether the C02 clock bound holds.

Every concrete delay in WaitPHYAck satisfies the retained invariant and can be
matched with the same delay. In Inactive the abstraction permits every delay;
removing other invariants, urgent/committed restrictions and synchronization
constraints adds behavior. Both retained clocks have ordinary unit rate.

Entry resets both clocks and enables active identically, restoring clock
agreement even if inactive clocks differed. Every concrete exit matches a copied
guard/update edge; any matching sender/receiver constraints have only been
relaxed. The retained writes on synchronized partner edges are absent, as shown
by the source inventory. Other discrete steps stutter. Functional clock resets
outside WaitPHYAck do not break the relation because inactive clocks are hidden.
No hidden step modifies either recorder. There are no extra entries/exits.

Consequently every concrete finite reachable prefix has a matching abstract
prefix preserving the C02 predicate. If the abstraction satisfies A[] C02, this
simulation argument supports transferring that safety statement to the pinned
full model. Independent review must accept the argument before that transfer is
used as a project verification claim. An abstract counterexample may be spurious.

This does NOT prove unconditional ACK completion, fairness, absence of Zeno runs,
deadlock freedom, PHY receipt, or validity of the model as a real-network model.
Explicit stutter loops retain the possibility of time-stopped execution.
The previous full-model 600-second timeout remains inconclusive and unchanged.

## Checks and reproduction

From repository root (Python environment with repository dependencies):

```sh
python3 evidence/verification/p3-20260924-c02-reduced/build.py --check
python3 evidence/verification/p3-20260924-c02-reduced/run.py \
  --run-id p3-20260924-c02-reduced-001 \
  --verifyta '/mnt/c/Program Files (x86)/UPPAAL-5.0.0/bin/verifyta.exe'
```

Use a clean committed checkout and a NEW run ID if 001 exists. Native invocation
uses the existing monitored PowerShell wrapper: 30 seconds/query, sampled 2 GiB
stop, BFS, some trace. Raw version/hardware/command/status/hash/trace files are
retained per run. The current host requires WSL Windows interop outside sandbox.

Four checks: exact C02 on model.xml; reachability of an active request;
reachability of an active request at deadline 3; exact C02 on negative-control.xml.
The negative control differs only by removal of the waiting invariant and should
violate C02. Reachability witnesses concern the abstraction, not the full model.
Expected verdicts are not results; only runs/*/results.json contains machine
results. A failed/error/timeout run cannot substantiate a property claim.

Acceptance still requires independent evidence and abstraction review, not author
self-acceptance. The active baseline and C02 acceptance status are not changed.
