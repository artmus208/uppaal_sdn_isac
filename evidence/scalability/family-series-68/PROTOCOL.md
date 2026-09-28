# Candidate P4 protocol — Issue #68

Status: proposed; no series authorization or Gate 1 acceptance is implied.
Question: how does formal-checking cost change for N=1,2,3,4 interacting UAV
contexts sharing one optional MAC queue-service opportunity per epoch?

## Frozen experiment inputs

Use the four complete generated XML models (50, 99, 148, 197 processes), the
same committed generator/input pins and parameter set, and the schema in
`query_schema.py`. Only N and the corresponding instance vector change. No
observer removal, reduction, fairness, priorities, parameter tuning or search
strategy adaptation between sizes. No transfer from the historical P3 runs.
Before P4, P0/Integrator must record the accepted commit, model/query/generator
hashes, parameter/vector files, actual verifier version and family scope.

## Query meanings and experiment roles

Every `generated/nN/p4-queries.json` row records the exact formula, substitution,
assumptions, scope and nonvacuity. Every measured process receives exactly one
file `p4/<id>.q`. The compact schema is:

| ID | Formula schema | Role / nonvacuity |
|---|---|---|
| shared-capacity | `A[] (sum_i (family_grant_i ? 1 : 0) <= 1)` | Global recorded opportunity cap; each service reachability checks the cap is exercised. Does not prove useful departure after absorbing overflow. |
| uI-service | `E<> family_grant_I` | One existential per entity, initially false. Separate executions may witness different entities; no fairness or SLA claim. |
| joint-backlog | `E<> AND_i (uI_mac_queue_q > 0)` | Simultaneous backlog, initially false. N=1 is a control. |
| u0-queue-safety | `A[] !u0_mac_queue_overflow_seen` | Exact renamed original C01-queue; test near-capacity reachability via u0-queue-full. No truth presumed with optional service. |
| family-queue-safety | `A[] !(OR_i uI_mac_queue_overflow_seen)` | One conjunction of original per-entity obligations. Predicate grows with N; report separately. |
| u0-queue-full | `E<> u0_mac_queue_q == u0_mac_queue_K && !u0_mac_queue_overflow_seen` | Exact renamed original boundary nonvacuity diagnostic; no all-entity inference. |

`sum`, `AND`, `OR`, and `I` above denote generation-time substitution, not UPPAAL
syntax. Generated files contain only concrete symbols/expressions. Queue capacity
stays K=4 and overflow value 5 remains absorbing. Claims concern abstract finite
models with preserved source observers and loss paths, not physical time or a
centralized controller's capacity. A negative queue-safety verdict is meaningful
behavior, not a generator failure. A timeout establishes no property verdict.

The primary cost curves have **one query per N**: fixed-u0 service, fixed-u0
queue safety and fixed-u0 queue-full. Global capacity/backlog/family safety form
separate curves with N-dependent predicates. The N service queries form a
separate coverage workload: publish individual times and sum/maximum plus query
count, never label their sum as the cost of one query. Do not assume symmetry:
the notification order is fixed by entity index. N=1 family safety is intentionally
a syntax-distinct control for the same logical requirement.

## Strategy, order, repeats and budgets

Candidate host: Windows 10 build 19045, Intel Core i5-8300H @2.30GHz, 8 logical
CPUs, 17,033,019,392 bytes physical RAM. Initial available memory was only
3,152,867,328 bytes, so use one verifier process and **2 GiB measured-memory
stop**, retaining at least 1 GiB available RAM before launch. Do not infer a
Windows process's RAM from WSL memory. Capture host/available RAM for each run;
if the headroom is absent, mark the run not started and wait for an explicitly
scheduled new session, rather than changing the budget.

The runner's recorded command/settings and actual `--help` output are authoritative
for option syntax. Use explicit depth-first search (`-o 1`), seed 68, statistics,
exact state representation and the verifier's unchanged default reduction/storage
settings: exhaustive symbolic exploration 0, compact DBM representation 1,
conservative space consumption `-S 1`, automatic extrapolation `-n 0`, and
default compressed hashmap discrete storage. No approximation, bit-state
hashing or automatic strategy fallback. Request the summary with `-u`; the
schema has no liveness formula (the tool warns its summary is wrong for those).
Behavior runs use `-t 0 -f <unique-prefix>` for some symbolic witness or
counterexample; include trace writing in end-to-end time and retain trace hashes.
One query per fresh process prevents prior-query cache effects. The compile and
load phases use the same tool/seed and preserve raw option output. For the future
series, confirm these settings against the accepted tool version before starting.

Proposed series (requires a separate P4 Issue and accepted new Gate 1):

1. Generate the entire four-size family once per repeat and measure that phase
   separately. Use ascending N=1,2,3,4. For each N measure compile-only and load,
   then the query IDs in their `p4-queries.json` order. Repeat this
   complete order three times. No warm-up runs or cache flushing; describe OS
   file-cache effects and retain each observation rather than deleting outliers.
2. Limits: generation 30 s; compile/load 60 s; each scientific query 60 s;
   measured memory 2 GiB; total verifier wall budget 2 hours. Thirty queries per
   sweep, three sweeps (maximum 90 minutes query time), plus compilation/load fits
   this cap. These are proposed future limits, not permission to run them here.
3. On a query timeout or memory threshold stop, record the censored observation
   and continue independent query cells. No extra repeats beyond the three
   scheduled ones, no automatic limit increase. Do not extrapolate a universal
   scalability boundary from one censored cell.
4. On compilation/load failure, skip that N's queries. On monitoring failure,
   unexpected verdict format, license error, disk failure, hash mismatch or
   exhausted total budget, stop the series and retain all completed evidence.
   If the same query reaches a limit in all three repeats at a size, report its
   observed boundary under this budget; do not silently omit it or change strategy.
5. Report individual observations and median/range for completed comparable
   cells. Keep timeout/memory stops separate; do not replace them by exact 60 s
   successes or average only the surviving samples without censoring disclosure.

Preparation in #68 uses one diagnostic attempt per selected N/query only,
at most 60 s per invocation and 1200 s total verifier wall time, 2 GiB stop.
It is not the three-repeat series above. The executable diagnostic plan and
actual per-invocation budgets are saved with the runs. No automatic retries.

## Measurement boundaries

- Generation: time the Python generator separately, without verifier. Record
  resulting hashes; filesystem writes are included.
- Compilation: `UPPAAL_COMPILE_ONLY=1`, retaining compressed lossless compiler
  stdout and stderr. This does not validate external queries. A separate
  `parse-all.q` run with `--query-index 0` parses queries and executes only
  `E<> true`; it is a load test, never nonvacuity evidence.
- Model checking: fresh verifier invocation for a single scientific query;
  external wall/CPU/peak memory includes process startup and compilation. Also
  retain the tool's reported verification CPU time/states/memory, if supplied,
  as the engine-only metric. Do not subtract a separately measured compile time
  to manufacture an exact model-checking time. If the tool does not expose a
  separate engine metric, mark it unavailable and report the end-to-end metric.
- Memory: native process private bytes and working set sampled with documented
  interval; the larger observed value triggers the stop. Preserve peak working
  set and sampled peak private bytes separately. Sampling is a stop threshold,
  not an exact OS allocation cap; its detection delay is recorded. Monitoring
  absence/failure aborts, never becomes a fictional memory constraint.

All runs retain run_id, source commit, status, explicit verdict or null, full
command and environment overrides, actual version, input/model/query/generator
hashes, parameters/vector, timestamps, hardware, limits, resource availability,
stdout/stderr and any trace references. A success exit alone is insufficient
for a verification claim. Trace generation settings are part of the command;
if no trace is requested/generated, record that rather than inventing one.

The joint-backlog predicate deliberately matches #66: a nonempty queue includes
the absorbing overflow sentinel 5. It does not require every queue to be live
and pre-overflow. Interpret witnesses within that abstraction; imposing a
no-overflow conjunct would be a different diagnostic requiring an explicit
query-schema decision.

## Decisions before P4

Integrator must accept the four-size domain and shared optional service/per-UAV
logical-controller interpretation; review the preserved abstraction/observer
limitations and unresolved diagnostic properties; accept the query schema,
search/measurement budget and host; then freeze a new baseline with hashes and
version. Decide whether any open nonvacuity result blocks a selected curve or
requires a narrower claim. Old P3 results retain their original scope. R03/R04/C06
and comparison with Glonina remain outside this preparation deliverable.
