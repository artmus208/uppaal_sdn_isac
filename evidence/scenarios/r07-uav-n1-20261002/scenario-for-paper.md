# Candidate text for P9a: safety-critical UAV sensing rejected after PHY failure

Consider the full N=1 composition (50 timed automata), containing one UAV,
one abstract base station, one radio link, one sensing target and one service
context. The environment issues a safety-critical UAV sensing demand at
abstract time 1. APP constructs strict sensing requirements and forwards the
request through the admission boundary to SDN. The admission decision remains
pending while the PHY measurement period reaches time 5.

At time 5, an allowed input selects failed detection probability
(`PD_FAILED=2`), critical missed detection (`MISS_CRITICAL=2`) and the
sensing-degraded environment class. The channel report activates sensing
evaluation and the PHY aggregate; a sensing report sets the degraded flag,
and the aggregate publishes its KPI. The boundary maps the same KPI to MAC,
SDN and APP and emits separate notifications. MAC consumes the report and
selects JOINT mode, while SDN reads fresh telemetry with sensing degradation
pending and proposes degraded admission under its sensing-boost policy.
These are responses to shared telemetry, rather than a packet travelling
through a mandatory PHY–MAC–SDN–APP pipeline.

The APP admission boundary applies the safety rule

\[
G_{\mathrm{safe}} =
(\mathrm{criticality}\ne\mathrm{SAFETY})\lor
(\mathrm{sensingSLAOK}\land\mathrm{reason}=\mathrm{COMM\_LIMITED}).
\]

For this safety-critical request, failed detection and critical missed detection
make `sensingSLAOK` false. The boundary converts degraded admission to rejection,
and APP reaches `Rejected`, clearing its pending flag. In parallel, the mapped
KPI triggers APP's sensing-SLA violation predicate,

\[
\mathrm{PD\_FAILED}\lor\mathrm{MISS\_CRITICAL}
\;\Longrightarrow\;G_{\mathrm{SLA\ violation}},
\]

which is a sufficient clause of the implemented predicate, not its complete
definition. The violation notification moves the SLA automaton to
`SLAViolated` and resets its response clock. APP subsequently emits
`sla_violation_report`; the environment records the report and the SLA
automaton reaches `SLAReported`. The admission result and report both occur
at time 5 in the consistently reachable suffix: the request-to-rejection
interval is 4 abstract units, and violation-to-report latency is 0.

The response requirement represented by the SLA automaton is

\[
t_{\mathrm{report}}-t_{\mathrm{violation}}
\le D_{\mathrm{sla\_violation}}=3.
\]

Here the pre-report reachable clock zone fixes the elapsed time to zero,
so this particular response meets the modeled deadline. The corresponding
observer safety formula can be written as
`A[] !u0_obs_app_ObsViolation_0.Bad`, but it was not executed in this experiment
and is not part of the selected N=1 frozen query pack. The observed response
deadline must not be interpreted as a successful sensing SLA or as a bound
on packet delivery. Zero latency is allowed by the abstraction; the time units
have no accepted conversion to milliseconds.

Run `r07-80-20261002-sim001` generated 63 transitions from the genuine UPPAAL
initial state. Independent run `r07-80-20261002-replay001` accepted the exported
path, checking edge selections, synchronized participants, full discrete
vectors and nonempty reachable clock-zone intersections carried through the
prefix. Final-value and final-clock negative controls were rejected at step 63.
These runs use unchanged full-model SHA256
`5234cb087e5274798926d516dedc77d1f9542ea7df59cec39f83859771ce1385` and actual
UPPAAL 5.0.0 revision `714BA9DB36F49691`. All query verdicts are null.

This witness illustrates a complete cross-layer **failure episode**, ending in
APP rejection and recorded violation response. It establishes one feasible
execution, not a universal verification guarantee, physical validation or
successful service completion. The composition contains no explicit packets,
and its environment-generated `service_complete` signal is not causally tied
to the shared queue's grant. The trace also retains an abstraction inconsistency:
the sensing automaton enters `FreshnessLimited` while `SensingState=7`
(`SensingFailure`); the rejection explanation uses the explicit failed KPI
classes and safety guard, without assigning a stronger meaning to that location.

Suggested table: scenario-events.md (selected milestones), with the full
63-step table and machine references in scenario-events.csv. This text is a
candidate for independent P5/P9a review; final acceptance requires an applicable
Gate 1 and accepted P3 evidence matching the exact model and configuration.
