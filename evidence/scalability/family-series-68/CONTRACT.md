# Four-size composition candidate

Issue #68 extends the accepted preparation prototype in PR #67. It does not
accept a new Gate 1. Base read commit:
`54531a34e612c8f056984531a63acb939e6af877`.

The complete inherited semantics are in
[the #66 contract](../family-feasibility-66/CONTRACT.md). Its N<=2 restriction is
replaced for this candidate by the explicit finite domain **N=1,2,3,4**. Its
abstraction, observer, optional-service and interpretation limits still apply.
The generator consumes the same pinned frozen XML; previous files are read-only.

| N | Core | Private boundary | Shared server | Observers | Total |
|---|---:|---:|---:|---:|---:|
| 1 | 20 | 7 | 1 | 22 | 50 |
| 2 | 40 | 14 | 1 | 44 | 99 |
| 3 | 60 | 21 | 1 | 66 | 148 |
| 4 | 80 | 28 | 1 | 88 | 197 |

Each UAV has one PHY link/target, MAC queue/scheduling context, logical SDN
control context and APP session. The single BS denotes an abstract common queue
server, not a measured base-station implementation. Increasing N also multiplies
the inherited per-entity fault/target envelopes and observers. No centralized
controller throughput, packet interference, physical calibration or cutoff is
claimed.

All private globals, clocks, types, functions, process bindings and channels use
the entity's compiled `uI_` namespace. Local clocks remain instance-local. The
only cross-entity functional reader/writer is SharedLoad. Every MAC epoch (5
abstract units), its committed staging chain selects private finite load inputs
and one server in `{-1,0,...,N-1}`. `-1` allows no service. Selecting I requires
the old queue to be nonempty and its scheduling mode COMM or JOINT. Ordered
updates preserve service-before-arrival, K=4, sticky overflow and absorbing q=5.
One recorded service opportunity can consume capacity even for q=5; it does not
mean useful packet departure, command ACK or restored SLA.

SharedLoad publishes the sample and offers/skips each MAC tick in increasing
entity order, without elapsed time in the committed chain. Other committed
automata may interleave. There is no work conservation, priority, fairness,
time-divergence or whole-system deadlock-freedom assumption added by this package.
The fixed notification order prevents silently assuming entity symmetry.

## Correspondence and actual differences

N=1 and N=2 `model.xml`, `queries.q` and `queries.json` are byte-identical to the
merged #67 package. The checker saves the matching hashes. This means these
specific tool inputs are identical; structural/local-step checks alone are not
a whole-composition timed-equivalence proof. The #66 differences from the frozen
single-context model, including input staging, remain unchanged. Historical P3
results keep their historical hashes and scope, with no automatic transfer.

For N=3 and N=4 the same generator loop creates more private contexts and extends
the one shared selector and fixed notification chain. Legacy query expansion
adds per-entity predicates and an all-N encoded-backlog diagnostic. Parameters
are fixed apart from N and its instance vector. New metadata uses Issue #68 and
the current base; the generator digest covers both `generate.py` and
`query_schema.py`. Separate compact P4 query files and `parse-all.q` are additional
artifacts, not replacements for the inherited query files.

## Static argument and its boundary

The checker compares every retained template, private declaration block, clock
scope, binding and endpoint to the frozen source under the entity renaming.
It verifies the exact shared selector, eligibility guard, write order, delivery
routing and committed locations. Before factorizing local truth tables it checks
the allowed AST dependencies of every assignment: private queue updates cannot
read another queue or an untested load class at fixed server selection. Then it
enumerates q=0..5, every scheduling mode, arrival, sticky flag and server choice
for each entity, plus every class input value. The all-queues=1/no-arrival witness
has exactly N+1 outcomes: no departure or one queue decrement, never two.

There are 8 negative controls for N=1 and 18 each for N=2,3,4, including the last
entity of each size. They detect mixed queues/clocks/ACKs/scratch fields, wrong
tick/sample routing, bindings, double service/grants, lost committed locations,
wrong selector bounds, recorder/reset errors and duplicate shared servers.
These are local-expression and composition checks, not reachable-state model
checking. Real diagnostic outcomes and their limits are stored separately.

The frozen timing mismatch D_meas=5 versus T_meas+J=6, deferred admission
recording and other observer/placeholder limitations are retained. A query
deletion does not remove its observer from the model. The candidate concerns
these complete finite compositions only. Acceptance of family/query/assumption
scope and a new Gate 1 remains the Integrator's decision.
