# Truthful UAV completion — Issue #108

For the exact frozen N=1 model, the package gives an inductive argument that
every reachable APP Completed state satisfies all 26 conjuncts of the accepted
completion-safety predicate. The strengthened invariant also makes the request
inactive, which preserves the receipt record through later activity.
A second argument traces success through actual request, admission, measurement,
enqueue, service, transmission and receipt events.

**Evidence class: mathematical argument plus static checks, pending independent
scientific acceptance.** No new UPPAAL execution. The original exhaustive
attempt remains timeout/null; the historical successful replay is separate.

Owner: vadimnbkg. Independent Reviewer/Integrator: artmus208.
Issue: https://github.com/artmus208/uppaal_sdn_isac/issues/108
Branch: codex/vadimnbkg/108-completion-safety-proof; target read.
Base: f0fcd770e3e6b93f99868b9116e4f0929f60d0fa.
Sole write scope: evidence/verification/20261004-completion-safety-proof/**.

Scientific input: uav-service-completion-r1-20261002, N=1, 51 processes,
one request/result without ID reuse; input commit
61386aa358805082b705dcd00c8cbfde5fb98248.
Accepted dependencies and exact authority are listed in [sources.md](sources.md).
Manifest preparation flags are superseded by the published #84 decisions,
not modified here. #101 capacity and #89 bounded-response work remain separate.

Read [proof.md](proof.md), then inspect [certificate.json](certificate.json)
and [premises.json](premises.json). The checker scans 884 transitions and
77 helpers, identifies 29 writer sites and checks four completion entrances.
It is a specialized fixed-model premise checker, not a general verifier.
Never regenerate the premise capsule merely to accept a changed input.

From repository root, using Python >=3.10 with no third-party packages:

~~~text
python -B evidence/verification/20261004-completion-safety-proof/check.py --check
python -B evidence/verification/20261004-completion-safety-proof/tests.py
python -B evidence/verification/20261004-completion-safety-proof/audit_history.py --check
~~~

These commands are read-only apart from transient test fixtures. To emit
certificates into new review files, replace --check with --output <path>.
The outer checker pins exact model/query/manifest bytes. Mutation controls
call the inner premise checker below the byte gate to exercise actual entry,
writer, helper, synchronization, scope and graph assumptions.

[historical-evidence.json](historical-evidence.json) links the original
600.5930649-second completion-safety timeout and the saved 100-transition
success replay. Its audit checks archive hashes, model identity, event order,
source edge references and status separation; it is not a new engine replay.

[article-snippet.md](article-snippet.md) supplies English article and reviewer
text; [sources.md](sources.md) maps claims to artifacts. The article, baseline,
generators, existing evidence and all shared software remain unchanged.
Receipt freshness is measured from acquisition completion, not acquisition
start; live clocks may grow after success. No fairness, universal success,
arbitrary-N, reused-ID or physical calibration claim follows.

Full check commands, environment and original failures are retained in
checks/ and checks-final/. HANDOFF.md records validation disposition and the
publication/reproduction handoff. C01/C03/C04/C05, P3 milestones and scientific
gates are not self-accepted or closed by this package.
