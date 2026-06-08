# PHY Property Report

| Property | Category | Query | Result | Interpretation | Source |
|---|---|---|---|---|---|
| deadlock_free | safety | `A[] not deadlock` | not_run | closed A_SYS has no deadlocks | PHY_level_formalization_reviewed-2026-06-06-143000.tex:properties:812 |
| reach_phy_normal | reachability | `E<> A_PH.PHYNormal` | not_run | normal PHY state is reachable | PHY_level_formalization_reviewed-2026-06-06-143000.tex:properties:813 |
| reach_phy_sensing_degraded | reachability | `E<> A_PH.PHYSensingDegraded` | not_run | sensing degradation is reachable | PHY_level_formalization_reviewed-2026-06-06-143000.tex:properties:814 |
| reach_phy_communication_degraded | reachability | `E<> A_PH.PHYCommunicationDegraded` | not_run | communication degradation is reachable | PHY_level_formalization_reviewed-2026-06-06-143000.tex:properties:815 |
| reach_phy_joint_degraded | reachability | `E<> A_PH.PHYJointDegraded` | not_run | joint degradation is reachable | PHY_level_formalization_reviewed-2026-06-06-143000.tex:properties:816 |
| aggregation_consistency | safety | `A[] (A_PH.PHYNormal imply (comm_ok && sensing_qos_ok))` | not_run | normal state implies both aggregate booleans are ok | PHY_level_formalization_reviewed-2026-06-06-143000.tex:properties:817 |
| ch_determinism | safety | `A[] (ch_enabled_count <= 1)` | not_run | channel classifier has at most one enabled result | PHY_level_formalization_reviewed-2026-06-06-143000.tex:properties:858 |
| sq_determinism | safety | `A[] (sq_enabled_count <= 1)` | not_run | sensing classifier has at most one enabled result | PHY_level_formalization_reviewed-2026-06-06-143000.tex:properties:859 |
| bm_recover_invariant | safety | `A[] (A_BM.BeamRecover imply c_rec <= D_BM)` | not_run | beam recovery never exceeds its invariant | PHY_level_formalization_reviewed-2026-06-06-143000.tex:properties:854 |
| ObsSenseReport | observer | `A[] not ObsSenseReport.Violation` | not_run | ObsSenseReport does not reach Violation | PHY_level_formalization_reviewed-2026-06-06-143000.tex:observers:820 |
| ObsFreshness | observer | `A[] not ObsFreshness.Violation` | not_run | ObsFreshness does not reach Violation | PHY_level_formalization_reviewed-2026-06-06-143000.tex:observers:832 |
| ObsBeamRecovery | observer | `A[] not ObsBeamRecovery.Violation` | not_run | ObsBeamRecovery does not reach Violation | PHY_level_formalization_reviewed-2026-06-06-143000.tex:observers:842 |
| contract_ch | contract | `A[] (ass_ch() imply not A_CH.ContractViolation_CH)` | not_run | A_CH contract violation is absent under assumptions | PHY_level_formalization_reviewed-2026-06-06-143000.tex:contracts:877 |
| contract_sig | contract | `A[] (ass_sig() imply not A_SIG.ContractViolation_SIG)` | not_run | A_SIG contract violation is absent under assumptions | PHY_level_formalization_reviewed-2026-06-06-143000.tex:contracts:878 |
| contract_bm | contract | `A[] (ass_bm() imply not A_BM.ContractViolation_BM)` | not_run | A_BM contract violation is absent under assumptions | PHY_level_formalization_reviewed-2026-06-06-143000.tex:contracts:879 |
| contract_sq | contract | `A[] (ass_sq() imply not A_SQ.ContractViolation_SQ)` | not_run | A_SQ contract violation is absent under assumptions | PHY_level_formalization_reviewed-2026-06-06-143000.tex:contracts:880 |
| contract_ph | contract | `A[] (ass_ph() imply not A_PH.ContractViolation_PH)` | not_run | A_PH contract violation is absent under assumptions | PHY_level_formalization_reviewed-2026-06-06-143000.tex:contracts:881 |

Generated query lines: 17.
