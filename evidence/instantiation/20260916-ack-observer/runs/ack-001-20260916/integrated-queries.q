// phy-01 -- candidate, no verdict
A[] not deadlock
// phy-02 -- candidate, no verdict
E<> phy_A_PH_0.PHYNormal
// phy-03 -- candidate, no verdict
E<> phy_A_PH_0.PHYSensingDegraded
// phy-04 -- candidate, no verdict
E<> phy_A_PH_0.PHYCommunicationDegraded
// phy-05 -- candidate, no verdict
E<> phy_A_PH_0.PHYJointDegraded
// phy-06 -- candidate, no verdict
A[] (phy_A_PH_0.PHYNormal imply (phy_comm_ok && phy_sensing_qos_ok))
// phy-07 -- candidate, no verdict
A[] (phy_ch_enabled_count <= 1)
// phy-08 -- candidate, no verdict
A[] (phy_sq_enabled_count <= 1)
// phy-09 -- candidate, no verdict
A[] (phy_A_BM_0.BeamRecover imply phy_c_rec <= phy_D_BM)
// phy-10 -- candidate, no verdict
A[] not obs_phy_ObsSenseReport_0.Violation
// phy-11 -- candidate, no verdict
A[] not obs_phy_ObsFreshness_0.Violation
// phy-12 -- candidate, no verdict
A[] not obs_phy_ObsBeamRecovery_0.Violation
// phy-13 -- candidate, no verdict
A[] (phy_ass_ch() imply not phy_A_CH_0.ContractViolation_CH)
// phy-14 -- candidate, no verdict
A[] (phy_ass_sig() imply not phy_A_SIG_0.ContractViolation_SIG)
// phy-15 -- candidate, no verdict
A[] (phy_ass_bm() imply not phy_A_BM_0.ContractViolation_BM)
// phy-16 -- candidate, no verdict
A[] (phy_ass_sq() imply not phy_A_SQ_0.ContractViolation_SQ)
// phy-17 -- candidate, no verdict
A[] (phy_ass_ph() imply not phy_A_PH_0.ContractViolation_PH)
// mac-01 -- candidate, no verdict
A[] not deadlock
// mac-02 -- candidate, no verdict
A[] (mac_resourceClass == mac_RES_EXHAUSTED imply !mac_silent_accept)
// mac-03 -- candidate, no verdict
A[] (mac_A_SCH_0.WaitPHYAck imply mac_c_phy_ack <= mac_D_phy_ack)
// mac-04 -- candidate, no verdict
A[] not obs_mac_ObsPhyAck_0.Violation
// mac-05 -- candidate, no verdict
A[] not obs_mac_ObsQueueCritical_0.Violation
// mac-06 -- candidate, no verdict
A[] not obs_mac_ObsSensingCritical_0.Violation
// mac-07 -- candidate, no verdict
E<> mac_A_SCH_0.SelectMode
// mac-08 -- candidate, no verdict
E<> mac_A_MAC_AGG_0.ReportSent
// mac-09 -- candidate, no verdict
A[] mac_policy_enabled_count >= 1
// sdn-01 -- candidate, no verdict
A[] not deadlock
// sdn-02 -- candidate, no verdict
A[] (sdn_A_RULE_0.RuleInstallPending imply sdn_c_rule <= sdn_D_rule_install)
// sdn-03 -- candidate, no verdict
A[] (sdn_telemetryClass == sdn_TEL_STALE imply !sdn_optimistic_reconfig)
// sdn-04 -- candidate, no verdict
A[] (sdn_telemetryClass == sdn_TEL_MISSING imply !sdn_optimistic_reconfig)
// sdn-05 -- candidate, no verdict
A[] (sdn_recoveryClass == sdn_REC_FAILED imply sdn_failure_report_sent)
// sdn-06 -- candidate, no verdict
A[] not obs_sdn_ObsRuleMiss_0.Violation
// sdn-07 -- candidate, no verdict
A[] not obs_sdn_ObsRecovery_0.Violation
// sdn-08 -- candidate, no verdict
A[] not obs_sdn_ObsAdmission_0.Violation
// sdn-09 -- candidate, no verdict
A[] not obs_sdn_ObsStaleTelemetry_0.Violation
// sdn-10 -- candidate, no verdict
E<> sdn_A_POLICY_0.Evaluate
// sdn-11 -- candidate, no verdict
E<> sdn_A_RULE_0.RuleTimeout
// sdn-12 -- candidate, no verdict
E<> sdn_A_REC_0.RecoveryFailed
// sdn-13 -- candidate, no verdict
A[] sdn_policy_enabled_count >= 1
// app-01 -- candidate, no verdict
A[] not deadlock
// app-02 -- candidate, no verdict
A[] not obs_app_ObsAdmission_0.Violation
// app-03 -- candidate, no verdict
A[] not obs_app_ObsWarn_0.Violation
// app-04 -- candidate, no verdict
A[] not obs_app_ObsViolation_0.Violation
// app-05 -- candidate, no verdict
A[] not obs_app_ObsFresh_0.Violation
// app-06 -- candidate, no verdict
A[] not obs_app_ObsUpdate_0.Violation
// app-07 -- candidate, no verdict
A[] not obs_app_ObsFa_0.Violation
// app-08 -- candidate, no verdict
A[] not obs_app_ObsMiss_0.Violation
// app-09 -- candidate, no verdict
A[] not obs_app_ObsSafety_0.Violation
// app-10 -- candidate, no verdict
A[] app_detection_kpi_consistent()
// app-11 -- candidate, no verdict
A[] not (app_criticalityClass == app_CRIT_SAFETY && app_admissionClass == app_ADM_DEGRADED && !app_gSafetyAllowsDegraded())
// app-12 -- candidate, no verdict
E<> app_Req_0.Accepted
// app-13 -- candidate, no verdict
E<> app_Req_0.AcceptedDegraded
// app-14 -- candidate, no verdict
E<> app_Req_0.Rejected
// reach-obs_phy_ObsSenseReport_0 -- candidate, no verdict
E<> obs_phy_ObsSenseReport_0.Violation
// reach-obs_phy_ObsFreshness_0 -- candidate, no verdict
E<> obs_phy_ObsFreshness_0.Violation
// reach-obs_phy_ObsBeamRecovery_0 -- candidate, no verdict
E<> obs_phy_ObsBeamRecovery_0.Violation
// reach-obs_mac_ObsPhyAck_0 -- candidate, no verdict
E<> obs_mac_ObsPhyAck_0.Violation
// reach-obs_mac_ObsQueueCritical_0 -- candidate, no verdict
E<> obs_mac_ObsQueueCritical_0.Violation
// reach-obs_mac_ObsSensingCritical_0 -- candidate, no verdict
E<> obs_mac_ObsSensingCritical_0.Violation
// reach-obs_mac_ObsBufferOverflow_0 -- candidate, no verdict
E<> obs_mac_ObsBufferOverflow_0.Violation
// reach-obs_mac_ObsMacReportFreshness_0 -- candidate, no verdict
E<> obs_mac_ObsMacReportFreshness_0.Violation
// reach-obs_sdn_ObsRuleMiss_0 -- candidate, no verdict
E<> obs_sdn_ObsRuleMiss_0.Violation
// reach-obs_sdn_ObsRecovery_0 -- candidate, no verdict
E<> obs_sdn_ObsRecovery_0.Violation
// reach-obs_sdn_ObsAdmission_0 -- candidate, no verdict
E<> obs_sdn_ObsAdmission_0.Violation
// reach-obs_sdn_ObsStaleTelemetry_0 -- candidate, no verdict
E<> obs_sdn_ObsStaleTelemetry_0.Violation
// reach-obs_sdn_ObsCommandAck_0 -- candidate, no verdict
E<> obs_sdn_ObsCommandAck_0.Violation
// reach-obs_sdn_ObsSensingDecision_0 -- candidate, no verdict
E<> obs_sdn_ObsSensingDecision_0.Violation
// reach-obs_app_ObsAdmission_0 -- candidate, no verdict
E<> obs_app_ObsAdmission_0.Violation
// reach-obs_app_ObsWarn_0 -- candidate, no verdict
E<> obs_app_ObsWarn_0.Violation
// reach-obs_app_ObsViolation_0 -- candidate, no verdict
E<> obs_app_ObsViolation_0.Violation
// reach-obs_app_ObsFresh_0 -- candidate, no verdict
E<> obs_app_ObsFresh_0.Violation
// reach-obs_app_ObsUpdate_0 -- candidate, no verdict
E<> obs_app_ObsUpdate_0.Violation
// reach-obs_app_ObsFa_0 -- candidate, no verdict
E<> obs_app_ObsFa_0.Violation
// reach-obs_app_ObsMiss_0 -- candidate, no verdict
E<> obs_app_ObsMiss_0.Violation
// reach-obs_app_ObsSafety_0 -- candidate, no verdict
E<> obs_app_ObsSafety_0.Violation
// integrated-01 -- candidate, no verdict
A[] not bus_protocol_error
// integrated-02 -- candidate, no verdict
E<> app_Req_0.Accepted
// integrated-03 -- candidate, no verdict
E<> bus_admission_timeout
// integrated-04 -- candidate, no verdict
E<> bus_schedule_loss
// integrated-05 -- candidate, no verdict
E<> bus_fault_delivered
// integrated-06 -- candidate, no verdict
A[] not deadlock
