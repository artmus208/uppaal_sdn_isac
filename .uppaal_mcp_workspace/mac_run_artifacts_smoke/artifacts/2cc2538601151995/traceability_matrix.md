# MAC Traceability Matrix

| Claim | IR | UPPAAL artifact |
|---|---|---|
| `A_MAC = A_SCH || A_Q || A_BUF || A_RSRC || A_MAC_AGG` | composition | `system A_SCH, A_Q, A_BUF, A_RSRC, A_MAC_AGG` |
| `A_SYS_MAC = A_MAC || A_ENV_MAC` | closed system | `A_ENV_MAC` |
| MAC automaton `A_SCH` | locations/guarantees | template `A_SCH` |
| MAC automaton `A_Q` | locations/guarantees | template `A_Q` |
| MAC automaton `A_BUF` | locations/guarantees | template `A_BUF` |
| MAC automaton `A_RSRC` | locations/guarantees | template `A_RSRC` |
| MAC automaton `A_MAC_AGG` | locations/guarantees | template `A_MAC_AGG` |
| bounded response `ObsPhyAck` | observer | `A[] not ObsPhyAck.Violation` |
| bounded response `ObsQueueCritical` | observer | `A[] not ObsQueueCritical.Violation` |
| bounded response `ObsSensingCritical` | observer | `A[] not ObsSensingCritical.Violation` |
| bounded response `ObsBufferOverflow` | observer | `A[] not ObsBufferOverflow.Violation` |
| bounded response `ObsMacReportFreshness` | observer | `A[] not ObsMacReportFreshness.Violation` |
