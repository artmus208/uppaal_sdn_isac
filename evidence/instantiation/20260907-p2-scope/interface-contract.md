# Candidate composition interface contract

Issue #17. Status: proposed, not implemented or accepted. Inputs and exact hashes
are in `inventory.json`; bindings and abstract constants in `instance-vector.json`.
The new boundary processes below replace the ten removed standalone environment
and stub instances. They must not run alongside those old instances. This document
specifies a finite test envelope, not a calibrated communication network.

## Namespace and ownership

Keep layer symbols separate (`phy_*[link]`, `mac_*[bs]`, `sdn_*[controller]`,
`app_*[service]`). For this candidate every index is 0. Each core component's
timing clock has its own owner; in particular PHY/SDN c_rec and PHY/MAC c_report
must remain distinct. Keep observer clocks separate, including local APP `x`.
Only the layer that makes a decision writes its mode/outcome. A bridge writes
an input mailbox or receiver-owned input field, never another layer's decision
flags or clocks except through an explicitly reviewed receiving transition.

| Data | Producer/decision owner | Receiver input owner / conversion |
|---|---|---|
| Physical finite samples, target events | E_PHY_INPUT | PHY input classes, assumption flags; PHY core computes derived classes |
| Queue/buffer/load classes | E_MAC_LOAD | MAC inputs; MAC core owns scheduleMode/macReason/pending flags |
| PHY report payload | PHY A_PH / child outputs | B_KPI snapshots; maps to MAC freshness/resource input and SDN telemetry input |
| MAC report payload | MAC reporting core | B_KPI snapshots; SDN receives mapped risk/degradation inputs |
| Controller policy | SDN A_POLICY/A_REC | B_POLICY mailbox; adapted MAC policy receiver sets permission/input flags |
| Service request fields | APP request builder | B_ADMISSION mailbox; explicit mapping to SDN admission inputs |
| Admission outcome | SDN policy | B_ADMISSION stages APP admissionClass/degradedReason before delivering response |
| Application KPI | B_KPI derives only from captured lower-layer payloads | APP freshness/quality fields; Req/Sla own local state and reporting flags |
| Rule/control ACK | E_FAULT for abstract dataplane; B_POLICY for lower control | Distinct SDN rule/controller receivers, not the current shared ack |

Existing multiple writers within one layer are not silently rewritten. A later
implementation must inspect their races (for example MAC reports) and give a
deterministic snapshot boundary. Shared type names do not imply identical enum
encodings: convert named values explicitly, reject unknown encodings.

## Channels and boundary routes

`local` below means namespaced to its layer. `bus` denotes a new boundary channel.
Every command/response is binary and carries a one-slot mailbox; reports are
broadcast within their publishing layer. Bridged receive/send is two separate
transitions. The sender publishes fields before the receiver's guard needs them.

| Logical route | Existing endpoint(s) | Proposed binding and payload |
|---|---|---|
| PHY report → MAC/SDN/APP | PHY A_PH `phy_kpi_report!`; MAC A_SCH and SDN A_MON/A_POLICY `phy_kpi_report?` | B_KPI receives local PHY broadcast, snapshots class/validity/age, then emits separate MAC/SDN report broadcasts and APP KPI notification |
| MAC report → SDN | MAC A_SCH/A_BUF/A_MAC_AGG `mac_report!`; SDN A_MON/A_POLICY `mac_report?` | B_KPI receives local MAC broadcast and publishes the SDN report after conversion |
| MAC schedule → PHY | MAC A_SCH `mac_schedule_cmd!`; no same-name PHY receiver | B_PHY_MAC accepts schedule mailbox, sequences relevant PHY configuration commands, then returns MAC `phy_ack!` only after command delivery |
| SDN policy → MAC | SDN A_SDN_AGG/A_REC `sdn_policy_cmd!`; MAC has no receiver | B_POLICY consumes typed control/recovery request; adapted MAC receiver accepts `bus_policy?`; ACK is controller-specific |
| APP request → SDN | APP Req binary `service_request!`; SDN A_POLICY broadcast receive | Keep APP leg binary. B_ADMISSION buffers one request; adapted SDN leg becomes binary admission request with payload mapping |
| SDN outcome → APP | SDN broadcasts accept/degraded/reject; APP binary receivers | Keep SDN output leg broadcast to B_ADMISSION. Stage APP fields, then send binary APP outcome; do not globally merge the conflicting declarations |
| Rule installation → abstract dataplane | SDN A_RULE flow_mod/forward_cmd/ack | E_FAULT consumes flow_mod/forward_cmd and can return typed `rule_ack`; may withhold it to exercise existing timeout paths |
| Recovery / fault | SDN A_REC link_failure/node_failure/rollback_cmd | E_FAULT provides at most one fault, handles rollback and reports; B_POLICY handles recovery-policy delivery |
| PHY measurement / target | measure_tick, target_detected | E_PHY_INPUT owns finite sample changes and periodic trigger, replacing ENV_CH/ENV_TARGET stimuli |
| PHY delivery notifications | mac_report_delivered, controller_report_delivered, aos_ctrl_expired | B_KPI supplies actual modeled delivery/age notifications; remove independent ENV_NET resets |
| APP lifecycle/reports | new_demand, service_complete, reports/reconfigure/terminate | E_SERVICE creates one request/finish event and records report outcomes; it does not pretend that report consumption implements reconfiguration |

The inventory enumerates all actual endpoints including unused channels. PHY
child reports and degradation broadcasts remain layer-local and retain observers.
PHY configuration inputs no longer used by the selected schedule envelope remain
explicitly disabled; list them in the implementation's model map rather than
adding a success-producing stub. Optional SDN security remains excluded.

## Boundary processes

Each is one new finite process. Initial state is Idle/Waiting with empty mailbox,
no outstanding request and no ACK. New local clocks start at zero. Delays below
use the abstract constants in the vector; committed staging states have no delay.
The source default initial core locations are preserved. Pending mailboxes cannot
be overwritten; attempting a second command records a protocol error and no ACK.

| Process | Required finite behavior |
|---|---|
| E_PHY_INPUT | Every T_input units select a finite input tuple and publish measure_tick when its receiver is ready; record a missed delivery at the deadline instead of blocking time. Emit a target event after updating target_seen input context. It writes only raw class/assumption inputs, never PHY outcomes. Values range over the declared finite input domains; no raw float conversion is used. |
| E_MAC_LOAD | Every T_mac_tick units choose queue, buffer, delay, drop, resource and demand classes independently within declared domains, then offer mac_tick. Record a missed tick if MAC is not ready. It never sends PHY ACK or fabricated PHY reports. |
| E_FAULT | Nondeterministically choose no fault, one rule miss, one link fault or one node fault in [12,13]. Offer once, then record delivered/dropped. For each accepted dataplane operation choose ACK within D_bus or loss. Consume failure/timeout/drop/rollback/forward reports with explicit outcome flags; availability is a finite input, not a topology algorithm. |
| E_SERVICE | Offer one new_demand at T_demand=1. Offer service_complete at T_complete=40. Record whether these broadcasts were consumed; no further requests. Consume the five binary report/control outputs used by the original Sink, recording warning/violation/reconfigure/degraded-accept/terminate separately. Termination also requests completion on a subsequent transition; reconfiguration is logged as unimplemented, not acknowledged as completed. |
| B_PHY_MAC | Idle → accept one MAC schedule and snapshot mode → send the mapped PHY commands in a fixed sequence → ACK MAC after all command handshakes, or record delivery failure at D_cmd with no ACK. Do not issue unsolicited ACK. Wait for outstanding MAC transaction to clear before accepting another. A late ACK is dropped. |
| B_POLICY | Receive distinct typed SDN control/recovery requests → snapshot policy → deliver bus_policy to a new MAC input receiver within D_bus or record loss. Return ctrl_ack only for delivered control requests; recovery has a separate completion indication. Do not acknowledge a rule operation. Serialize pending policy mailboxes. |
| B_ADMISSION | Accept APP request only when empty, stage SDN input, offer binary request within D_bus. On SDN outcome while awaiting that request, snapshot it. Stage APP outcome in a committed step, then offer binary response within D_bus. Timeout/loss leaves the request explicitly unresolved and triggers the new admission-timeout failure path required below. Ignore unsolicited SDN outcomes with a diagnostic flag. No second session. |
| B_KPI | Always be able to observe local broadcasts; maintain one latest sample mailbox per source. New sample overwrites an undelivered old sample with an explicit overwrite flag. Nondeterministically deliver each captured report within D_bus or record loss. Publish typed MAC/SDN/APP updates in fixed order and preserve sample age. Never create a good KPI solely because time elapsed. |

Sampling all enum combinations is an intentionally broad abstract environment.
It can include physically inconsistent tuples; do not claim an over-approximation
proof until a concrete-to-abstract relation is reviewed. Missed inputs, lost
reports and no-fault paths belong to the envelope. Sampling periods, single-fault
and one-session limits must be stated in every result using this vector.

## Finite mappings and failure semantics

The following are **proposed policy choices**, subject to independent review.
PHY waveform is fixed to the pinned default W_OFDM. For the single-link schedule
test, SCH_COMM requests waveform_config, SCH_SENS requests sensing_mode_cmd,
SCH_JOINT requests waveform_config then sensing_mode_cmd, and SCH_CONSTRAINED
requests power_cmd. Commands retain the default finite configuration payload and
set admissibility true only for that selected supported configuration. They model
configuration delivery, not optimization, throughput or guaranteed sensing
improvement. SCH_IDLE is not a successful schedule: reject it with no ACK.
PHY_ACK means completion of those command handshakes, never completed beam
recovery or satisfaction of an SLA. D_cmd=1 is an extra model assumption.

SDN POL_COMM_PRIO maps permissions to (comm=true, sensing=false), POL_SENS_BOOST
to (false,true), POL_NORMAL/POL_REROUTE to (true,true), and POL_CONSTRAINED/
POL_REJECT to (false,false). Rejection also carries the typed policy/reason.
An adapted MAC receiving transition must consume that input; the current
generator has no such transition. Mapping permissions does not implement rerouting.

At APP→SDN request staging, critical sensing requirements set a sensing-demand
input and communication-critical requirements set a communication input. Do not
reuse service_request_pending across layers: the APP flag tracks transport and
the SDN flag tracks evaluation. Existing gPolCommPrio depends only on SDN's pending
flag, so supporting actual service requirements needs a separately reviewed
policy extension. Until then the one UAV request is an abstract admission trigger
with preserved payload, not proof that the controller enforces its requirements.

Accept/degraded/reject sets APP admissionClass to the matching ADM value in a
separate staging transition. For degraded outcome map missing/stale information
to DEG_STALE, resource limitation to DEG_RESOURCE_LIMITED and otherwise to
DEG_COMM_LIMITED; preserve the original SDN reason in the mailbox. Use
gSafetyAllowsDegraded before offering degraded delivery; if APP cannot accept the
degradation, deliver a rejection with preserved reason. Outcome availability must
not depend on a write performed after the receiving guard is evaluated.

For quality payloads map PHY PdClass/RfaClass/AccClass/CoverageClass by named
OK/LOW-or-LIMITED/FAILED-or-CRITICAL values to APP pd/false-alarm/accuracy/coverage
domains. Map Rfa HIGH to FA_HIGH, CRITICAL to FA_CRITICAL. A missed-detection
class is an independent E_PHY_INPUT finite measurement, constrained to reject
the two contradictions in APP detection_kpi_consistent; do not manufacture it
from a probability-of-detection value. MAC mappedResourceClass is RES_EXHAUSTED
for STARVED, RES_TIGHT for LIMITED, otherwise the E_MAC_LOAD resource class.

Age is time since modeled sample generation, including bridge delay. Publish
FRESH for age <5, STALE for 5<=age<10, EXPIRED for age>=10. Before the first
sample validity=false; MAC input is KPI_MISSING, SDN is TEL_MISSING, APP is
DET_EXPIRED. For a valid sample the MAC freshness mapping is FRESH/STALE/MISSING
and SDN is FRESH/STALE/MISSING for the three respective age bands. A valid recent
but bad-quality sample is fresh with bad quality; do not equate failure and age.
Explicit validity and age clocks are required because existing receipt resets
cannot implement this contract. APP receipt resets of age_sensing must be replaced
or complemented by source-age storage and an explicit expiry outcome.

Boundary deadlines do not justify inserting successful core transitions. At
failure the bridge records loss; the actual consumer timeout/rejection must
remain possible. APP RequestPending currently has an invariant but no dedicated
timeout edge, so it needs an explicit unresolved/admission-failure outcome in the
integrated implementation. Similarly, a receiver unavailable at a deadline must
not time-lock the environment. At equality both success and timeout may be
enabled unless a reviewed guard partition explicitly establishes precedence.

## Clock, observer and counter obligations

Start admission transport at APP request emission, controller evaluation at its
receipt, and MAC ACK timing at the explicitly chosen endpoint. The current MAC
clock starts before command send; `scheduler-analysis.md` explains why a reset
change is semantic. Do not add stage bounds blindly when stages overlap. The
one-unit bridge proposal does not prove any end-to-end deadline is met.

Split SDN ack into rule_ack and ctrl_ack, with pending-kind checks and no late
cross-transaction delivery. Namespace and adapt existing observers to these
endpoints. An observer must not compete with a functional binary receiver:
use a separate monitoring event or receiver-updated pending flags. Broadcast
receiver updates follow system order; specify that order, and do not let observers
write functional state. [UPPAAL edges](https://docs.uppaal.org/language-reference/system-description/templates/edges/).

The eight APP sequence counters are plain int in the input XML. One request
does not bound all repeated KPI/violation reports. Replace each counter-based
observer trigger with an explicitly reviewed event/pending protocol, or introduce
a proved bound for this finite-horizon experiment. Do not silently wrap or saturate
a counter still used to distinguish new events. Core zero-time self loops also
remain possible; the periodic environment does not prove time divergence.

## Required implementation review

Check endpoint coverage for every retained edge; initial validity/age and clocks;
single-writer boundary fields; enum mapping totality; request/ACK correlation;
all deadline equality cases; absence of stub-generated success; APP placeholder
and lifecycle scope; query remapping and observer noninterference. Record any
semantic deviation from the inputs. These checks must precede a frozen baseline.
This specification supplies the candidate decisions and exposes missing behavior;
it supplies no integrated XML, executed adapter or verified property.
