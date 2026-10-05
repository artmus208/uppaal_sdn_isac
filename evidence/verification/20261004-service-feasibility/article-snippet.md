# Proposed article and reviewer text — not applied to the manuscript

## Article paragraph

We separate truthful completion from successful-service feasibility. For the
fixed one-request UAV model, let a result be inserted at FIFO rank r, and denote
by e its age at insertion, by phi the delay to the first subsequent service
decision, by k the number of skipped decisions before dispatch, by l the delay
from dispatch to transmission attempt, and by b the attempt-to-receipt delay.
Consecutive service decisions are separated by T=5 abstract time units. Along
a history containing dispatch and receipt, the receipt age is
e+phi+(r-1+k)T+l+b. The strict freshness requirement is an age below F=5.
Consequently, successful receipt requires r=1, no skipped decision, and
e+phi+l+b<5. In particular, inserting the result at rank two or greater cannot
lead to fresh successful receipt, irrespective of later eventual service.
This implication does not assert initial-state reachability of each rank.

A separate graph-and-clock argument establishes that every time-divergent
execution containing a request emission enters an absorbing application terminal
location by request age 40. Pending admission is bounded by 15, accepted locations
by service age 40, and neither clock is reset after emission. Terminal outcomes
include rejection, failure, timeout and cancellation as well as success. The
result does not establish that every finite prefix admits a time-divergent
continuation, and does not cover finite deadlocks or infinite bounded-time
executions. Both results are fixed-model mathematical arguments supported by
source-premise audits, not new exhaustive UPPAAL verdicts.

## Reviewer response candidate

We have made the successful-service assumptions quantitative and distinguished
them from the correctness of an already received result. The new fixed-model
analysis derives a FIFO freshness obstruction: service period and strict
freshness bound are both five, so one preceding token already consumes the whole
freshness budget. A capacity-four queue therefore does not imply that all its
results can meet the freshness contract. For a result inserted first, queue
phase, enqueue latency, dispatch-to-attempt delay and transport delay must jointly
remain below five; eventual fairness alone supplies no such bound.

We additionally give a conditional terminal-outcome bound on time-divergent
executions. This bound allows unsuccessful terminal outcomes and cannot be used
to exclude deadlock or Zeno behavior, or to replace an unresolved unconditional
bounded-response query. The proof package provides the exact XML/manifest pins,
complete relevant writer inventory, graph obligations and mutation controls.
No baseline semantics or historical run verdict has been changed.

## Claim disposition

These are proposed integration paragraphs for the authorized P9 process.
Supporting C02/C03/C04/C05 evidence is submitted; independent scientific acceptance
is pending. No requirement, P3 milestone or gate is self-closed.
