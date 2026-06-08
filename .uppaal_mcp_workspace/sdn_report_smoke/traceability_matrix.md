# SDN Traceability Matrix

| Claim | IR | UPPAAL artifact |
|---|---|---|
| `A_SDN = A_MON || A_RISK || A_POLICY || A_RULE || A_REC || A_SDN_AGG` | composition | `system A_MON, A_RISK, A_POLICY, A_RULE, A_REC, A_SDN_AGG` |
| `A_SYS_SDN = A_SDN || A_ENV_SDN` | closed system | `A_ENV_SDN` |
| SDN automaton `A_MON` | locations/guarantees | template `A_MON` |
| SDN automaton `A_RISK` | locations/guarantees | template `A_RISK` |
| SDN automaton `A_POLICY` | locations/guarantees | template `A_POLICY` |
| SDN automaton `A_RULE` | locations/guarantees | template `A_RULE` |
| SDN automaton `A_REC` | locations/guarantees | template `A_REC` |
| SDN automaton `A_SDN_AGG` | locations/guarantees | template `A_SDN_AGG` |
| bounded response `ObsRuleMiss` | observer | `A[] not ObsRuleMiss.Violation` |
| bounded response `ObsRecovery` | observer | `A[] not ObsRecovery.Violation` |
| bounded response `ObsAdmission` | observer | `A[] not ObsAdmission.Violation` |
| bounded response `ObsStaleTelemetry` | observer | `A[] not ObsStaleTelemetry.Violation` |
| bounded response `ObsCommandAck` | observer | `A[] not ObsCommandAck.Violation` |
| bounded response `ObsSensingDecision` | observer | `A[] not ObsSensingDecision.Violation` |
