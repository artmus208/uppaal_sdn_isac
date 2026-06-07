# PHY-Specific MCP Layer Tasks

Цель: перейти от текущего универсального MCP-wrapper над `verifyta` к PHY-specific assistant для файла `PHY_level_formalization_reviewed-2026-06-06-143000.tex`.

Итоговый слой должен уметь извлекать контрактную спецификацию из LaTeX, строить проверяемую UPPAAL-модель `A_SYS`, генерировать property pack, запускать `verifyta`, валидировать соответствие статье и объяснять counterexample в терминах PHY/SDN/ISAC.

## 0. Неперегибаемые инварианты

- [x] `A_PHY` всегда трактуется как ровно пять PHY-компонентов:
  `A_CH || A_SIG || A_BM || A_SQ || A_PH`.
- [x] `A_ENV` не является PHY-компонентом, но обязателен для закрытой проверяемой модели:
  `A_SYS = A_PHY || A_ENV`.
- [x] `A_ENV` генерируется как композиция:
  `ENV_CH || ENV_TARGET || ENV_MAC || ENV_NET`.
- [x] Timed automata не вычисляют `SINR`, `Pd`, `Rfa`, `CRB`, `p_mis`, `Omega_BM` и `Pi_PHY`.
- [x] Guards в UPPAAL используют только finite class variables, clocks, bounded integers и booleans.
- [x] Report/event channels объявляются как `broadcast chan`.
- [x] Command channels от environment/MAC/SDN объявляются как обычные `chan`.
- [x] Каждый transition edge имеет не больше одного sync label.
- [x] `PHYState` обновляет только `A_PH`.
- [x] Bounded deadlines проверяются observer-автоматами, а не unbounded leads-to `p --> q`.
- [x] Deadline включительный: событие при `c == D` допустимо, violation только при `c > D`.
- [x] `Pi_PHY` в базовой модели остается внешним score или требует отдельного priced/weighted TA режима.

## 1. Contract IR: внутренняя машинная спецификация

- [x] Спроектировать `PhyContractModel` как промежуточное представление между LaTeX и UPPAAL XML.
- [x] Добавить сущности IR: `AutomatonSpec`, `EnvSpec`, `LocationSpec`, `TransitionSpec`, `ClockSpec`, `VariableSpec`, `ChannelSpec`, `ObserverSpec`, `PropertySpec`, `ContractSpec`.
- [x] Для каждой сущности хранить provenance: имя секции, line number или диапазон строк из `.tex`.
- [x] Описать enum/bounded-int классы из `X_disc`: `SINRClass`, `BLERClass`, `CQIClass`, `IClass`, `DopplerClass`, `DelaySpreadClass`, `PowerClass`, `DRTClass`, `PilotDensityClass`, `PayloadSenseClass`, `PRSClass`, `BeamErrorClass`, `BlockageClass`, `PdClass`, `RfaClass`, `AccClass`, `CRBClass`, `AoSClass`, `CapClass`, `CoverageClass`, `ResourceShareClass`, `MisClass`, `BMOverheadClass`, `ChannelClass`, `SignalClass`, `BeamClass`, `SensingState`, `PHYState`.
- [x] Зафиксировать canonical names для templates, instances и locations, чтобы queries стабильно ссылались на `A_PH.PHYNormal`, `A_BM.BeamRecover` и т.п.
- [x] Добавить schema validation для IR: обязательные автоматы, обязательные clocks, обязательные каналы, обязательные observers, обязательные properties.
- [x] Добавить сериализацию IR в JSON для отладки MCP tools.
- [x] Добавить golden JSON fixture для текущего `.tex`.

## 2. LaTeX extractor

- [x] Реализовать `phy_spec.extract_contract_model(tex_text|tex_path)`.
- [x] Извлекать структуру секций: базовая модель, `alpha_PHY`, assume-guarantee, operational semantics, автоматы PHY, SensCAP/freshness, интерфейс отчетов, verification properties.
- [x] Извлекать формулы композиции `A_PHY`, `A_SYS`, `A_ENV`.
- [x] Извлекать список `X_disc` и все множества значений классов из `align`-блоков.
- [x] Извлекать clocks и reset semantics из таблицы clocks.
- [x] Извлекать invariants: `MeasurePending`, `SignalReconfiguring`, `SensingEvaluating`, `PHYKpiReporting`, `BeamRecover`.
- [x] Извлекать handshake channels из verbatim-блока.
- [x] Извлекать broadcast report channels.
- [x] Извлекать broadcast diagnostic/degradation/recovery events.
- [x] Извлекать locations и transition sketches для `A_CH`, `A_SIG`, `A_BM`, `A_SQ`, `A_PH`.
- [x] Извлекать `ENV_CH`, `ENV_TARGET`, `ENV_MAC`, `ENV_NET` behavior sketches.
- [x] Извлекать assume/guarantee таблицу для пяти PHY-автоматов.
- [x] Извлекать property pack и observer definitions.
- [x] Извлекать ограничения применимости: no continuous guards, no probability proof inside TA, no base-TA optimization of `Pi_PHY`.
- [x] Добавить диагностику extractor-а: missing section, ambiguous class set, duplicate location, unsupported LaTeX construct.
- [x] Добавить тесты extractor-а на текущем `.tex` как primary fixture.
- [x] Добавить negative fixture: удалить `A_ENV` из TeX и убедиться, что extractor/validator ругается.
- [x] Добавить negative fixture: waveform как location в `A_SIG` и убедиться, что validator ругается.

## 3. Alpha PHY registry and checks

- [x] Реализовать `phy_alpha.list_classes()`.
- [x] Реализовать `phy_alpha.generate_uppaal_declarations()`.
- [x] Реализовать `phy_alpha.validate_threshold_policy(profile_json)`.
- [x] Реализовать `phy_alpha.classify_sample(meas, cfg, profile)` для внешней проверки примеров.
- [x] Реализовать `phy_alpha.check_boundary_policy()` с правилом `boundary(good,bad) -> bad`.
- [x] Реализовать `phy_alpha.check_no_continuous_guards(model_xml|contract_ir)`.
- [x] Запретить в guards прямые имена continuous KPI: `SINR_c`, `SINR_s`, `Pd`, `Rfa`, `CRB_R`, `CRB_v`, `CRB_theta`, `Acc_r`, `Acc_v`, `p_mis`, `Omega_BM`, `Pi_PHY`.
- [x] Проверять, что все safety-critical class boundaries консервативны.
- [x] Проверять, что все class variables имеют bounded domain.
- [x] Проверять, что estimator-derived values появляются только в alpha/profile/report metadata, а не в UPPAAL transition guards.
- [x] Добавить threshold profiles: `default`, `conservative_safety`, `stress`.
- [x] Не реализовывать parameter synthesis в этом слое; только instantiate profile.

## 4. UPPAAL XML generation foundation

- [x] Реализовать XML builder на `xml.etree.ElementTree` или другом структурном API, без ручной склейки XML строк.
- [x] Генерировать корректный `nta` документ с declarations, templates, system declaration и optional queries.
- [x] Генерировать bounded-int/constant declarations для class values.
- [x] Генерировать clocks, booleans, flags, report variables и helper functions.
- [x] Генерировать template instances: `A_CH`, `A_SIG`, `A_BM`, `A_SQ`, `A_PH`, `ENV_CH`, `ENV_TARGET`, `ENV_MAC`, `ENV_NET`, observers.
- [x] Генерировать `system A_CH, A_SIG, A_BM, A_SQ, A_PH, ENV_CH, ENV_TARGET, ENV_MAC, ENV_NET, ...;`.
- [x] Добавить deterministic layout координаты, чтобы XML открывался в UPPAAL GUI без каши.
- [x] Добавить режим `minimal`, `with_observers`, `with_debug_counters`, `with_negative_scenarios`.
- [x] Добавить static validation после генерации: XML parse, templates exist, init exists, all transition sources/targets valid.
- [ ] Добавить smoke verification generated model через `verifyta`.

## 5. Channel semantics validation

- [x] Реализовать `phy_sync.check_channel_semantics(model_xml|contract_ir)`.
- [x] Проверять, что `channel_report`, `signal_report`, `beam_report`, `sensing_report`, `phy_kpi_report` объявлены как `broadcast chan`.
- [x] Проверять, что diagnostic/recovery/degradation events объявлены как `broadcast chan`.
- [x] Проверять, что `measure_tick`, `pilot_config`, `prs_config`, `ssb_burst_config`, `waveform_config`, `payload_sensing_config`, `beam_cmd`, `extra_ssb_cmd`, `handover_assist_cmd`, `power_cmd`, `sensing_mode_cmd`, `recovery_cmd`, `new_beam_confirmed`, `mac_report_delivered`, `controller_report_delivered` объявлены как обычные `chan`.
- [x] Проверять, что `A_SQ` слушает `channel_report?`, `signal_report?`, `beam_report?`.
- [x] Проверять, что `A_PH` слушает `channel_report?`, `signal_report?`, `beam_report?`, `sensing_report?`.
- [x] Проверять, что observers слушают только broadcast events/reports и не блокируют систему.
- [x] Проверять, что один edge не содержит два sync label.
- [x] Проверять, что если нужен report плюс отдельное событие деградации, они вынесены в разные transitions или событие закодировано в report payload.

## 6. A_CH generator and checks

- [x] Сгенерировать locations: `MeasurePending`, `ChannelNominal`, `InterferenceLimited`, `MobilityLimited`, `MultipathLimited`, `Blockage`, `Outage`, `ContractViolation_CH`.
- [x] Сгенерировать input `measure_tick?`.
- [x] Сгенерировать output `channel_report!`.
- [x] Сгенерировать update `ChannelClass := highest_priority_CH(...)`.
- [x] Реализовать helper function `highest_priority_CH`.
- [x] Реализовать priority order: `Outage > Blockage > InterferenceLimited > MobilityLimited > MultipathLimited > ChannelNominal`.
- [x] Реализовать `channel_degraded_flag`.
- [x] Реализовать optional separate alerts: `phy_outage!`, `channel_degraded!`, `mobility_alert!`, `multipath_alert!`, `blockage_detected!`.
- [x] Проверять `ch_enabled_count <= 1` или доказывать детерминизм через generated priority function.
- [x] Проверять отсутствие continuous guards.
- [x] Проверять guarantee: после `measure_tick?` до `D_meas` публикуется `channel_report!`.
- [ ] Проверять contract violation path при нарушении assumptions.

## 7. A_SIG generator and checks

- [x] Сгенерировать waveform `W` как finite variable, а не location.
- [x] Сгенерировать locations: `SignalNominal`, `PilotBasedSensing`, `PayloadAssistedSensing`, `SignalReconfiguring`, `SignalLimited`, `ContractViolation_SIG`.
- [x] Сгенерировать inputs: `waveform_config?`, `pilot_config?`, `payload_sensing_config?`.
- [x] Сгенерировать output `signal_report!`.
- [x] Сгенерировать `SignalClass` updates.
- [x] Проверять, что `OFDM`, `OTFS`, `AFDM`, `SC`, `OTHER` не появились как locations.
- [x] Проверять invariant `SignalReconfiguring: c_sig <= D_sig`.
- [x] Проверять transitions из статьи для pilot-based/payload-assisted/reconfiguration/limited.
- [x] Реализовать `signal_degraded_flag`.
- [x] Реализовать optional separate `signal_degraded!` self-loop.
- [x] Проверять guarantee: после конфигурационной команды до `D_sig` публикуется `signal_report!`.

## 8. A_BM generator and checks

- [x] Сгенерировать locations: `BeamSearch`, `BeamSearchSeen`, `BeamTrack`, `BeamLock`, `BeamPredict`, `BeamMisalign`, `BeamRecoveryStart`, `BeamRecover`, `BeamHOAssist`, `BeamFailed`, `ContractViolation_BM`.
- [x] Сгенерировать inputs: `beam_cmd?`, `target_detected?`, `extra_ssb_cmd?`, `new_beam_confirmed?`, `recovery_cmd?`.
- [x] Сгенерировать outputs: `beam_report!`, `beam_misaligned!`, `recovery_start!`, `beam_restored!`, `handover_hint!`, `beam_failure!`.
- [x] Сгенерировать `BeamClass` updates.
- [x] Проверять invariant `BeamRecover: c_rec <= D_BM`.
- [x] Запретить transition guard `c_rec > D_BM` из `BeamRecover`.
- [x] Требовать timeout guard `c_rec == D_BM` для `beam_failure!`.
- [x] Проверять, что outcome events recovery: `beam_restored!`, `handover_hint!`, `beam_failure!`.
- [x] Проверять, что recovery outcome не смешивается с `beam_report!` на одном edge.
- [x] Проверять, что при входе в `BeamRecover` не позже `D_BM` происходит ровно один outcome.
- [x] Проверять, что `Omega_BM` не используется как TA guard; используется только `BMOverheadClass`.
- [x] Проверять guarantee: misalignment порождает `beam_misaligned!` до `D_BM`.

## 9. A_SQ generator and checks

- [x] Сгенерировать locations: `Idle`, `SensingEvaluating`, `SensingQoSOk`, `ProbabilityLimited`, `FalseAlarmLimited`, `AccuracyLimited`, `FreshnessLimited`, `CoverageLimited`, `CapacityLimited`, `SensingFailure`, `ContractViolation_SQ`.
- [x] Сгенерировать inputs: `channel_report?`, `signal_report?`, `beam_report?`.
- [x] Сгенерировать output `sensing_report!`.
- [x] Реализовать helper function `highest_priority_SQ`.
- [x] Реализовать priority order: `SensingFailure > FreshnessLimited > AccuracyLimited > ProbabilityLimited > FalseAlarmLimited > CapacityLimited > CoverageLimited > SensingQoSOk`.
- [x] Проверять, что `A_SQ` действительно зависит от `ChannelClass`, `SignalClass`, `BeamClass` и sensing class variables.
- [x] Проверять `sq_enabled_count <= 1` или доказывать детерминизм через generated priority function.
- [x] Проверять отсутствие guards по `Pd`, `Rfa`, `Acc_r`, `Acc_v`, `CRB`, `C_s`.
- [x] Реализовать flags `sensing_degraded_flag`, `sensing_failure_flag`.
- [x] Реализовать optional separate `sensing_degraded!`, `sensing_failure!`.
- [x] Проверять guarantee: после свежих child reports до `D_sense` публикуется `sensing_report!`.

## 10. A_PH generator and checks

- [x] Сгенерировать locations: `PHYNormal`, `PHYCommunicationDegraded`, `PHYSensingDegraded`, `PHYJointDegraded`, `PHYKpiReporting`, `PHYRecovery`, `PHYFailure`, `ContractViolation_PH`.
- [x] Сгенерировать inputs: `channel_report?`, `signal_report?`, `beam_report?`, `sensing_report?`, `recovery_cmd?`.
- [x] Сгенерировать outputs: `phy_kpi_report!`, `phy_failure!`.
- [x] Реализовать booleans/helper functions `comm_ok()` и `sensing_qos_ok()`.
- [x] Реализовать single-writer policy для `PHYState`.
- [x] Проверять, что `A_CH`, `A_SIG`, `A_BM`, `A_SQ`, `ENV_*` не обновляют `PHYState`.
- [x] Проверять aggregation consistency: `A[] (A_PH.PHYNormal imply (comm_ok && sensing_qos_ok))`.
- [x] Проверять четыре reachability свойства: `PHYNormal`, `PHYSensingDegraded`, `PHYCommunicationDegraded`, `PHYJointDegraded`.
- [x] Реализовать `degradation_flag`.
- [x] Реализовать optional separate `degradation_event!` self-loop.
- [x] Проверять guarantee: после degradation/child update до `D_report` публикуется `phy_kpi_report!`.

## 11. A_ENV and closed-system generation

- [x] Сгенерировать `ENV_CH` с bounded nondeterministic `measure_tick!`.
- [x] В `ENV_CH` обновлять estimator class variables перед `measure_tick!`.
- [x] Сгенерировать `ENV_TARGET` с nondeterministic updates для `PRSClass`, `BeamErrorClass`, `BlockageClass` и `target_detected!`.
- [x] Сгенерировать `ENV_MAC` с admissible `pilot_config!`, `waveform_config!`, `recovery_cmd!`, `extra_ssb_cmd!`, `new_beam_confirmed!`.
- [x] Сгенерировать `ENV_NET` с bounded delivery для `mac_report_delivered!` и `controller_report_delivered!`.
- [x] Реализовать assumption state variables: `TimingOk`, `ConfigAdmissible`, `BeamCmdAdmissible`, network delivery ok flags.
- [x] Проверять, что generated `A_SYS` включает все `ENV_*`.
- [ ] Добавить режим open-system contract, где `A_ENV` не включен, а свойства оборачиваются assumptions; по умолчанию использовать closed-system.
- [ ] Проверять, что `A[] not deadlock` запускается только на закрытой модели или явно помеченной open-assumption модели.
- [x] Добавить scenario profiles для нормального, degraded и failure окружения.

## 12. Observer generators

- [x] Реализовать generic `generate_bounded_response_observer(trigger, responses, deadline, name)`.
- [x] Сгенерировать `ObsSenseReport`: `sensing_degraded? -> phy_kpi_report? within D_report`.
- [x] Сгенерировать `ObsFreshness`: `aos_ctrl_expired? -> sensing_report? with SensingState == FreshnessLimited within D_sense`.
- [x] Сгенерировать `ObsBeamRecovery`: `recovery_start? -> one of beam_restored?/handover_hint?/beam_failure? within D_BM`.
- [ ] Сгенерировать optional `ObsChannelReport`: `measure_tick? -> channel_report? within D_meas`.
- [ ] Сгенерировать optional `ObsSignalReport`: config command -> `signal_report? within D_sig`.
- [ ] Сгенерировать optional `ObsSensingReport`: child report update -> `sensing_report? within D_sense`.
- [ ] Сгенерировать optional `ObsPhyKpiReport`: child degradation/update -> `phy_kpi_report? within D_report`.
- [x] Проверять, что observer waiting locations не имеют invariant `c_obs <= D`.
- [x] Проверять, что violation transition использует `c_obs > D`.
- [x] Проверять, что success transition допускает `c_obs <= D`.
- [x] Проверять non-interference: observer syncs только на broadcast channels.

## 13. Property pack generation

- [x] Реализовать `phy_property_pack.generate(contract_ir, profile)`.
- [x] Генерировать base safety: `A[] not deadlock`.
- [x] Генерировать reachability для всех значимых locations `A_PH`.
- [x] Генерировать aggregation consistency.
- [x] Генерировать classifier determinism properties: `ch_enabled_count <= 1`, `sq_enabled_count <= 1` при debug counters enabled.
- [x] Генерировать contract properties: `ass_i() imply not ContractViolation_i`.
- [x] Генерировать observer properties: `A[] not Obs*.Violation`.
- [x] Генерировать local invariants: `A[] (A_BM.BeamRecover imply c_rec <= D_BM)`.
- [x] Генерировать channel semantic checks as static report, не как UPPAAL query, если это синтаксическое свойство.
- [x] Генерировать negative property pack для intentionally broken models.
- [x] Сохранять queries как `.q` и как JSON с metadata/provenance.

## 14. Static semantic validators

- [x] Реализовать `phy_validate_contract_ir`.
- [x] Реализовать `phy_validate_generated_model`.
- [x] Проверять обязательные пять PHY templates.
- [x] Проверять обязательные четыре ENV templates.
- [x] Проверять обязательные observers при `with_observers`.
- [x] Проверять no continuous guards.
- [x] Проверять report/event broadcast semantics.
- [x] Проверять command handshake semantics.
- [x] Проверять single-sync-per-transition.
- [x] Проверять single writer для report variables и `PHYState`.
- [x] Проверять required inputs `A_SQ` и `A_PH`.
- [x] Проверять `A_SIG` waveform-not-location.
- [x] Проверять `A_BM` deadline semantics.
- [x] Проверять no unbounded leads-to used for bounded deadlines.
- [x] Проверять all classes in range.
- [x] Проверять all query references exist.
- [x] Проверять no dangling channels: command sender/receiver пары, broadcast senders/listeners.
- [x] Проверять reachability sanity по generated location names.

## 15. Verifyta integration extensions

- [ ] Расширить `uppaal_verify` options preset: normal verification, trace-on-violation, diagnostic run.
- [ ] Добавить safe support для verifyta trace generation flags после проверки конкретного UPPAAL 5.0 syntax.
- [x] Добавить `phy_verify_contract(tex_path|contract_ir|model_xml, profile, mode)`.
- [x] Добавить `phy_verify_property_pack(model, queries, explain=True)`.
- [x] Добавить timeout profile per scenario.
- [x] Добавить run metadata: UPPAAL version, verifyta command, profile hash, source TeX hash, generated model hash, query hash.
- [x] Добавить artifact layout:
  `artifacts/<run_id>/source.tex`, `contract.json`, `model.xml`, `queries.q`, `results.json`, `trace.*`, `report.md`.
- [x] Добавить cache key: source hash + profile + generator version + verifyta version + queries + options.
- [x] Добавить `force` для bypass cache.

## 16. Trace and counterexample explanation

- [x] Реализовать parser для verifyta counterexample trace output.
- [x] Нормализовать trace в события: time/delay, automaton, location, transition, sync, update, class values.
- [x] Сопоставлять UPPAAL instance/location с domain meaning: `A_BM.BeamRecover -> beam recovery in progress`, `A_SQ.FreshnessLimited -> stale sensing information`, и т.п.
- [x] Сопоставлять class values с физическим смыслом: `PdClass=FAILED`, `AoSClass=EXPIRED`, `BeamClass=FAILED`.
- [x] Выделять root-cause candidates: missing report, late report, invalid class priority, blocked handshake, impossible guard, environment assumption violation.
- [x] Классифицировать counterexample как `possible_physical_scenario`, `abstraction_artifact`, `modeling_error`, `environment_assumption_violation`, `unknown`.
- [x] Для abstraction artifact указывать, какие class combinations требуют replay на estimator/simulator layer.
- [x] Для modeling error указывать конкретный invariant/guard/channel mismatch.
- [x] Для deadline violation выводить trigger, expected response, deadline, actual path.
- [x] Для beam recovery выводить, какой outcome отсутствует или пришел поздно.
- [x] Для freshness выводить различие `AoS_BS` и `AoS_CTRL`, если оно видно из trace.
- [x] Генерировать compact explanation для MCP ответа.
- [x] Генерировать detailed Markdown report для артефактов.

## 17. MCP tool surface for PHY layer

- [x] Добавить `phy_extract_contract(tex_text?, tex_path?)`.
- [x] Добавить `phy_validate_contract(contract_json)`.
- [x] Добавить `phy_generate_uppaal_model(contract_json?, tex_text?, tex_path?, profile?, include_observers?)`.
- [x] Добавить `phy_generate_property_pack(contract_json?, model_xml?, profile?)`.
- [x] Добавить `phy_verify_contract(tex_path?, tex_text?, profile?, mode?)`.
- [x] Добавить `phy_check_no_continuous_guards(model_xml?, contract_json?)`.
- [x] Добавить `phy_check_channel_semantics(model_xml?, contract_json?)`.
- [x] Добавить `phy_check_alpha_profile(profile_json)`.
- [x] Добавить `phy_explain_counterexample(result_json, trace_text?, contract_json?)`.
- [x] Добавить `phy_export_report(run_id|result_json)`.
- [x] Добавить `phy_list_profiles()`.
- [x] Добавить `phy_get_profile(name)`.
- [x] Добавить `phy_list_scenarios()`.
- [x] Добавить `phy_verify_scenario(name, profile?)`.
- [x] Обновить `uppaal_list_examples()` так, чтобы PHY examples были видны отдельно.
- [x] Добавить MCP instructions: когда использовать generic `uppaal_verify`, а когда `phy_verify_contract`.

## 18. Reports and publication artifacts

- [x] Генерировать `report.md` с таблицей `Property | Query | Result | Interpretation | Source`.
- [x] Генерировать `traceability_matrix.md`: утверждение в статье -> IR entity -> UPPAAL template/query -> result.
- [x] Генерировать `model_summary.md`: templates, clocks, variables, channels, observers, queries.
- [x] Генерировать `violations.md` с explanations и suggested fixes.
- [x] Генерировать CSV/Markdown таблицы для статьи.
- [x] Генерировать `assume_guarantee_report.md`.
- [x] Генерировать `alpha_profile_report.md`.
- [x] Генерировать `coverage_report.md`: какие sections/automata/properties из `.tex` покрыты генератором и тестами.

## 19. Scenario and benchmark suite

- [x] Создать generated scenario `nominal_phy`.
- [x] Создать scenario `channel_outage`.
- [x] Создать scenario `interference_limited`.
- [x] Создать scenario `mobility_limited`.
- [x] Создать scenario `multipath_limited`.
- [x] Создать scenario `signal_reconfiguring`.
- [x] Создать scenario `signal_limited`.
- [x] Создать scenario `beam_recovery_success`.
- [x] Создать scenario `beam_handover_hint`.
- [x] Создать scenario `beam_failure_timeout`.
- [x] Создать scenario `sensing_probability_limited`.
- [x] Создать scenario `sensing_freshness_limited`.
- [x] Создать scenario `sensing_failure`.
- [x] Создать scenario `phy_communication_degraded`.
- [x] Создать scenario `phy_sensing_degraded`.
- [x] Создать scenario `phy_joint_degraded`.
- [x] Создать intentionally broken scenario: report channel declared as `chan`.
- [x] Создать intentionally broken scenario: continuous guard in automaton.
- [x] Создать intentionally broken scenario: `c_rec > D_BM`.
- [x] Создать intentionally broken scenario: `PHYState` written outside `A_PH`.
- [x] Создать intentionally broken scenario: missing `A_ENV`.

## 20. Tests

- [x] Unit tests для LaTeX extractor.
- [x] Unit tests для IR schema validation.
- [x] Unit tests для alpha registry.
- [x] Unit tests для UPPAAL XML builder.
- [x] Unit tests для channel semantics validator.
- [x] Unit tests для each automaton generator.
- [x] Unit tests для observer generator.
- [x] Unit tests для property pack generator.
- [x] Unit tests для trace parser.
- [x] Golden tests: current `.tex` -> expected `contract.json`.
- [x] Golden tests: current `.tex` -> generated `model.xml`.
- [x] Golden tests: current `.tex` -> generated `queries.q`.
- [ ] Verifyta smoke tests for minimal closed model.
- [ ] Verifyta smoke tests for each scenario.
- [ ] Negative tests for each semantic validator.
- [x] Regression tests for MCP tool JSON shapes.
- [x] Test that generic MVP tools still work after PHY layer additions.

## 21. Documentation

- [x] Обновить README: current MVP vs PHY layer.
- [x] Добавить `docs/phy_layer_usage.md`.
- [x] Добавить пример Codex prompt: extract contract from TeX, generate model, verify, explain result.
- [x] Добавить пример direct CLI run without MCP.
- [x] Добавить пример MCP tool calls.
- [x] Добавить описание profiles.
- [x] Добавить описание artifacts layout.
- [x] Добавить limitations: no radiophysics proof, no probability distribution proof, no parameter synthesis, no `Pi_PHY` optimization in base mode.
- [x] Добавить troubleshooting: UPPAAL path, Windows/WSL paths, trace generation, timeouts, invalid queries.

## 22. Definition of Done

- [x] Из текущего `PHY_level_formalization_reviewed-2026-06-06-143000.tex` автоматически строится `contract.json`.
- [x] Из `contract.json` автоматически строится `model.xml`.
- [x] Generated `model.xml` содержит `A_CH`, `A_SIG`, `A_BM`, `A_SQ`, `A_PH`, `ENV_CH`, `ENV_TARGET`, `ENV_MAC`, `ENV_NET`.
- [x] Generated `model.xml` содержит observers для bounded report, freshness и beam recovery.
- [x] Generated `queries.q` содержит базовые reachability/safety/contract/observer properties из статьи.
- [x] Static validators проходят на корректной модели.
- [x] Static validators ловят все intentionally broken cases.
- [ ] `verifyta` успешно запускается на generated closed model.
- [x] MCP tool `phy_verify_contract` возвращает structured JSON, artifact paths и compact explanation.
- [x] При нарушении свойства MCP объясняет counterexample в терминах PHY/SDN/ISAC, а не только отдает сырой stdout.
- [x] README содержит рабочий путь использования из Codex через VS Code/WSL.

## 23. Порядок реализации

1. IR schema + ручной fixture `contract.json` для текущей статьи.
2. XML generator из fixture без extractor.
3. `A_ENV` + closed `A_SYS`.
4. Property pack + observers.
5. Static validators.
6. Verifyta integration + reports.
7. LaTeX extractor.
8. Trace parser/explanation.
9. Scenario benchmark suite.
10. MCP tool polish and docs.

Причина такого порядка простая: сначала надо доказать, что целевая UPPAAL-модель вообще исполнима и проверяема. Extractor из LaTeX имеет смысл делать после того, как IR и generator уже стабилизированы.
