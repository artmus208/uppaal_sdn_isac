# Service reachability diagnostic — Issue #70

Owner: vadimnbkg. Independent reviewer/integrator: artmus208 / user-integrator.
Scope: `evidence/scalability/service-reachability-20260929/**` only.
Base: PR #69, `a51a77e7852aee514bb0217a17d970fcf94cb704`.
User accepted that unmerged candidate as input specifically for this diagnostic;
this is not acceptance of the family, Gate 1 or P4.

One fixed campaign tests the ten existing `E<> family_grant_i` queries for
N=1..4, ascending N/i. Exact models/queries and supporting inputs are pinned in
inputs.json. They are never regenerated or modified. Existing deterministic DFS
runs timed out; random DFS (`-o 2`, seed 20260929) changes traversal only, with
exhaustive symbolic exploration and compact DBM retained. No concrete-state
random heuristic, fairness, priorities, reduction or model change is added.
Each entity may have a separate witness. A grant is an abstract opportunity,
including possible selection of an absorbing overflow queue, not useful packet
delivery, ACK, fairness or SLA. Timeouts establish no reachability verdict.

Limits: 30 s per query, native sampled 2 GiB memory stop, 420 s aggregate verifier
wall time including 10 s metadata calls; one attempt per query, no retries or
seed sweep. Native free RAM must be at least 3 GiB before every process.
Monitoring/license/parser/unexpected-verdict failures stop the campaign;
independent cells continue after timeout/memory limit. End-to-end time includes
loading and trace writing. Sampling is a stop threshold, not an OS allocation cap.

`monitor.ps1` is byte-identical to the #68 implementation. The runner reuses
pinned #68 Python monitor helpers. Controls exercise normal completion, timeout,
measured-memory stop and child reaping on the current host, before verification.

From a clean committed checkout on WSL with native Windows UPPAAL:

```sh
python3 -B evidence/scalability/service-reachability-20260929/runner.py pins
python3 -B evidence/scalability/service-reachability-20260929/runner.py controls
# Commit/export controls and source before the campaign.
python3 -B evidence/scalability/service-reachability-20260929/runner.py run --verifyta /mnt/d/UPPAAL/app/bin/verifyta.exe
```

Output directories are immutable. These commands launch the one planned campaign;
reproduction of verifier attempts requires a separately authorized scope/budget.
For read-only reproduction use input and evidence audits. All exact commands,
actual version, hashes, clean source commit, per-run hardware, status/verdict,
resource samples, stdout/stderr and trace availability are retained. Existing
results from #68 and historical P3 remain unchanged. Acceptance is pending.
