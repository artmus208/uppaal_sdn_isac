# SDN Property Report

| Property | Category | Query | Result | Interpretation |
|---|---|---|---|---|
| `deadlock_free` | `safety` | `A[] not deadlock` | not_run | closed SDN/RIC model has no deadlocks |
| `rule_invariant` | `timing` | `A[] (A_RULE.RuleInstallPending imply c_rule <= D_rule_install)` | not_run | rule install pending respects deadline invariant |
| `stale_no_optimistic` | `safety` | `A[] (telemetryClass == TEL_STALE imply !optimistic_reconfig)` | not_run | stale telemetry blocks optimistic reconfiguration |
| `missing_no_optimistic` | `safety` | `A[] (telemetryClass == TEL_MISSING imply !optimistic_reconfig)` | not_run | missing telemetry blocks optimistic reconfiguration |
| `recovery_failure_report` | `safety` | `A[] (recoveryClass == REC_FAILED imply failure_report_sent)` | not_run | recovery failure is explicit |
| `ObsRuleMiss` | `observer` | `A[] not ObsRuleMiss.Violation` | not_run | rule miss has bounded explicit outcome |
| `ObsRecovery` | `observer` | `A[] not ObsRecovery.Violation` | not_run | recovery has bounded explicit outcome |
| `ObsAdmission` | `observer` | `A[] not ObsAdmission.Violation` | not_run | admission has bounded service outcome |
| `ObsStaleTelemetry` | `observer` | `A[] not ObsStaleTelemetry.Violation` | not_run | stale/missing telemetry never enables optimistic reconfiguration |
| `reach_policy_evaluate` | `reachability` | `E<> A_POLICY.Evaluate` | not_run | policy evaluation is reachable |
| `reach_rule_timeout` | `reachability` | `E<> A_RULE.RuleTimeout` | not_run | rule timeout path is reachable |
| `reach_recovery_failed` | `reachability` | `E<> A_REC.RecoveryFailed` | not_run | recovery failure path is reachable |

Generated query lines: 13.
