# SDN/RIC-Specific MCP Layer Tasks

Цель: масштабировать PHY/MAC-specific MCP подход на
`SDN_RIC_control_plane_formalization.tex`.

Итоговый SDN/RIC-слой должен уметь извлекать контракт из LaTeX, строить
проверяемую UPPAAL-модель `A_SYS_SDN = A_SDN || A_ENV_SDN`, генерировать
property pack, валидировать SDN/RIC-семантику, запускать `verifyta`, объяснять
counterexample и не ломать уже готовые PHY/MAC-слои.

## 0. Инварианты SDN/RIC-слоя

- [ ] `A_SDN = A_MON || A_RISK || A_POLICY || A_RULE || A_REC || A_SDN_AGG`.
- [ ] Closed-system default: `A_SYS_SDN = A_SDN || A_ENV_SDN`.
- [ ] `A_ENV_SDN` моделирует только локальную проекцию среды: `mac_report`,
  `phy_kpi_report`, `service_request`, `rule_miss`, `link_failure`,
  `node_failure`, `ack`.
- [ ] `A_SEC` не входит в базовый `A_SDN`; только optional extension.
- [ ] SDN/RIC не является AI-agent, MAC scheduler или PHY estimator.
- [ ] Guards используют только finite classes, bounded ints, booleans и clocks.
- [ ] Raw metrics, stochastic rates, recovery cost и optimization scores не
  используются в ordinary timed automata guards.
- [ ] `TEL_STALE` или `TEL_MISSING` запрещают `optimistic_reconfig`.
- [ ] Rule miss всегда завершается `flow_mod/forward`, `drop_report` или
  `timeout_report`.
- [ ] Service admission всегда завершается `service_accept`,
  `service_degraded` или `service_reject`.
- [ ] Recovery всегда завершается stable config, rollback или explicit failure.
- [ ] Bounded deadlines проверяются observer-автоматами, а не unbounded
  leads-to.
- [ ] Каждый transition edge имеет не больше одного sync label.

## 1. Layer Integration

- [ ] Добавить пакет `src/uppaal_mcp/sdn/` по паттерну `phy/` и `mac/`.
- [ ] Зарегистрировать SDN/RIC в reusable `LayerAdapter`.
- [ ] Сохранить PHY/MAC API и тесты без регресса.
- [ ] Зафиксировать source default:
  `SDN_RIC_control_plane_formalization.tex`.

## 2. Contract IR

- [ ] Описать `SdnContractModel`: classes, clocks, variables, channels,
  automata, env, observers, policies, interface procedures, properties,
  contracts, provenance.
- [ ] Зафиксировать canonical templates: `A_MON`, `A_RISK`, `A_POLICY`,
  `A_RULE`, `A_REC`, `A_SDN_AGG`, `A_ENV_SDN`.
- [ ] Зафиксировать classes: `TelemetryClass`, `RiskClass`, `PolicyClass`,
  `RuleClass`, `RecoveryClass`, `SliceClass`, `ServiceImpact`, `SdnReason`.
- [ ] Зафиксировать clocks: `c_mon`, `c_dec`, `c_rule`, `c_ctrl_ack`,
  `c_rec`, `c_rollback`, `c_admission`, optional `c_sec_ack`.
- [ ] Добавить JSON serialization и golden fixture
  `tests/fixtures/sdn_contract_article.golden.json`.
- [ ] Валидировать обязательные автоматы, channels, policies, observers,
  properties и source provenance.

## 3. LaTeX Extractor

- [ ] Реализовать section-aware extractor для SDN/RIC tex.
- [ ] Извлекать композиции `A_SDN`, `A_SYS_SDN`, `A_ENV_SDN`.
- [ ] Извлекать `alpha_SDN`, finite class domains и declarations block.
- [ ] Извлекать policy guards: `gPolConstrained`, `gPolReject`,
  `gPolReroute`, `gPolSensingBoost`, `gPolCommPrio`, `reconfig_allowed`.
- [ ] Извлекать locations/invariants/edge sketches для всех `A_*`.
- [ ] Извлекать interface table: rule miss, recovery, sensing degradation,
  service admission.
- [ ] Извлекать assumptions, guarantees, limitations, observers и queries.
- [ ] Добавить diagnostics: missing section, ambiguous class, incomplete
  policy, duplicate location, unsupported LaTeX construct.

## 4. Alpha/Profile Layer

- [ ] Реализовать SDN class registry и UPPAAL declarations.
- [ ] Валидировать deadline profile: `D_mon`, `D_decision`,
  `D_rule_install`, `D_rule_ack`, `D_ctrl_ack`, `D_recovery`, `D_rollback`,
  `D_admission`, `D_sec_ack`.
- [ ] Добавить profiles: `default`, `conservative_safety`, `stress`.
- [ ] Проверять conservative policy: stale/missing telemetry cannot choose
  optimistic reroute or sensing boost.
- [ ] Запретить raw/continuous guard tokens: raw queue length, raw delay,
  raw SINR/CRB/Pd/Rfa, packet rates, recovery probability, expected cost.

## 5. UPPAAL Generation

- [ ] Генерировать declarations, templates, instances, system declaration и
  optional queries структурным XML API.
- [ ] Генерировать `A_MON`: freshness collection and missing/stale states.
- [ ] Генерировать `A_RISK`: deterministic risk classification.
- [ ] Генерировать `A_POLICY`: policy selection and service impact update.
- [ ] Генерировать `A_RULE`: rule miss, install, ack, drop, timeout.
- [ ] Генерировать `A_REC`: link/node failure, standby, reembedding,
  rollback, recovery failure.
- [ ] Генерировать `A_SDN_AGG`: command build, send, await ack, timeout.
- [ ] Генерировать `A_ENV_SDN` with bounded nondeterministic scenarios.
- [ ] Поддержать modes: `minimal`, `with_observers`, `with_debug_counters`,
  `with_negative_scenarios`, `with_optional_sec`, `open_system`.
- [ ] Поддержать layouts: `readable`, `compact`; генерировать maps:
  `model_map.md`, `template_map.md`, `channels_map.md`, `policy_map.md`,
  `interface_map.md`.
- [ ] Добавить Graphviz/SVG export.

## 6. Static Validators

- [ ] Проверять required templates/instances/init locations.
- [ ] Проверять channel semantics: broadcasts for reports/outcomes, handshakes
  for commands/ack/failure paths, one sync per edge.
- [ ] Проверять no raw metric guards.
- [ ] Проверять bounded domains for all SDN classes.
- [ ] Проверять policy completeness and deterministic priority:
  reject, constrained stale, reroute, sensing boost, comm priority, normal.
- [ ] Проверять stale telemetry invariant:
  `A[] (telemetryClass == TEL_STALE imply !optimistic_reconfig)`.
- [ ] Проверять explicit outcomes for rule miss, admission, recovery and
  sensing degradation.
- [ ] Проверять single-writer policy for `policyClass`, `serviceImpact`,
  `sdnReason`, `optimistic_reconfig`, pending flags.
- [ ] Проверять observer shape: waiting locations without deadline invariant,
  violation only on `x > D`, success on allowed outcomes.
- [ ] Проверять query references and readable layout.

## 7. Observers and Properties

- [ ] Генерировать `ObsRuleMiss`.
- [ ] Генерировать `ObsRecovery`.
- [ ] Генерировать `ObsAdmission`.
- [ ] Генерировать `ObsStaleTelemetry`.
- [ ] Генерировать optional `ObsCommandAck`, `ObsSensingDecision`,
  `ObsSecAck`.
- [ ] Генерировать property pack: deadlock, observer safety, stale telemetry,
  local invariants, reachability, policy consistency.
- [ ] Сохранять `queries.q`, `queries.json`, `property_pack.json` and negative
  property pack metadata.

## 8. Reports, Artifacts, Trace Explanation

- [ ] Генерировать `report.md`, `traceability_matrix.md`,
  `model_summary.md`, `alpha_profile_report.md`, `coverage_report.md`,
  `policy_report.md`, `interface_report.md`, `properties.csv`.
- [ ] Генерировать run artifact layout with source, contract, model, queries,
  results, trace, metadata and cache key.
- [ ] Объяснять counterexamples: stale optimistic reconfig, rule timeout,
  missing admission outcome, recovery failure, blocked ack, impossible policy,
  wrong channel semantics.

## 9. CLI and MCP Tools

- [ ] CLI: `sdn-extract`, `sdn-generate`, `sdn-export-diagram`,
  `sdn-property-pack`, `sdn-report`, `sdn-run-artifacts`, `sdn-verify`,
  `sdn-verify-property-pack`, `sdn-list-scenarios`, `sdn-scenario`,
  `sdn-verify-scenario`, `sdn-verify-all-scenarios`, `sdn-list-benchmarks`,
  `sdn-benchmark`, `sdn-validate-benchmarks`.
- [ ] MCP: `sdn_extract_contract`, `sdn_validate_contract`,
  `sdn_generate_uppaal_model`, `sdn_validate_layout`,
  `sdn_export_diagram`, `sdn_generate_property_pack`,
  `sdn_export_property_pack`, `sdn_generate_report`, `sdn_export_report`,
  `sdn_export_run_artifacts`, `sdn_verify_contract`,
  `sdn_verify_property_pack`, `sdn_check_alpha_profile`,
  `sdn_check_channel_semantics`, `sdn_explain_counterexample`,
  `sdn_list_scenarios`, `sdn_get_scenario`, `sdn_verify_scenario`,
  `sdn_verify_all_scenarios`, `sdn_list_benchmarks`, `sdn_get_benchmark`,
  `sdn_validate_benchmarks`.
- [ ] Обновить `COMMAND_REFERENCE.md` и README only after tools exist.

## 10. Benchmarks and Tests

- [ ] Positive benchmarks: `nominal_sdn`, `rule_miss_install`,
  `rule_miss_drop`, `rule_timeout`, `stale_telemetry_constrained`,
  `sensing_degradation_boost`, `sensing_degradation_reject`,
  `service_admission_accept`, `service_admission_degraded`,
  `service_admission_reject`, `link_failure_standby`,
  `node_failure_reembedding`, `recovery_rollback`, `recovery_failed`,
  `command_ack_timeout`.
- [ ] Broken benchmarks: wrong channel semantics, raw metric guard,
  missing `A_ENV_SDN`, stale optimistic reconfig, missing rule miss outcome,
  missing admission outcome, missing ack timeout, incomplete policy table,
  `A_SEC` forced into base model.
- [ ] Golden fixtures: contract JSON, generated XML, readable XML, queries.
- [ ] Unit tests for extractor/generator/property pack/layout/reports/static
  validators.
- [ ] CLI and MCP smoke checks.

## Definition of Done

- [ ] `sdn-extract --tex SDN_RIC_control_plane_formalization.tex` returns
  validated contract JSON.
- [ ] `sdn-generate --layout readable --output-dir ...` writes model, queries,
  contract and maps.
- [ ] `sdn-property-pack --include-negative --output-dir ...` writes query
  metadata.
- [ ] `sdn-verify-property-pack --static-only` passes.
- [ ] `sdn-validate-benchmarks` passes with expected positive/broken split.
- [ ] MCP tools expose the same workflow as CLI.
- [ ] Existing PHY and MAC tests still pass.
