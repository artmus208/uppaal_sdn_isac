# Proposed article/reviewer text

We analyzed the effect of the 22 explicit observer processes in the fixed
51-process N=1 UAV service-completion composition. The analysis separates 27
observer bookkeeping variables from production-visible state, retaining the
ACK and recovery recorders that occur in production guards. Observer updates
affect only bookkeeping state, and the five committed observer locations have
exhaustive, update-free, zero-time exits. Removing the observer processes while
preserving the remaining declarations, automata and relative process order
therefore preserves production-state reachability and safety up to finite
zero-time stuttering. The resulting diagnostic composition has 29 processes.

The correspondence supports both directions of transfer for the fixed
completion-safety predicate and other retained-state reachability predicates;
it supplies no new model-checking verdict. Deadlock requires a directional
statement: deadlock freedom of the observer-erased composition would imply
deadlock freedom of the monitored composition, while the converse can fail
because internal observer transitions can mask production deadlock. Ordinary
maximal-path liveness and statistical behavior are not transferred by this
finite-trace argument. A separate correspondence holds for retained,
stutter-insensitive properties under an explicitly time-divergent execution
convention, without asserting that every prefix admits such a continuation.

Finally, nonrestriction and error-detection adequacy are distinct obligations.
Polling observers do not necessarily start their local clocks at a production
event, unlike recorders updated at the event or synchronous broadcast receivers.
Accordingly, observer Violation predicates require their own event-correlation
and scheduling justification before being interpreted as end-to-end deadline
guarantees. The source-bound certificate, mutation controls and exact diagnostic
XML support independent review of these claims. The bounded native experiment
is reported separately in native-summary.md; its direct scope is the diagnostic
model and transfer still depends on independent acceptance of the proof.
