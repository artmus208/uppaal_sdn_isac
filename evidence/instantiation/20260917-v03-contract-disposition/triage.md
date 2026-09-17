# Диспозиция полного набора

Все 43 source timing constants и 14 integration keys сопоставлены с #32. Ни одна строка `separate_correction_required` не считается исправленной. Детали исходных intervals/resets — в закреплённом inventory #32; ссылки на точные XML edges сохранены в coverage.json.

| Группа | Параметры | Диспозиция | Основание / следующий шаг |
|---|---|---|---|
| phy-measurement | `phy.D_meas`, `phy.T_meas`, `phy.J_meas` | separate_correction_required | D_meas=5 / envelope=6: retain both historical values as observed; no report-by-5 or deadlock-freedom claim. Separately choose explicit timeout/failure at 5 or justified guard/envelope change before such claim. |
| phy-latest | `phy.D_sig`, `phy.D_report` | stage_assumption | Latest waveform_config/child report restarts its stage clock. Declare superseded/coalesced inputs; no response for each older event and no total deadline across repeated resets. |
| phy-observers | `phy.D_sense`, `phy.D_BM` | separate_correction_required | Keep core stage budget; independently align sensing_degraded/aos_ctrl_expired/recovery_start with actual core trigger coverage and matching outcomes before observer claims. D_BM recovery_cmd has no sender, but other recovery inputs remain relevant. |
| mac-stage | `mac.D_collect`, `mac.D_sched` | stage_assumption | D_collect and D_sched are stages with separate resets. ApplySchedule wait outside send-based ACK interval; no 2+5+3 global deadline. |
| mac-ack | `mac.D_phy_ack` | preserve_accepted_correction | Preserve #31 send-to-matching-ACK-or-ScheduleFailure<=3; do not rerun existing verifier cases without a discrepancy. |
| mac-observers | `mac.D_queue_crit`, `mac.D_buf_report`, `mac.D_mac_report` | separate_correction_required | Queue/buffer/report start/end polling remains unresolved. Preserve core phase bounds; ReportStale publication is unbounded, so D_mac_report is build-only. No blanket observer acceptance. |
| sdn-monitor | `sdn.D_mon` | stage_assumption | D_mon bounds CollectReports classification after receipt, not report generation or monitoring period. |
| sdn-decision | `sdn.D_decision` | stage_assumption_and_separate_observer_correction | Evaluate<=5 is a stage. SensingDecision pending/policy-class polling needs separate event correlation; unsolicited policy outcomes are not admission completion. |
| sdn-rule | `sdn.D_rule_install`, `sdn.D_rule_ack` | separate_correction_required | Install<=8 and ACK<=5 start at same rule_miss; not 8+5. RuleMiss/RuleInstalled waiting and ==8 timeout require explicit dispatch/outcome contract in a separate correction; retain numbers until reviewed. |
| sdn-control | `sdn.D_ctrl_ack` | separate_correction_required | Control ACK age starts on bus_ctrl_request, not command_pending. Review CommandSent unbounded waiting and stale/typed outcomes separately; preserve 5 as desired send-based bound. |
| recovery | `sdn.D_recovery`, `sdn.D_rollback` | correction_specified | Recovery accepted-failure to local outcome<=30, dispatch/failure by20, rollback<=10. Functional correction and passive recorder separately specified in contracts.md. |
| admission | `sdn.D_admission`, `app.D_admission` | correction_specified | APP send-to-accepted-outcome-or-local-timeout<=15; separate SDN receive-to-emission<=15 observer. Event-correlated recording; conditional transports+Evaluate<=7. |
| app-build | `app.D_req` | stage_assumption | D_req<=3 bounds RequestBuild only. RequestReady wait outside admission; no demand-to-send deadline. |
| app-events | `app.D_sla_warn`, `app.D_sla_violation`, `app.D_safety`, `app.D_fresh_report`, `app.D_update_report`, `app.D_fa_report`, `app.D_miss_report` | separate_correction_required | Oldest outstanding coalesced episodes, not per-notification guarantees. Match response events and atomic close; do not use stale flags/observer clearing. SLA core bounds and observer-only requirements are distinct. |
| inactive | `phy.D_child`, `phy.D_net`, `phy.T_report`, `phy.J_SSB`, `phy.tau_SSB`, `mac.D_phy_report`, `sdn.D_sec_ack`, `app.D_event`, `app.D_update`, `app.D_fresh`, `app.D_detect_warn`, `app.D_detect_violation`, `app.D_sensing_fresh` | inapplicable | Declaration-only in selected XML/query set; not an implemented constraint. A_SEC disabled; retain source declaration without transferring a guarantee. |
| transport | `D_cmd`, `D_bus` | environment_assumption | Per-bridge interval from actual accept/snapshot; delivery or loss at equality. D_cmd covers entire schedule route, D_bus phases as documented; no forced delivery. |
| offers | `T_input`, `T_mac_tick`, `T_demand`, `T_complete`, `fault_window` | environment_assumption | Periodic attempts may be missed; demand/completion/fault are absolute offers, not guaranteed reception/duration. Fault window inclusive [12,13]; no-fault/drop permitted. |
| freshness | `freshness_warn_age`, `freshness_expire_age` | environment_assumption | Age from source generation; <5 fresh, [5,10) stale, >=10 expired; missing before first sample. Delivery does not reset age; latest overwrite remains explicit. |
| finite | `max_fault_events`, `max_requests_per_service`, `max_outstanding_per_command_kind` | scope_assumption | One session/request/fault, one outstanding slot per command kind. These are finite structural bounds, not retry/timing guarantees; wider use requires a separate model. |
| configuration | `layer_profiles`, `justification` | claim_boundary | Abstract profile selection and justification; time scale unspecified; no physical calibration or universal deadlines. |

## Граница принятия

Stage/environment assumptions описывают выбранную абстракцию и не являются verification claim. Остальные corrections остаются обязательными перед использованием соответствующих observer properties как evidence. Их подробные endpoints и production scopes должны пройти отдельное решение: Issue #33 не выдаёт общее разрешение править все слои.

Для recovery/admission следующий deliverable уже специфицирован. Для PHY measurement/observer coverage, MAC polling/report, SDN rule/control/sensing и остальных APP latches нужны отдельные contract/correction задания; до них claims по этим наблюдателям остаются неподтверждёнными. APP Crit/Agg placeholders не реализуют никаких сроков. Неиспользуемые декларации не требуют удаления.

43/14 — полнота по объявленным поверхностям #32, не утверждение об инвентаризации любой будущей конфигурации.
