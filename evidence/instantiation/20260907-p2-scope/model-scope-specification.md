# P2 — Model instances, composition and abstraction

Issue [#17](https://github.com/artmus208/uppaal_sdn_isac/issues/17), Owner
`carwasher`; primary requirements R01, R02, R05, R06. This is a **candidate
specification**, not an implemented integrated model or an accepted P2 result.
Independent scientific review is pending. Input commit:
`7baa86e8d0d9eb2fc2df8d728a360c6b7cfb91bb` on `read`.

## Evidence boundary

`inventory.py` checks the exact bytes of 38 inputs against their Git blobs at
the input commit, constructs ten explicitly selected default-profile generator
variants in memory and parses four stored XMLs. `inventory.json` contains their
hashes, ordered process bindings, declarations, channel endpoints and structural
counts. Full edge/location records are included for the three generated default
models and stored APP. `inventory.md` is the readable projection. This is neither
an UPPAAL syntax/type check nor model checking; the parser covers the explicit
zero-argument instantiation syntax of these inputs and rejects unsupported forms.

The baseline manifest hash is
`89b8d6f520546c873649643b3cf90fd80f58e4458a443832369e3d1d28bf719a`.
It still describes a historical dirty candidate and has `frozen: false`.
Pinning current source bytes here does not supersede that baseline. P1's package
is merged through PR #16 but scientific acceptance in Issue #15 remains pending.

## R01 — What is actually instantiated

| Surface | Core processes | Environment/stubs | Observers | Total |
|---|---:|---:|---:|---:|
| Generated PHY, default with observers | 5 | 4 | 3 | 12 |
| Generated MAC, default with observers | 5 | 1 | 5 | 11 |
| Generated SDN, default with observers | 6 | 1 | 6 | 13 |
| Stored APP | 4 | 4 | 8 | 16 |

PHY core is A_CH/A_SIG/A_BM/A_SQ/A_PH; MAC core is
A_SCH/A_Q/A_BUF/A_RSRC/A_MAC_AGG; SDN core is
A_MON/A_RISK/A_POLICY/A_RULE/A_REC/A_SDN_AGG. APP binds Req/Sla/Crit/Agg to
A_REQ/A_SLA/A_CRIT/A_SVC_AGG. Crit and Agg each have one location and **zero
transitions**, so their names cannot establish implemented criticality or
aggregation behavior. Other APP processes are an SDN stub, demand environment,
always-good KPI stub and report sink. Exact bindings are in the inventory.

Every listed process has one explicit zero-argument instance. None of these
system definitions parameterizes a base-station/device population or provides a
network topology. Five PHY automata are five cooperating functions, not five
radios. The APP request builder chooses SVC_UAV; this represents a service class,
not a simulated UAV trajectory or a count of UAV devices.

| Physical entity | Current representation | Proposed case-study interpretation |
|---|---|---|
| Base station | No dedicated node instance; aggregate PHY/MAC state | One serving BS, id 0 |
| Device/UAV | No device-indexed state; APP builds one UAV service request | One device, which is the one UAV; do not count it twice |
| Radio link | One shared set of PHY classes | One BS–UAV link, id 0 |
| Target | ENV_TARGET emits target events without target IDs | One sensing target, id 0 |
| Controller | One SDN functional composition | One SDN/RIC controller |
| Service | One Req/Sla pair, without session IDs | One service session, id 0 |
| Queue | Finite queue/buffer/load classes | One aggregate queue; no explicit packet queue |
| Handover destination | Hint/outcome only, no second cell | Zero explicit destination cells; no intercell performance claim |

## Candidate vector and reproducible construction contract

`instance-vector.json` is the machine-readable proposal. It retains 20 core
processes, adds eight boundary processes, and retains 22 observers: **50 proposed
processes**, not 50 currently implemented or verified processes. Keeping the two
APP placeholders makes their missing behavior visible. Optional SDN security and
extended PHY observers have count zero. Entity counts differ from process counts.

The vector gives ordered source surfaces, every retained/removed instance,
entity bindings, interface timing assumptions and a naming rule. The construction
procedure for the separately scoped integrated implementation is:

1. Generate each layer with the explicit kwargs/profile in `inventory.json`;
   load APP from its pinned stored XML. Confirm each input hash before assembly.
2. Retain only the named instances, including the named observer groups. Remove
   all ten standalone environment/stub instances listed in the vector. In
   particular, MAC `minimal` is still closed and does not remove A_ENV_MAC.
3. Qualify instance names by `<group>_<original_process>_0`. Qualify layer
   symbols by layer and entity index; preserve references within each template
   using parsed identifiers, not unscoped string substitution. Keep template-local
   clocks local. Share symbols only through the explicit interface contract.
4. Implement the eight boundary templates and required endpoint adaptations in
   `interface-contract.md`. Retained templates are **inputs for adaptation**,
   not a claim that their present edges can be concatenated unchanged. Keep the
   existing layer-local decisions unless a disposition explicitly calls for review.
5. Initialize classes/flags from the pinned declarations, then apply the explicit
   interface startup state. All clocks start at zero. Emit the system groups in
   JSON order and instances in each `retain` order. Qualify observer queries to
   the new process names and endpoint clocks; retain a property-ID mapping.
6. Serialize the assembled XML, parameter set, instance vector and queries;
   record their separate hashes. Run reference/type checks and the applicable
   P2 regression suite before submitting the integrated artifact for review.

The JSON fixes a small, abstract one-session test configuration. Time constants
are in abstract clock units, with no seconds-per-unit assertion. Its default
layer constants and extra bus/input bounds are deliberate test assumptions, not
physical calibration. Their acceptance is an independent decision. Multiple
devices, packet arrivals and topology growth require a new vector, per-entity
storage and explicit shared-resource arbitration; copying the single global
state does not implement them.

## R02 — Composition findings

The inventory reproduces four same-name channel-kind conflicts: service_request,
service_accept, service_degraded and service_reject are broadcast in SDN but
binary in APP. Other blockers are structural:

- MAC has no receiving edge for sdn_policy_cmd. Its only sender is A_ENV_MAC;
  real SDN policy commands therefore cannot simply replace that environment.
- MAC mac_schedule_cmd/phy_ack have no same-name PHY endpoint. Their current
  partner is A_ENV_MAC. Scheduling success would otherwise be supplied by a stub.
- SDN A_RULE and A_SDN_AGG both receive the binary `ack`. A future shared ACK
  source needs distinct transaction kinds/endpoints to avoid acknowledging the
  wrong outstanding operation.
- PHY, MAC and SDN have overlapping global clock names, including c_report and
  c_rec. APP and SDN also share admission names. Equal spellings do not justify
  shared clocks, flags or enum codes; their reset owners differ.
- APP's good-KPI stub bypasses actual lower-layer quality. Two APP placeholders
  have no behavior. Service reconfiguration/termination reports currently end in
  a sink, rather than causing real controller/network actions.
- APP acceptance receivers test admissionClass/gAcceptDegraded in guards.
  An update performed only on the simultaneous SDN send cannot establish that
  receiver guard beforehand. Payload staging must precede the synchronization.

Under UPPAAL semantics, binary synchronization requires a sender and receiver;
broadcast may send without listeners and involves enabled receivers. Guards use
the pre-transition valuation; sender updates execute before receiver updates.
Thus unifying a channel declaration changes possible blocking and event loss.
These are semantic obligations, not formatting fixes.
[UPPAAL semantics](https://docs.uppaal.org/language-reference/system-description/semantics/).

The complete proposed ownership, staging, delivery and failure rules are in
`interface-contract.md`. All eight adapter/environment definitions there are
requirements for subsequent implementation, not existing automata.

## R05 — Detailed scheduler analysis

`scheduler-analysis.md` examines the existing MAC A_SCH: six locations, nine
edges, its two timing clocks, priority selection, timeout boundary and interaction
with the environment. It includes the exact edge table generated from XML and
the practical consequences of its current clock-reset points. This automaton is
small enough to inspect independently while exercising both report and command
interfaces. No reachability or deadline satisfaction is inferred from inspection.

## R06 — What abstraction bounds, and what it does not

The raw SINR, angle, delay/loss distributions, continuous motion, optimizer state
and packet lists are outside these automata. They become finite classes plus
finite mode/control flags. For A_SCH the policy guards read queue (5 values),
buffer (3), delay (4), resource and mapped resource (4 each), communication and
sensing demand (3 each), KPI freshness (3), and sensing-priority permission (2).
The Cartesian product of these **inputs alone** is 51,840 valuations. This is
an overcount of independent combinations, not the scheduler state space: the
locations, output flags, global peers and clocks are additional, and constraints
may exclude combinations. The ordered if/else chain returns one selected mode
per valuation even when several raw guards are true.

The default MAC has 37 syntactic locations and 65 edges over 11 processes;
minimal has 22 and 50 over six. The difference removes five observers, but the
generator still declares observer clocks and its bounded policy counter. A mode
name alone does not prove the verifier eliminated those variables or saved memory.
No explicit queue length or buffer capacity follows from these finite classes.

UPPAAL clocks have dense-time valuations. A finite location/enum inventory does
not count symbolic zones or establish practical verification cost. Plain `int`
is also bounded by the tool's default range; incrementing APP event counters
without an explicit horizon can exceed it and abort checking. Such counters must
be reviewed rather than described as harmless unbounded mathematics.
[UPPAAL types](https://docs.uppaal.org/language-reference/system-description/declarations/types/).

For a family of n independent identical discrete components with m possible
local discrete configurations, the unconstrained product has m^n combinations;
shared variables, synchronization and clock zones change the reachable symbolic
system. This elementary product estimate is not a scalability experiment. P4
must measure runtime, explored states and peak memory on accepted per-configuration
XMLs after Gate 1, with separate run IDs.

An abstraction's soundness needs a relation from concrete events to classes and
a demonstration that concrete steps/delays are represented under the stated
environment assumptions. Choosing a worse label, deleting observers, or having
fewer XML edges does not prove trace inclusion. P1 supplies proposed calibration
methods; this package supplies neither physical data nor an abstraction proof.

## Decisions and acceptance

`decisions.md` disposes of P1 inputs and records the implementation/review
obligations. R01/R02/R05/R06 are addressed as a specification; they are not marked
closed. The integrated XML, accepted interface contract and accepted instance
vector remain separate required P2 outputs before Gate 1. P3/P4 are not unblocked
by this report. No edits to the manuscript, generators or manifests are included.
