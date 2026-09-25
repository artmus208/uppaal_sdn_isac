# C01: recovery invariant audit and remaining deadlock strategy

Issue #39, owner vadimnbkg. Base ref `read`, base commit
`840105be7990a5527d7934450bb3dce0f3e04f7a` (user-accepted PR #54 merge).
Branch `codex/vadimnbkg/39-c01-structure`, target `read`.
Write scope: this directory only. Frozen model, queries, sources, manifests and
all preceding evidence remain unchanged. This is a static proof-support package,
not a new UPPAAL verification run or an independently accepted C01 result.

## Result

The pinned recovery topology supports an inductive proof of both attempt bounds
and recorder protocol correctness. It needs neither a time-divergence assumption
nor successful recovery. The proof concerns all finite prefixes of the concrete
frozen composition, including prefixes of blocked or Zeno executions.

The previous full-model query results remain timeout/null. No positive machine
verdict is created by the Python checker. Counting this proof toward C01 needs
explicit review and acceptance of the proof-based evidence route; the accepted
C02 exception does not automatically authorize another substitution.

Global deadlock freedom is not proved by the recovery argument. It remains the
principal global obligation after any acceptance of these local invariants.
Queue overflow remains the existing negative result with a saved counterexample.

## Pinned premises

Full model: `evidence/governance/20260906-baseline/gate1-20260923/model.xml`.
SHA256: `592678ed678ce8f70cf278f542e48bd2bb739969b53a962423d3e63f91e3e1e2`.
Baseline: `reviewer-r1-gate1-20260923`.

`check.py` checks the exact initializations and all three recorder function
bodies (XML lines 511–531), the unique `sdn_A_REC_0` instance, six recovery
locations, all 22 edges (lines 3673–3857), all recorder call sites and absence
of other global/local references or external writes. Both ordinary and late
outcome copies are retained. It rejects changes to those pinned premises.
It is not a parser or soundness checker for arbitrary UPPAAL source programs.

The complete edge/guard/synchronization inventory is in `audit.json`.
Guards, invariants and synchronization only restrict which listed recovery
edges execute. Other templates cannot change the recorder variables, including
on synchronizing partner edges. Passage of time does not modify these discrete
variables. Consequently their effects on the proposed invariant are identity.

## Inductive argument on the concrete XML

Let a be active, p primary count, r rollback count, t total count, b sticky bad,
and e sticky protocol error. All locations have b=e=false, p<=1, r<=1 and t=p+r.
The stronger location-indexed invariant is:

| Recovery location | Additional invariant |
|---|---|
| StableConfig / RecoveryFailed | a=false; completed-episode counters may remain |
| FailureDetected | a=true, p=0, r=0, t=0 |
| StandbySwitch / ReactiveReembedding | a=true, p=1, r=0, t=1 |
| Rollback | a=true, r=1, p in {0,1}, t=p+1 |

Initially StableConfig has all counters zero and both sticky flags false.
For each concrete transition:

- Edges 0–1 start only in inactive StableConfig, reset counters and enter
  FailureDetected. A duplicate active start is impossible under the invariant.
- Edges 2–3 are the only primary dispatches. They leave FailureDetected with
  p=0, set p=t=1, and enter one of the two primary-wait locations.
- Edges 4, 7–8 are the only rollback dispatches. Each leaves a location with
  r=0, enters Rollback with r=1, and increases t to p+1<=2.
- All recovery exits, including late copies (5–6, 9–13, 15–21), call finish
  from an active location, clear a and enter StableConfig or RecoveryFailed.
  Finish preserves the counts. A subsequent start resets them at the next episode.
- Edge 14 is the RecoveryFailed report self-loop and touches no recorder field.

There is no edge that returns from a primary-wait location to FailureDetected
or dispatches again within that location; no edge dispatches again in Rollback.
The error branches in start/dispatch/finish are therefore unreachable under the
invariant. Saturating updates cannot conceal a violation in this argument:
all inductive predecessor states are below saturation, and sticky b remains false.
Local timeouts or unsuccessful recovery still terminate the counted episode;
this is not a proof that the network service recovers or any episode must finish.

`check.py` enumerates the finite declared recorder valuation domains, selecting
all valuations satisfying each source-location invariant, and checks each edge's
recorder update against the target invariant. It checks 35 edge/valuation
obligations. This is an induction-obligation check, not exploration of the full
network state space: 35 must not be reported as UPPAAL states explored.
The update semantics are an explicit Python transcription of the function bodies
whose exact syntax is checked. Review must examine this transcription and the
noninterference premise; passing assertions alone is not independent approval.

Sensitivity checks reject removed finish, an external recorder write, an extra
recovery instance, and a repeated primary-dispatch obligation that violates the
invariant. These are in-memory checks; no altered XML is published or executed.

## Global deadlock: separate disposition

Local safety is compatible with a blocked composition. Dropping clocks, guards,
observers or synchronization cannot be used here to establish deadlock freedom:
such changes can enable a transition that is unavailable in the full model.
No deadlock-preserving abstraction has been established.

The accepted P1/P2 scope already identifies the PHY D_meas=5 versus T_meas+J=6
discrepancy and retained timing observers as limitations
(`evidence/governance/20260910-p1-p2-review/final-20260923/README.md`, lines 73–76).
Those local warnings do not constitute a reachable global deadlock witness.
Likewise, the saved unconditional-ACK counterexample is a noncompletion result,
not automatically a deadlock counterexample.

The completed full-model deadlock attempts used BFS/shortest at 60 seconds,
DFS/some trace at 60 seconds, then DFS/some trace at 300 seconds; all timed out.
Their saved records remain the only execution evidence for this obligation.

For a subsequent bounded attempt, change the search strategy rather than repeat
the same DFS budget increase: use full-model symbolic exploration with randomized
DFS order (`--exploration 0 -o 2`), explicit seed (`-r 20260925`) and exact DBM
representation (`--state-representation 0`), retaining the original query and
300-second/2-GiB limits. The exact installed tool's captured `verifyta-help.txt`
documents these options. This is a proposed experiment, not an executed run or
claim that a counterexample will be found. It may require runner option support
and its own clean source checkpoint/fresh run ID before execution. Do not use
bit-state hashing or concrete randomized exploration as an exhaustive proof.

## Reproduction, checks and acceptance boundary

```sh
python3 -B evidence/verification/p3-20260925-c01-structure/check.py
```

Stdout must match `audit.json`. Commands, source/manifest hashes and check outcomes
are retained in `checks.txt`. The native tool was invoked only for help/version,
not model checking. The original timeout machine records are linked from the
previous [C01 report](../p3-20260925-c01/README.md), with exact run IDs, statuses,
model/query hashes, tool versions and raw archives. No new verification run ID
or positive verdict is assigned to this static audit.

Acceptance requested: review the concrete inductive argument and decide whether
it may count toward the two attempt-related C01 obligations. Global deadlock,
reachability and total P3 acceptance remain separate. No automatic extension of
the C02 scope exception, no Gate 1 change, and no new Issue or model repair.
The exact published HEAD and handoff PR are recorded in #39.
