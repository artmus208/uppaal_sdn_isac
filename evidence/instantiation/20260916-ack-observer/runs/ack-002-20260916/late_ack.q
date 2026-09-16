A[] not obs_mac_ObsPhyAck_0.Violation
E<> fixture_completed == 2
E<> mac_A_SCH_0.Idle && fixture_completed > 0 && !mac_phy_ack_timeout
E<> mac_A_SCH_0.ScheduleFailure && mac_phy_ack_timeout
E<> fixture_completed == 2 && mac_obs_ack_late && mac_obs_ack_active && mac_c_obs_ack == 0
E<> mac_A_SCH_0.Idle && mac_obs_ack_late && !mac_phy_ack_timeout
