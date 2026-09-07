# Reproducible P2 source inventory

Source commit: `7baa86e8d0d9eb2fc2df8d728a360c6b7cfb91bb`. Issue #17.

Counts below are XML syntax counts, not reachable states or verification results.

| Surface | Processes | Locations | Transitions |
|---|---:|---:|---:|
| generated:phy:with_observers | 12 | 57 | 269 |
| generated:phy:minimal | 9 | 48 | 258 |
| generated:phy:open_system | 8 | 53 | 245 |
| generated:phy:with_extended_observers | 16 | 69 | 281 |
| generated:mac:with_observers | 11 | 37 | 65 |
| generated:mac:minimal | 6 | 22 | 50 |
| generated:sdn:with_observers | 13 | 52 | 100 |
| generated:sdn:minimal | 7 | 35 | 84 |
| generated:sdn:open_system | 12 | 51 | 80 |
| generated:sdn:with_optional_sec | 14 | 56 | 105 |
| stored:phy | 12 | 57 | 269 |
| stored:mac | 11 | 37 | 65 |
| stored:sdn | 13 | 52 | 100 |
| stored:app | 16 | 47 | 61 |

## Instantiated templates

### generated:phy:with_observers

| Process | Template | Initial | Locations | Transitions |
|---|---|---|---:|---:|
| A_CH | Template_A_CH | ChannelNominal | 8 | 31 |
| A_SIG | Template_A_SIG | SignalNominal | 6 | 41 |
| A_BM | Template_A_BM | BeamSearch | 11 | 67 |
| A_SQ | Template_A_SQ | Idle | 11 | 24 |
| A_PH | Template_A_PH | PHYNormal | 8 | 71 |
| ENV_CH | Template_ENV_CH | TickWait | 1 | 5 |
| ENV_TARGET | Template_ENV_TARGET | TargetWait | 1 | 2 |
| ENV_MAC | Template_ENV_MAC | ConfigWait | 1 | 13 |
| ENV_NET | Template_ENV_NET | DeliveryWait | 1 | 4 |
| ObsSenseReport | Template_ObsSenseReport | Idle | 3 | 3 |
| ObsFreshness | Template_ObsFreshness | Idle | 3 | 3 |
| ObsBeamRecovery | Template_ObsBeamRecovery | Idle | 3 | 5 |

### generated:mac:with_observers

| Process | Template | Initial | Locations | Transitions |
|---|---|---|---:|---:|
| A_SCH | Template_A_SCH | Idle | 6 | 9 |
| A_Q | Template_A_Q | QueueNormal | 4 | 7 |
| A_BUF | Template_A_BUF | BufferSafe | 3 | 6 |
| A_RSRC | Template_A_RSRC | ResourceAvailable | 4 | 7 |
| A_MAC_AGG | Template_A_MAC_AGG | ReportIdle | 4 | 5 |
| A_ENV_MAC | Template_A_ENV_MAC | EnvIdle | 1 | 16 |
| ObsPhyAck | Template_ObsPhyAck | Idle | 3 | 3 |
| ObsQueueCritical | Template_ObsQueueCritical | Idle | 3 | 3 |
| ObsSensingCritical | Template_ObsSensingCritical | Idle | 3 | 3 |
| ObsBufferOverflow | Template_ObsBufferOverflow | Idle | 3 | 3 |
| ObsMacReportFreshness | Template_ObsMacReportFreshness | Idle | 3 | 3 |

### generated:sdn:with_observers

| Process | Template | Initial | Locations | Transitions |
|---|---|---|---:|---:|
| A_MON | Template_A_MON | MonitorIdle | 5 | 8 |
| A_RISK | Template_A_RISK | RiskLow | 4 | 16 |
| A_POLICY | Template_A_POLICY | PolicyIdle | 7 | 13 |
| A_RULE | Template_A_RULE | RuleStable | 7 | 10 |
| A_REC | Template_A_REC | StableConfig | 6 | 11 |
| A_SDN_AGG | Template_A_SDN_AGG | CommandBuild | 5 | 6 |
| A_ENV_SDN | Template_A_ENV_SDN | EnvIdle | 1 | 20 |
| ObsRuleMiss | Template_ObsRuleMiss | Idle | 3 | 3 |
| ObsRecovery | Template_ObsRecovery | Idle | 3 | 3 |
| ObsAdmission | Template_ObsAdmission | Idle | 3 | 3 |
| ObsStaleTelemetry | Template_ObsStaleTelemetry | Safe | 2 | 1 |
| ObsCommandAck | Template_ObsCommandAck | Idle | 3 | 3 |
| ObsSensingDecision | Template_ObsSensingDecision | Idle | 3 | 3 |

### stored:app

| Process | Template | Initial | Locations | Transitions |
|---|---|---|---:|---:|
| Req | A_REQ | ServiceIdle | 8 | 13 |
| Sla | A_SLA | SLAOk | 4 | 9 |
| Crit | A_CRIT | Idle | 1 | 0 |
| Agg | A_SVC_AGG | DemandStored | 1 | 0 |
| Sdn | A_SDN_RIC_STUB | SdnIdle | 5 | 7 |
| Env | A_ENV_DEMAND | EnvIdle | 2 | 2 |
| Kpi | A_KPI_OK_STUB | KpiIdle | 1 | 1 |
| Sink | A_REPORT_SINK | Sink | 1 | 5 |
| ObsAdmission | ObsServiceAdmission | Idle | 3 | 3 |
| ObsWarn | ObsSlaWarningDeadline | Idle | 3 | 3 |
| ObsViolation | ObsSlaViolationDeadline | Idle | 3 | 3 |
| ObsFresh | ObsDetectionFreshness | Idle | 3 | 3 |
| ObsUpdate | ObsUpdatePeriodViolation | Idle | 3 | 3 |
| ObsFa | ObsFalseAlarmCritical | Idle | 3 | 3 |
| ObsMiss | ObsMissedDetectionCritical | Idle | 3 | 3 |
| ObsSafety | ObsSafetyCriticalViolation | Idle | 3 | 3 |

## Same-name cross-layer channels

Endpoint presence is syntactic; no enabledness or compatibility is inferred.

| Channel | Layer | Kind | Senders | Receivers |
|---|---|---|---|---|
| mac_report | mac | broadcast | A_BUF, A_MAC_AGG, A_SCH | none |
| mac_report | sdn | broadcast | A_ENV_SDN | A_MON, A_POLICY |
| phy_kpi_report | phy | broadcast | A_PH | ObsSenseReport |
| phy_kpi_report | mac | broadcast | A_ENV_MAC | A_SCH |
| phy_kpi_report | sdn | broadcast | A_ENV_SDN | A_MON, A_POLICY |
| sdn_policy_cmd | mac | binary | A_ENV_MAC | none |
| sdn_policy_cmd | sdn | binary | A_REC, A_SDN_AGG | A_ENV_SDN |
| service_accept | sdn | broadcast | A_POLICY | none |
| service_accept | app | binary | Sdn | Req |
| service_degraded | sdn | broadcast | A_POLICY | none |
| service_degraded | app | binary | Sdn | Req |
| service_reject | sdn | broadcast | A_POLICY | none |
| service_reject | app | binary | Sdn | Req |
| service_request | sdn | broadcast | A_ENV_SDN | A_POLICY |
| service_request | app | binary | Req | Sdn |

Channel-kind conflicts: `service_accept`, `service_degraded`, `service_reject`, `service_request`.
