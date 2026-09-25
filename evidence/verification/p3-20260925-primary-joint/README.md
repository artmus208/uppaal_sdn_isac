# Joint primary-attempt prerequisites and receiver readiness

This is a supplemental diagnostic for Issue #39/P3. It uses the exact frozen
model and does not add queries to the frozen selected-query pack.

Run `p3-20260925-primary-joint-001` used symbolic randomized DFS, seed
20260925, compact DBM, diagnostic traces, one process at a time, 60 seconds per
query and the existing sampled 2 GiB working-set limit. Model SHA256 is
`592678ed678ce8f70cf278f542e48bd2bb739969b53a962423d3e63f91e3e1e2`.

| Diagnostic | Formula | Result |
| --- | --- | --- |
| joint-prerequisites | `E<> (FailureDetected && reconfig_allowed && (standby || alternative))` | `success/satisfied`, 9.3879618 s |
| standby-receiver | same plus `sdn_standby_available && boundary_B_POLICY_0.Idle` | `timeout/null`, 60.0819804 s |
| alternative-receiver | same plus `sdn_alternative_config_exists` and a fault-boundary idle receiver | `timeout/null`, 60.0561174 s |

The first result proves that a reachable state can simultaneously have an
active recovery episode, a permitted reconfiguration policy and at least one
available standby/alternative configuration. The two receiver formulas did
not finish; their timeouts do not show that either receiver condition is
unreachable.

The readiness predicates are conservative proxies for the actual binary
channels: `bus_rec_policy_request!` is received by `Boundary_B_POLICY.Idle`,
while `bus_rec_flow_request!` is received by the fault-boundary idle locations.
An actual primary-dispatch witness must still execute the synchronized edge and
pass its receiver guard/update/target-invariant checks. This diagnostic does
not establish primary dispatch, two attempts, recovery completion or deadlock
freedom.

Raw files are archived in `evidence/verification/runs/` and metadata is under
`evidence/verification/p3-20260923/p3-20260925-primary-joint-001/`. Reproduce
the integrity check with:

```sh
python3 evidence/verification/p3-20260925-primary-joint/audit.py
```

The run was produced from clean source commit
`5b601846966cc44ad7c13110b231089745afa76a`; actual UPPAAL version, hardware,
parameters, vector and exact commands are in the archived run metadata. No
model, runner, manuscript, baseline or frozen query was changed.

