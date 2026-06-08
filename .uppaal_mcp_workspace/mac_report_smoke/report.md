# MAC Property Report

| Property | Category | Query | Result | Interpretation |
|---|---|---|---|---|
| `deadlock_free` | `safety` | `A[] not deadlock` | not_run | closed MAC model has no deadlocks |
| `no_silent_accept` | `safety` | `A[] (resourceClass == RES_EXHAUSTED imply !silent_accept)` | not_run | exhausted resource is never silently accepted |
| `ack_invariant` | `timing` | `A[] (A_SCH.WaitPHYAck imply c_phy_ack <= D_phy_ack)` | not_run | wait-for-PHY-ack state respects its deadline |
| `ObsPhyAck` | `observer` | `A[] not ObsPhyAck.Violation` | not_run | PHY command is acked or failed by deadline |
| `ObsQueueCritical` | `observer` | `A[] not ObsQueueCritical.Violation` | not_run | critical queue gets bounded response |
| `ObsSensingCritical` | `observer` | `A[] not ObsSensingCritical.Violation` | not_run | critical sensing demand gets bounded response |
| `reach_schedule` | `reachability` | `E<> A_SCH.SelectMode` | not_run | scheduler can reach policy selection |
| `reach_report` | `reachability` | `E<> A_MAC_AGG.ReportSent` | not_run | MAC can emit report |

Generated query lines: 9.
