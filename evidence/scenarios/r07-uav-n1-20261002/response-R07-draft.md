# Proposed response to R07 — not yet applied to the manuscript

We propose adding one concrete safety-critical UAV sensing failure scenario,
with a table tracing the sole request from its initial conditions through PHY
measurement, cross-layer KPI fan-out, MAC scheduling, SDN admission policy and
APP rejection/violation reporting. A failed detection-probability class with
consistent critical missed detection makes degraded sensing unsafe; the APP
boundary rejects SDN's degraded-admission proposal. The separate SLA automaton
reports the violation within its modeled response deadline on the observed path.

The unchanged full N=1 model contains 50 automata. UPPAAL generated a 63-transition
path and an independent replay accepted every transition from the genuine
initial state. Two altered endpoint expectations were rejected. The event table,
trace, commands, actual tool version, hashes and per-run resource evidence are
preserved in `evidence/scenarios/r07-uav-n1-20261002/`.

The proposed text distinguishes this feasible failure episode and its observed
reporting latency from universal SLA verification, successful service completion
and packet delivery. In particular, MAC JOINT selection and queue grant are not
APP completion. The material also explicitly identifies the missing packet-level
correlation and the retained sensing location/class inconsistency.

This is a candidate change, not a claim that the manuscript has already been
revised or that R07/P5 has been accepted. Independent acceptance still needs a
P5-applicable Gate 1 disposition, matching accepted P3 evidence/verification run
and confirmation of the reviewer assignment. The historical P3 results and
P4 family activation do not supply those decisions automatically.
