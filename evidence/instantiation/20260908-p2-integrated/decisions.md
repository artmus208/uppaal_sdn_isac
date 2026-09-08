# Candidate implementation decisions and review obligations

Issue #19 implements the merged proposed contract from #17; it does not accept
that contract scientifically. `composition.json/adaptations` records exact
before/after copies of changed retained XML and declarations. Original source
files are neither overwritten nor silently regenerated.

## Composition and lexical scope

One explicit instance of every retained process is ordered exactly as in the
specification vector. Process identifiers use the specified group/original/zero
format. Global declarations, function identifiers, parameters, template locals
and edge selections undergo an injective token renaming with a layer prefix.
Renaming a local and its shadowed global identically preserves their original
lexical scope. Identifier suffixes, comments and strings are not substring-edited;
query location members remain unchanged. The pinned scalar dialect is the
supported input, not an arbitrary UPPAAL source-to-source transformation service.

Source generation must match the specification's model and query hashes before
adaptation. An installed generator is allowed only when its Python bytes match
the pinned source. All 38 audited files and both specification JSON inputs are
read. The user-authorized scoped continuation in #19 classifies only AGENTS.md
as operational context: context_document_hashes retains pinned and actual hashes,
while all other files and both specification JSON pins remain strictly enforced.
Scientific manifests, baseline, validation inputs and model sources are not
exempted. The audit checks the recorded context hashes too; historical runs must
be regenerated from their own source checkpoint, not rewritten using this one.
Implementation file hashes are separately recorded; their sorted
hash/path records define `generator_hash`.

## Command and policy transactions

`B_PHY_MAC` retains one schedule snapshot: COMM sends waveform_config, SENS sends
sensing_mode_cmd, JOINT sends those two commands in that order, CONSTRAINED sends
power_cmd. IDLE records failure. A command handshake represents delivery of the
pinned supported configuration; it does not mean beam recovery or SLA success.
The core MAC ACK clock now resets on command emission. After D_cmd=1 a pending
bridge records loss without ACK. A late or unsolicited ACK cannot leave the
bridge; a repeated command while busy records protocol_error without overwriting
the mailbox. A separate transaction-open flag releases the bridge after the old
MAC transaction closes, even if scheduling a later command has already begun.

SDN's single shared ACK is split into rule, controller-policy, recovery-policy,
recovery-flow and rollback ACKs. Each has one functional receiver. Recovery no
longer writes the aggregate controller's command_pending flag. `B_POLICY` stages
the permission mapping before a binary MAC input handshake; only a delivered
request can produce its matching ACK. Separate transaction-open flags distinguish
an old timed-out transport from a newly pending policy decision.

The dataplane environment retains an explicit flow_mod → forward_cmd → rule_ack
sequence and independent loss selection. Recovery flow/rollback requests have
typed responses. Failure, timeout, drop, resource-reject and forward/rollback
outcomes have separate finite diagnostic flags. These finite abstract operations
do not implement routing or placement algorithms.

## Admission and application lifecycle

`B_ADMISSION` snapshots every request field into a finite mailbox, then offers a
binary SDN request. The existing policy still treats it as an abstract admission
trigger: storing strict UAV requirements does not prove the controller enforces
them. This limitation was explicit in the specification. An output is correlated
using the pending request flag in the pre-state; a diagnostic tag written on the
emitting transition is not used as its receiving guard.

SDN outcomes are broadcast to the bridge, then APP outcome/reason fields are
staged on a separate committed transition before the binary APP response. Safety
can turn a degraded outcome into rejection while preserving the original SDN
reason. Unsolicited outcomes are recorded. Transport loss leaves APP pending
until a new explicit RequestPending → Rejected timeout at its original deadline.
The admission observer requires an actual resolved pending flag as well as an
outcome; staged payload alone is not delivery.

The request builder no longer manufactures good sensing KPI values. Accepted
states no longer use receipt-reset age_sensing invariants; B_KPI owns source-age
classification and expiry. The SLA monitor can re-enter its reporting states
after a previous report. E_SERVICE offers one demand at 1 and completion at 40,
records delivered/dropped broadcasts and the five report/control outputs.
Termination requests completion in a later transition. Reconfiguration is logged
as unimplemented. APP Crit/Agg are deliberately retained placeholders.

## Sampling, age and delivery

E_PHY_INPUT selects bounded classes in private committed staging locations and
publishes the whole tuple atomically. This avoids both partial visible samples and
the compiler's combinatorial expansion of a single enormous select list. STALE
and SUSPECTED classes are retained. Missed detection excludes PD_OK/MISS_CRITICAL
and PD_FAILED/MISS_OK. Scenario labels are independent finite inputs because the
retained PHY automata already use them; their relationship to detailed class
values remains an unaccepted source-model limitation.

Sampling is attempted every five units. A busy classifier/report pipeline may
skip a PHY sample; its old source-age clock then continues. MAC independently
samples queue/buffer/delay/drop/resource/demand classes every five units. A missing
binary tick receiver records loss and does not block time. Source clocks reset at
sample generation, not at bridge reception. A new generation invalidates pending
older transport and records overwrite; old data cannot inherit the new clock's
freshness. This is a conservative implementation choice requiring review: old
delivered PHY data is marked missing until a new report is delivered.

B_KPI can observe both local report broadcasts in every location. It snapshots
their finite payloads, retains one latest mailbox per source and records overwrite
or delivery loss. One-unit mailbox deadlines are enforced by bounded local clocks;
empty-mailbox clock housekeeping also permits time to continue. PHY delivery
stages MAC/SDN/APP fields and emits their notifications in order. Freshness is
source age <5, 5<=age<10, and >=10; bad quality does not become stale solely because
it is bad. Before a report, validity is false. PHY expiry has an explicit event.
MAC report delivery updates SDN slice inputs from the captured resource/queue
classes; the source-age clock is retained in the map, while SDN's shared telemetry
freshness follows the PHY sensing source. This simplified telemetry aggregation
requires independent review before treating it as a multi-source network model.

Lower-layer delivery notices are separate binary offers in committed stages,
with an explicit immediate-drop alternative if the peer cannot receive. The
notices do not delay a completed KPI fan-out past an age boundary. Report fan-out
is abstract and loss may affect the whole captured report. A new raw sample can
invalidate pending transport during a committed fan-out; these atomic ordering
choices and the specification's single-slot assumptions require review.

## Observer semantics and claim limits

APP's eight incrementing event counters become boolean oldest-outstanding-event
latches with producer-reset age clocks. A repeated event while outstanding does
not reset the oldest deadline. Observers clear only monitoring latches on a
response; they never write functional layer state. Several events before one
response are coalesced rather than independently counted. This removes overflow
without pretending to preserve arbitrary counter-based trace semantics.

PHY observers receive a broadcast and classify timing in a committed location;
late responses go to Violation. This separates receipt from clock tests and keeps
the observer out of binary receiver competition. Other retained observer
limitations, including guard-polled triggers and source-policy decisions, are not
a proof of noninterference or completeness. Candidate queries retain a mapping
to their original formulas; the changed environment/observer semantics must be
considered for every eventual claim.

UPPAAL language references checked on 2026-09-08:
[edge updates and pre-state guards](https://docs.uppaal.org/language-reference/system-description/templates/edges/),
[verifyta command-line help](https://docs.uppaal.org/toolsandapi/verifyta/).
Installed `verifyta --help` supplies the recorded UPPAAL_COMPILE_ONLY contract.
These references support language interpretation; only saved compile diagnostics
support the reported syntax check. No state-space exploration, timed property
verdict, physical validation or Gate 1 acceptance is supplied by this package.
