# PHY Traceability Matrix

| Article claim | IR entity | UPPAAL artifact | Source |
|---|---|---|---|
| `A_PHY = A_CH || A_SIG || A_BM || A_SQ || A_PH` | composition | `system ... A_PH ...` | invariants |
| `A_SYS = A_PHY || A_ENV` | closed system | `ENV_CH, ENV_TARGET, ENV_MAC, ENV_NET` | invariants |
| PHY automaton A_CH | A_CH | Template_A_CH / instance A_CH | PHY_level_formalization_reviewed-2026-06-06-143000.tex:A_CH:377 |
| PHY automaton A_SIG | A_SIG | Template_A_SIG / instance A_SIG | PHY_level_formalization_reviewed-2026-06-06-143000.tex:A_SIG:444 |
| PHY automaton A_BM | A_BM | Template_A_BM / instance A_BM | PHY_level_formalization_reviewed-2026-06-06-143000.tex:A_BM:487 |
| PHY automaton A_SQ | A_SQ | Template_A_SQ / instance A_SQ | PHY_level_formalization_reviewed-2026-06-06-143000.tex:A_SQ:585 |
| PHY automaton A_PH | A_PH | Template_A_PH / instance A_PH | PHY_level_formalization_reviewed-2026-06-06-143000.tex:A_PH:667 |
| Bounded response ObsSenseReport | ObsSenseReport | A[] not ObsSenseReport.Violation | PHY_level_formalization_reviewed-2026-06-06-143000.tex:observers:820 |
| Bounded response ObsFreshness | ObsFreshness | A[] not ObsFreshness.Violation | PHY_level_formalization_reviewed-2026-06-06-143000.tex:observers:832 |
| Bounded response ObsBeamRecovery | ObsBeamRecovery | A[] not ObsBeamRecovery.Violation | PHY_level_formalization_reviewed-2026-06-06-143000.tex:observers:842 |
| Assume-guarantee for A_CH | A_CH | ass_ch() imply not ContractViolation_CH | PHY_level_formalization_reviewed-2026-06-06-143000.tex:contracts:263 |
| Assume-guarantee for A_SIG | A_SIG | ass_sig() imply not ContractViolation_SIG | PHY_level_formalization_reviewed-2026-06-06-143000.tex:contracts:265 |
| Assume-guarantee for A_BM | A_BM | ass_bm() imply not ContractViolation_BM | PHY_level_formalization_reviewed-2026-06-06-143000.tex:contracts:267 |
| Assume-guarantee for A_SQ | A_SQ | ass_sq() imply not ContractViolation_SQ | PHY_level_formalization_reviewed-2026-06-06-143000.tex:contracts:269 |
| Assume-guarantee for A_PH | A_PH | ass_ph() imply not ContractViolation_PH | PHY_level_formalization_reviewed-2026-06-06-143000.tex:contracts:271 |
