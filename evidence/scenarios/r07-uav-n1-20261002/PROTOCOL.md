# R07 candidate: directed symbolic simulation, Issue #80

Prepared 2026-10-02, starting at 04:30 Moscow (01:30 UTC). User explicitly
instructed executing `promts/02 10 2026.md`; this is new execution authorization
for candidate preparation, independent of the exhausted #78 campaigns. Accepted
limited P1/P2 scope and decisions are saved in decisions.json. This protocol
does not extend the P4 activation into final P5 Gate 1 acceptance.

Object: unchanged full N=1, 50 processes, baseline uav-family-r1-20260929.
Model: evidence/scalability/family-series-68/generated/n1/model.xml.
SHA256: 5234cb087e5274798926d516dedc77d1f9542ea7df59cec39f83859771ce1385.
Base: 91113a1b634f030c7e895f54f5c36a0b140d66eb, published read / merged #79.
Parameters and instance vector: corresponding generated/n1 JSON, hashes
f89f9bb0cbaff4a45440533aa273fc38f2d9efdd34b77309b59187c6c75b9a18 and
69b5105223a5dd3a2bae34513f6126416fdb15fad0b99a6b405f977332feddad.
One UAV, BS, radio link, sensing target and service session; zero explicit packets.
Shared capacity 1 per 5 abstract units, optional service, no fairness.

## Goal and method

Failure scenario: one safety-critical UAV request, PHY PD_FAILED=2 with consistent
MISS_CRITICAL=2, sensing-degraded input scenario=2; KPI publication fans out to
MAC, SDN, APP. Observe MAC consumption/selection, SDN sensing-boost admission
decision, safety filtering to APP rejection and recorded SLA violation report.

Exact final predicate:
`u0_app_Req_0.Rejected && !u0_app_service_request_pending &&
u0_app_admissionClass == 2 && u0_app_pdClass == 2 &&
u0_app_missedDetectionClass == 2 && u0_bus_violation_recorded &&
u0_app_sla_violation_report_sent && u0_bus_outcome_for_request &&
u0_bus_mac_report_consumed && u0_sdn_policyClass == 1`.
POL_SENS_BOOST=1 and ADM_REJECTED=2 must be checked against model declarations
before execution. Required historical milestones: demand, request forwarding,
PHY input/report, mapped KPI, MAC consumption and schedule choice, SDN decision,
APP safety filter/rejection and report. A report received before rejection still
belongs to this single service context; event ordering is read from the trace.

Engine.getInitialState and getTransitions are the sole sources of reachable
states. spine.tsv supplies primary edge/select preferences, derived from model
code and the old path's edge list; no old final state is imported. Enumerate all
engine successors, retain at most 4 matching successors per waypoint, depth first
with return to reachable prefixes. Maximum 256 expanded nodes, 128 path steps,
64 failed branches and 55 seconds per simulation cell. Save enabled edge keys,
selected full states and full DBMs, plus best partial XTR on failure.
Preferences choose a witness; they do not remove transitions from the model or
prove a universal property. No verifyta/model-checking query is executed:
query_hash=null and property_verdict=null.

Export engine-generated XTR; independently replay every saved edge, full discrete
state and reachable DBM intersection from the genuine initial state. Carry each
nonempty intersection forward. Two negative controls alter only the final expected
APP admission value (2 -> 1) and final expected clock zone (an untouched final
clock reset to zero -> one). Controls never alter XML. No exact times are selected
independently from zones: tables show symbolic bounds unless the entire path is
restricted consistently. Endpoint deadline is evaluated from the reachable
pre-report clock zone against D_sla_violation=3; this remains a path observation.

## Budget and lifecycle

Task cap 180 minutes from 01:30 UTC, finish by 04:30 UTC (07:30 Moscow), before
08:00 Moscow. Native campaign cap 600 seconds including probes/cleanup; at most
one initial simulation, one justified corrected simulation if failure identifies
a concrete schedule/driver defect, one replay and two negative controls. A change
to the strategy must be recorded in a protocol addendum and checkpoint before
its run. No identical retries, exhaustive searches or strategy sweeps.

Native Windows UPPAAL 5.0.0 engine with JDK17 via WSL; actual version is captured
from engine.getVersion for every cell. Per cell native timeout 60 seconds,
Java heap512 MiB, sampled owned-tree stop2 GiB, fresh native RAM >=3 GiB.
Reuse the read-only #78 native monitor/cleanup implementation through scoped
copies with the total budget and cell checks adapted for this campaign.
Process PID and creation time identify owned children; cleanup kills only the
owned tree, confirms termination, and retains monitor records. Python watchdog
reserves 20 seconds for cleanup. Failures, timeouts, partial traces and logs stay
in their original run directories. Unique run IDs `r07-80-20261002-<cell>`;
directories `runs/<cell>/` refuse overwrite. stdout/stderr, memory CSV, hardware,
commands and hashes are retained. Dense trace/log files may be losslessly archived
with original size/hash metadata. Protocol/source checkpoint precedes any launch.

Stop on goal or explicit node/branch/time/memory budget; stop campaign on model
hash drift, tool/license/lifecycle failure or wrong negative-control outcome.
No APP success, packet delivery, accepted verification run, R07 closure or P5
acceptance follows from simulation.
