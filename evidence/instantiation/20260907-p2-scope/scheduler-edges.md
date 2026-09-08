# Existing A_SCH edge table

Generated from the pinned default MAC XML inventory. Static inspection only.

| Edge | Source | Target | Guard | Synchronization | Update |
|---:|---|---|---|---|---|
| 1 | Idle | CollectKPI | — | mac_tick? | c_sched = 0, mac_report_sent = false |
| 2 | CollectKPI | SelectMode | c_sched <= D_collect | phy_kpi_report? | c_sched = 0 |
| 3 | CollectKPI | ApplySchedule | kpiFreshnessClass != KPI_FRESH &#124;&#124; c_sched == D_collect | — | scheduleMode = SCH_CONSTRAINED, macReason = REASON_STALE_PHY_KPI, c_phy_ack = 0 |
| 4 | SelectMode | ScheduleFailure | gP0() | — | scheduleMode = SCH_CONSTRAINED, macReason = REASON_RESOURCE_EXHAUSTED, mac_report_pending = true, silent_accept = false |
| 5 | SelectMode | ApplySchedule | !gP0() | — | select_mac_policy(), c_phy_ack = 0, phy_command_pending = true |
| 6 | ApplySchedule | WaitPHYAck | — | mac_schedule_cmd! | phy_command_pending = true |
| 7 | WaitPHYAck | Idle | c_phy_ack <= D_phy_ack | phy_ack? | phy_command_pending = false, phy_ack_timeout = false |
| 8 | WaitPHYAck | ScheduleFailure | c_phy_ack == D_phy_ack | — | phy_ack_timeout = true, macReason = REASON_PHY_ACK_TIMEOUT, mac_report_pending = true, phy_command_pending = false |
| 9 | ScheduleFailure | Idle | — | mac_report! | mac_report_sent = true, mac_report_pending = false, silent_accept = false |
