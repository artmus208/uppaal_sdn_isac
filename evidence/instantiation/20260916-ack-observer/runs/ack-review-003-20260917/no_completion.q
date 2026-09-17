E<> fixture_sent == 1 && mac_obs_ack_active
E<> obs_mac_ObsPhyAck_0.Violation && fixture_sent == 1 && fixture_completed == 0 && mac_A_SCH_0.WaitPHYAck && mac_obs_ack_active && mac_c_obs_ack > 3
A[] fixture_completed == 0
A[] not obs_mac_ObsPhyAck_0.Violation
