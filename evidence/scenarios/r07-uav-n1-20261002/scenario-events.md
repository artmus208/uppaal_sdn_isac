# Selected events; full 63-step table in scenario-events.csv

Times are marginal bounds from reachable prefix DBMs, not independently chosen timestamps. The t=5 suffix is fixed consistently by the engine path. All units are abstract.

| Step | Reachable time | Event | Machine reference |
|---:|---|---|---|
| 1 | #time in [1,1] | The only demand creates a strict safety-critical UAV sensing request. | state_index=1 |
| 4 | #time in [1,1] | APP request sent; APP admission clock resets. Single service-context correlation begins. | state_index=4 |
| 6 | #time in [1,1] | Captured request forwarded to SDN Evaluate; decision clock resets. | state_index=6 |
| 15 | #time in [5,5] | SharedLoad chooses one queue arrival before its optional service epoch. | state_index=15 |
| 18 | #time in [5,5] | MAC tick starts KPI collection. | state_index=18 |
| 43 | #time in [5,5] | PHY input publishes PD_FAILED, MISS_CRITICAL and sensing-degraded scenario. | state_index=43 |
| 46 | #time in [5,5] | Channel report wakes sensing evaluation and PHY aggregate. | state_index=46 |
| 47 | #time in [5,5] | Sensing report sets degraded flag; highest_priority_SQ assigns SensingState=7. | state_index=47 |
| 48 | #time in [5,5] | Aggregate publishes PHY sensing-degraded KPI to boundary. | state_index=48 |
| 50 | #time in [5,5] | Fresh KPI maps detection/miss to APP and degradation to SDN; shared fan-out. | state_index=50 |
| 51 | #time in [5,5] | MAC consumes the PHY report and enters SelectMode. | state_index=51 |
| 52 | #time in [5,5] | SDN monitor receives PHY notification. Pending policy evaluation reads mapped telemetry. | state_index=52 |
| 53 | #time in [5,5] | APP KPI broadcast occurs while request is pending; A_REQ does not receive it in RequestPending. | state_index=53 |
| 54 | #time in [5,5] | Violation notification moves A_SLA to SLAViolated and resets response clock. | state_index=54 |
| 58 | #time in [5,5] | MAC selects JOINT. This is a scheduler choice, not successful APP service. | state_index=58 |
| 59 | #time in [5,5] | SDN sensing boost proposes degraded admission for the captured request. | state_index=59 |
| 60 | #time in [5,5] | Bridge maps ADM_DEGRADED to APP with sensing-failure reason. | state_index=60 |
| 61 | #time in [5,5] | Safety guard forbids degraded sensing and converts admission to rejected. | state_index=61 |
| 62 | #time in [5,5] | APP receives service_reject and clears pending; A_REQ reaches Rejected. | state_index=62 |
| 63 | #time in [5,5] | APP sends SLA violation report; environment records it. Pre-report elapsed=0 <= 3. | state_index=63 |

All references address `runs/replay001/steps.jsonl.gz`. The full CSV includes participating processes, channels and changed values/locations.
