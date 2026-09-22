// Candidates only: no verifier verdict, no Gate acceptance.
// C01-deadlock: entire composition, not only selected observers.
A[] not deadlock
// C02-ACK-elapsed: producer-owned recorder, not observer scheduling.
A[] (!mac_obs_ack_late && (mac_obs_ack_active imply mac_c_obs_ack <= mac_D_phy_ack))
// ACK-unconditional-completion diagnostic: NOT time-divergence restricted.
mac_obs_ack_active --> !mac_obs_ack_active
// ACK-trigger reachability: guard against vacuous elapsed-safety success.
E<> mac_obs_ack_active
// Timeout reachability does not establish universal completion.
E<> mac_phy_ack_timeout
// ACK-success needs a transition trace or event marker: Idle is also initial.
// No queue-capacity query: no justified occupancy/capacity abstraction exists.
// No recovery-attempt query: passive attempt recorder is not implemented yet.
