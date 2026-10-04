# Integration-ready English text (proposed; independent acceptance pending)

For the frozen single-UAV, single-request completion model (51 processes), we
establish a safety property by induction over its timed transition system:
every reachable APP Completed state satisfies the complete request-correlated
receipt predicate. A successful entry requires an actual result-delivery
rendezvous, matching request and sample identities, recorded admission,
measurement, enqueue, dispatch and transmission, acceptable stored payload
quality, sample age below 5 and request age at most 40 abstract time units.
These age bounds concern the instant of receipt.

The proof has two obligations. First, the four entrances to Completed establish
all 26 conjuncts of the frozen completion-safety query and deactivate the
request. Second, Completed is absorbing, and a complete writer audit shows that
the receipt record is preserved by every subsequent action and delay. In
particular, a later termination notice preserves an inactive request's outcome.
The proof binds to the exact XML/query hashes, examines 884 transitions and 77
global helpers, and identifies 29 sites that can write the relevant state.
A specialized static checker validates entry implications and the reviewed
preservation premises; mutation controls reject changes that invalidate them.
It is not a general UPPAAL model checker or a proof-assistant certificate.

A separate event-history argument traces every successful completion through
actual request emission, admission, sensing, enqueueing, service, transmission
and receipt. The stored sample's age begins at acquisition completion. This
scope matters: the acquisition itself takes five abstract units, quality is
represented by accepted classes, and the model has no request-ID reuse. Neither
multi-request operation nor physical timing/accuracy is established.

The direct completion-safety search previously timed out after approximately
600.59 seconds and retains a null verdict. The new result is recorded as a
mathematical argument, separately from that inconclusive search and the existing
100-transition engine success replay. Truthful completion does not imply that
completion is inevitable: the original model retains loss, optional service,
rejection and timeout. In particular, at request age 40 successful receipt and
timeout remain nondeterministic alternatives. Independent review of the proof
is required before presenting it as accepted evidence.

# Suggested reviewer response

We have added a source-bound inductive argument for the full completion-safety
predicate, together with a closed writer inventory, causal-history argument,
reproducible premise checker and mutation controls. The text distinguishes
receipt-time bounds from clocks that continue advancing after completion.
The prior native timeout/null record is retained. This package supplies
mathematical evidence for the exact frozen N=1 model; it does not claim a new
exhaustive UPPAAL result, universal bounded response, or closure of the remaining
P3 requirements. Proposed placement: the verification/results discussion,
immediately after the frozen completion-model/query description; link the
full proof and input hashes as supplementary evidence.
