E<> fixture_sent == 1 && mac_obs_ack_active && fixture_from_first_send == 0
E<> fixture_sent == 1 && fixture_completed == 1 && !mac_obs_ack_active && !mac_phy_ack_timeout && fixture_from_first_send == 0
E<> fixture_sent == 2 && fixture_completed == 1 && mac_obs_ack_active && fixture_from_completion == 0
E<> fixture_sent == 2 && fixture_completed == 2 && fixture_from_first_send == 0
A[] not obs_mac_ObsPhyAck_0.Violation
E<> fixture_sent == 2 && fixture_completed == 1 && mac_obs_ack_active && mac_obs_ack_late && fixture_from_completion == 0
