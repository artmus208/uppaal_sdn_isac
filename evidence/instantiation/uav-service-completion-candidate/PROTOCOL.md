# Issue #82 native candidate protocol

Authorization: user instruction to execute Issue #82 in this implementation
chat, including its explicit engine-witness criterion. No authority, budgets,
run IDs or semantic results transfer from #78/#80. Candidate preparation only;
new P1/P2 acceptance and Gate 1 are still required for downstream P3/P5 claims.

Full changed model: 51 instances, original 50 plus one result job. Input/base
and candidate model, generator, parameter, instance and query hashes are pinned
in inventory.json/assignment.json. The runner verifies model hash and a clean
source checkpoint before every invocation, and saves the exact source commit,
all input/tool binary hashes and expanded command before launch. Actual tool
version is captured by Engine.getVersion; a guessed version is never evidence.

Question: does the engine admit the complete matching healthy causal chain?
spine.tsv proposes edge/select preferences, with no imported final state.
Engine.getInitialState/getTransitions provide all states and transitions.
Maximum 256 nodes, 64 failed branches, 128 transitions, 4 successor choices per
waypoint; 55 s internal timeout, 60 s native timeout. Missing path is inconclusive.
Saved states include the entire integer vector, locations and closed DBM.
Independent replay matches every edge/select, full discrete vector and the
nonempty intersection of saved/reachable clock zones; this intersection is
carried forward. No independent selection of convenient times from each zone.

Commands from repository root:

```
python3 -B evidence/instantiation/uav-service-completion-candidate/generate.py --check
python3 -B evidence/instantiation/uav-service-completion-candidate/run.py --build
python3 -B evidence/instantiation/uav-service-completion-candidate/run.py --cell simulate --name simulate-001 --input evidence/instantiation/uav-service-completion-candidate/spine.tsv
python3 -B evidence/instantiation/uav-service-completion-candidate/run.py --cell replay --name replay-001 --input evidence/instantiation/uav-service-completion-candidate/runs/simulate-001/trace.xtr
python3 -B evidence/instantiation/uav-service-completion-candidate/run.py --cell negative-discrete --name negative-discrete-001 --input evidence/instantiation/uav-service-completion-candidate/runs/simulate-001/trace.xtr
python3 -B evidence/instantiation/uav-service-completion-candidate/run.py --cell negative-clock --name negative-clock-001 --input evidence/instantiation/uav-service-completion-candidate/runs/simulate-001/trace.xtr
```

At most five native engine invocations: initial simulation, one justified
corrected simulation if a specific driver/schedule problem is identified,
one replay, two controls. Changes require recorded addendum and checkpoint.
No identical retries or exhaustive strategy sweep. Aggregate native budget
600 s, including fresh metadata/probes/cleanup, with 90 s launch reserve.
Each wrapper increment and accumulated cost are retained. Stop on tool,
license, resource/lifecycle failure, hash drift or unexpected negative control.
Queries are published, but exhaustive query execution is outside this witness
campaign: query_hash=null and property_verdict=null for simulation/replay.

Native Windows JDK17/UPPAAL engine via WSL. Java heap cap 512 MiB; owned tree
sampled stop 2 GiB (not a hard native allocation cap); fresh native available
RAM >=3 GiB before each launch. Monitor uses PID plus creation time and kills
only owned processes; confirms reap. 100 ms requested sample interval; actual
gaps remain in memory.csv. Python watchdog 80 s plus 20 s identity cleanup.
Unique run directories refuse overwrite. Partial/failing runs are retained.

Controls change only the expected final sample identity (1 to 0) or require
measurement_age=0, disjoint from an acquisition that has already spent 5 units.
Final-state delay closure may advance clocks after receipt, so imposing a
later sample age would be an invalid negative control. Model XML
is unchanged. These test replay's discrete/zone checks, not universal safety.

Driver provenance: model-independent DBM/XTR routines are compiled read-only
from #79 TimedReplay.java at the pinned base. Scoped search/replay and resource
monitor code is adapted from optional #81 diagnostic source; original and new
hashes are recorded. The separate candidate's result requires its own engine
states and replay; historical evidence establishes none of its properties.

## Readiness correction, before simulate-002

simulate-001 at source df63fa793a2485f15adcaf135a7f655386e0cb7f returned a
model-compilation error (empty parsed /nta/system), with zero transitions.
It spent 2.1194943 s wrapper-native wall and its raw model/logs remain intact.
The cause was added APP/PHY locations serialized after transitions: NTA's
Java XML reader is order-sensitive. The compiler now sorts template element
groups into name/parameter/declaration/location/init/transition order. An
offline Java loader check confirms all 51 templates AND nonempty candidate
system before execution; it invokes no engine. Structural tests now include
this ordering. The replacement candidate has its own model hash.

This specific readiness failure is counted separately from actual directed
simulation. Fixed campaign allowance: at most six engine invocations, including
this failed setup cell, up to two actual directed simulations (second only
after a diagnosed schedule/driver defect), replay and two controls. Aggregate
600 s and all per-cell limits are unchanged; failed setup cost is carried
forward. No identical retry. The next cell is simulate-002, and positive
replay/control input paths are changed to that successful cell's trace.

## Constraint syntax correction, before simulate-003

simulate-002 compiled the parsed XML but UPPAAL rejected the receipt guard's
nested boolean/clock disjunction as a constraint used in a boolean precondition.
No transitions were executed. Raw failed XML/logs remain in simulate-002.
The only request emitted by this composition is strict UAV. Its exact receipt
requirement is therefore emitted as a conjunction (strict freshness/update
classes, sample_age<5, service_age<=40), with clock-free identity/quality tests.
Bad identity/quality and stale receipt now have separate failure edges, without
negating a clock constraint. This is a compiler encoding correction for the
same strict-UAV contract, not a weaker age predicate. New model hash required.

Total setup cost so far: 4.4984719 s. At most seven engine cells now include
the two retained compile-readiness errors, up to two actual simulations,
one replay and two controls. Aggregate cap remains 600 s; all per-cell caps
unchanged. The next simulation is simulate-003. No query run or old campaign
budget is introduced by this specific correction.

## Directed schedule correction, before simulate-004

simulate-003 compiled the full candidate and accepted 35 transitions, then
returned schedule_exhausted: waypoint 35 requested input edge 15 after edge
16; actual enabled input edge was 17. A substring rewrite of the historical
failure spine accidentally changed `20 17 0` when replacing `0 17` with the
healthy channel edge `0 15`. The corrected spine changes this exact waypoint
only. It also explicitly advances B_KPI Fresh->Stale (edge 48) at historical
sample age 5, required before the measuring job can finish after global time
10; the candidate result sample's own clock is independent. No model, inputs,
limits, previous run or semantic result changes. This is the second and last
actual directed simulation under the fixed protocol. Its input is
spine-corrected.tsv; replay/controls use runs/simulate-004/trace.xtr if successful.

## Inherited timer maintenance, before simulate-005

simulate-004 compiled and reached admitted APP and JobMeasuring in 64 legal
transitions. Next epoch was unavailable because inherited B_KPI Fresh has
p<=1 and m<=1 even with no messages pending. Its enabled edge 55 resets idle
m; idle p resets by edge 52. These mandatory maintenance transitions were
missing from the witness selector, not from the model. Source locations and
full zones in the retained prefix identify the restriction at global time
[5,6]. No candidate clock/input changes are justified by this result.

One additional directed simulation is concretely justified: the selector may
advance only enabled B_KPI idle timer resets (52/55 Fresh, 58/61 Stale,
64/67 Expired) when the next waypoint is unavailable; the waypoint stays
pending. The spine also completes the existing SDN monitor's fresh collection
(10:2,10:5) and takes the original no-fault branch (22:9) in [12,13]. These
are engine transitions and every inserted step is exported/audited. No
background simulation state is synthesized or clock reset assigned by the
harness. Explicit global source/input/model hashes remain unchanged except
for the selector and spine hashes.

Revised fixed maximum: eight engine cells (two retained compile errors,
three directed simulations, one replay, two controls), 600 s aggregate and
unchanged per-cell/node/path/memory limits. This third actual simulation has
one diagnosed added capability, not a retry of the same strategy. The only
new command is run.py --cell simulate --name simulate-005 --input
spine-maintenance.tsv (relative to the candidate directory). On success,
replay/controls consume runs/simulate-005/trace.xtr. If this strategy remains
inconclusive, preserve the diagnostic result; no further search campaign.

Pre-simulate-005 review correction: admission rejection/timeout edges also
require the candidate request to remain active, so they cannot overwrite
an already recorded cancellation with admission rejection. Original active
admission loss/timeout behavior is preserved. Completion-safety query now
also checks the immutable payload predicate and admitted/transport IDs.
This creates a new candidate model/query hash before the next cell; old
simulate-003/004 XML is saved with those cells. No old witness is transferred.

## Strict freshness boundary control and targeted delayed acquisition

simulate-005 reached a real matching stored result, queue insertion, MAC
service, transmission and APP receipt in 100 transitions. The endpoint was
ServiceFailed (outcome 3), not Completed: sample measured at t=10 and received
at t=15 had age exactly 5. This is the intended strict rejection boundary.
The goal search unwound until its branch cap and recorded status=error;
its full engine-selected partial XTR and endpoint remain diagnostic, with
no property verdict or success claim.

The exact scheduling cause is visible in zones: the pending B_KPI idle m
reset at t=5 forced job start at precisely 5 when chosen before that reset.
Likewise idle p/m resets at t=10 forced immediate acquisition before reset.
One targeted final positive simulation moves the enabled m reset (27:55)
before job start, and takes idle p/m resets (27:58,27:61) after Fresh->Stale,
before acquisition. This permits later measuring/receipt in consistent zones;
it does not alter model clocks, sample quality, classes, strict <5 or <=40.
The difference is three concrete real transitions in spine-fresh.tsv.

Maximum nine cells now includes two setup failures, four actual simulations,
one replay and two controls. The only extra execution is simulate-006 with
spine-fresh.tsv, justified by the observed equality control; no identical
retry. Per-cell and aggregate 600 s cap unchanged. On success all replay
commands use runs/simulate-006/trace.xtr. No further strategy sweep is planned.
