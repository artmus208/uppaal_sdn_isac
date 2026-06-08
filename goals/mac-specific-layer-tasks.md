# MAC-Specific MCP Layer Tasks

Цель: масштабировать текущий PHY-specific MCP подход на
`MAC_resource_scheduling_formalization.tex`.

Итоговый MAC-слой должен уметь извлекать контракт из LaTeX, строить UPPAAL-модель
`A_SYS_MAC = A_MAC || A_ENV_MAC`, генерировать property pack, валидировать
MAC-семантику, запускать `verifyta`, объяснять counterexample и готовить основу
для следующих уровней SDN/RIC и Application.

## 0. Инварианты MAC-слоя

- [ ] MAC не выполняет SDN rerouting, slice migration, global recovery или admission control.
- [ ] MAC принимает только конечные PHY/MAC/SDN классы, а не сырые измерения.
- [ ] Continuous MAC metrics не используются в UPPAAL guards.
- [ ] Closed-system default: `A_SYS_MAC = A_MAC || A_ENV_MAC`.
- [ ] `A_MAC = A_SCH || A_Q || A_BUF || A_RSRC || A_MAC_AGG`.
- [ ] `mac_report` и `phy_kpi_report` объявляются как `broadcast chan`.
- [ ] Command/ack channels объявляются как обычные `chan`.
- [ ] Bounded guarantees проверяются observers, а не unbounded leads-to.

## 1. Reusable Layer Framework

- [ ] Ввести общий layer contract shape: `layer_id`, `contract_ir`, extractor hooks, generator hooks, validators, reports, scenarios.
- [ ] Оставить PHY рабочим baseline без регресса.
- [ ] Добавить MAC как второй concrete layer без копирования PHY-кода вслепую.
- [ ] Подготовить extension points для будущих SDN/RIC и Application layers.

## 2. MAC Contract IR

- [ ] Описать `MacContractModel`: classes, channels, clocks, variables, automata, env, observers, properties, policies, reports, provenance.
- [ ] Зафиксировать canonical template names: `A_SCH`, `A_Q`, `A_BUF`, `A_RSRC`, `A_MAC_AGG`, `A_ENV_MAC`.
- [ ] Зафиксировать canonical observer names: `ObsPhyAck`, `ObsQueueCritical`, `ObsSensingCritical`, optional `ObsBufferOverflow`, `ObsMacReportFreshness`.
- [ ] Добавить JSON serialization для отладки MCP tools.
- [ ] Добавить schema validation для обязательных автоматов, clocks, channels, policies, observers и properties.

## 3. LaTeX Extractor

- [ ] Реализовать section-aware extractor для `MAC_resource_scheduling_formalization.tex`.
- [ ] Извлекать composition `A_MAC`.
- [ ] Извлекать closed-system projection `A_SYS_MAC`.
- [ ] Извлекать `alpha_MAC`, finite classes, class domains и conservative boundary policy.
- [ ] Извлекать `mu_PHY->MAC` mapping и strictest-class priority.
- [ ] Извлекать declarations: constants, clocks, channels, typedefs, shared variables.
- [ ] Извлекать MAC policy table `P0..P7`.
- [ ] Извлекать generated guard helpers `gP0..gP7`.
- [ ] Извлекать locations/invariants/edge sketches для `A_SCH/A_Q/A_BUF/A_RSRC/A_MAC_AGG`.
- [ ] Извлекать assumptions, guarantees, report interface и verification properties.
- [ ] Добавить diagnostics: missing section, ambiguous policy, duplicate location, unsupported LaTeX construct.

## 4. Alpha MAC

- [ ] Реализовать MAC class registry.
- [ ] Генерировать UPPAAL declarations для MAC finite classes.
- [ ] Валидировать profile/deadlines: `D_collect`, `D_sched`, `D_phy_ack`, `D_queue_crit`, `D_buf_report`, `D_mac_report`, `D_phy_report`.
- [ ] Запретить raw continuous/counter tokens в guards: queue length samples, delay samples, loss rate, utilization, HARQ counters.
- [ ] Проверять bounded domains for all MAC classes.
- [ ] Проверять conservative boundary policy.

## 5. UPPAAL Generation

- [ ] Генерировать declarations из MAC IR.
- [ ] Генерировать `A_SCH`: `Idle`, `CollectKPI`, `SelectMode`, `ApplySchedule`, `WaitPHYAck`, `ScheduleFailure`.
- [ ] Генерировать `A_Q`: `QueueNormal`, `QueueWarning`, `QueueCritical`, `QueueDraining`.
- [ ] Генерировать `A_BUF`: `BufferSafe`, `BufferWarning`, `BufferOverflow`.
- [ ] Генерировать `A_RSRC`: `ResourceAvailable`, `ResourceTight`, `ResourceConflict`, `ResourceExhausted`.
- [ ] Генерировать `A_MAC_AGG`: `ReportIdle`, `ReportBuild`, `ReportSent`, `ReportStale`.
- [ ] Генерировать `A_ENV_MAC`: `mac_tick!`, `phy_kpi_report!`, `sdn_policy_cmd!`, `service_priority!`, `phy_ack!`.
- [ ] Генерировать `system A_SCH, A_Q, A_BUF, A_RSRC, A_MAC_AGG, A_ENV_MAC, ...;`.
- [ ] Поддержать `minimal`, `with_observers`, `with_debug_counters`, `with_negative_scenarios`.
- [ ] Добавить readable layout and compact layout.
- [ ] Генерировать `model_map.md`, `template_map.md`, `channels_map.md`, `policy_map.md`.
- [ ] Добавить Graphviz/SVG export.

## 6. Static Validators

- [ ] Проверять required templates and init locations.
- [ ] Проверять report/event broadcast semantics.
- [ ] Проверять command/ack handshake semantics.
- [ ] Проверять one sync label per transition.
- [ ] Проверять no continuous MAC metrics in guards.
- [ ] Проверять single-writer policy for `scheduleMode`, `macReason`, `mac_report_pending`, `silent_accept`.
- [ ] Проверять no silent accept when `ResourceClass=RES_EXHAUSTED`.
- [ ] Проверять PHY command completion: `phy_ack?` до `D_phy_ack` или `ScheduleFailure/mac_report!`.
- [ ] Проверять queue critical bounded response.
- [ ] Проверять buffer overflow bounded report.
- [ ] Проверять sensing critical bounded response.
- [ ] Проверять layout collapse, label density, readable violation/report zones.

## 7. Observers and Properties

- [ ] Генерировать `ObsPhyAck`.
- [ ] Генерировать `ObsQueueCritical`.
- [ ] Генерировать `ObsSensingCritical`.
- [ ] Генерировать optional `ObsBufferOverflow`.
- [ ] Генерировать optional `ObsMacReportFreshness`.
- [ ] Генерировать property pack: deadlock, observer safety, no silent accept, local invariants, reachability.
- [ ] Сохранять `queries.q` and `queries.json` with metadata/provenance.
- [ ] Генерировать negative property pack for intentionally broken models.

## 8. Reports, Artifacts, Trace Explanation

- [ ] Добавить MAC reports: `report.md`, `traceability_matrix.md`, `alpha_profile_report.md`, `coverage_report.md`, `policy_report.md`, `properties.csv`.
- [ ] Добавить run artifact layout with source, contract, model, queries, results, trace, metadata and cache key.
- [ ] Объяснять MAC counterexamples: stale KPI, missed PHY ack, queue critical timeout, buffer overflow, resource exhaustion, blocked handshake.
- [ ] Добавить compact root-cause classification: physical/input scenario, environment assumption violation, modeling error, abstraction artifact, unknown.

## 9. MCP Tools and CLI

- [ ] MCP: `mac_extract_contract`.
- [ ] MCP: `mac_validate_contract`.
- [ ] MCP: `mac_generate_uppaal_model`.
- [ ] MCP: `mac_generate_property_pack`.
- [ ] MCP: `mac_verify_contract`.
- [ ] MCP: `mac_verify_property_pack`.
- [ ] MCP: `mac_check_alpha_profile`.
- [ ] MCP: `mac_check_channel_semantics`.
- [ ] MCP: `mac_validate_layout`.
- [ ] MCP: `mac_export_diagram`.
- [ ] MCP: `mac_explain_counterexample`.
- [ ] MCP: `mac_list_scenarios`.
- [ ] MCP: `mac_validate_benchmarks`.
- [ ] CLI: `mac-extract`.
- [ ] CLI: `mac-generate`.
- [ ] CLI: `mac-property-pack`.
- [ ] CLI: `mac-report`.
- [ ] CLI: `mac-run-artifacts`.
- [ ] CLI: `mac-verify`.
- [ ] CLI: `mac-verify-property-pack`.
- [ ] CLI: `mac-list-scenarios`.
- [ ] CLI: `mac-scenario`.
- [ ] CLI: `mac-verify-all-scenarios`.
- [ ] CLI: `mac-list-benchmarks`.
- [ ] CLI: `mac-validate-benchmarks`.
- [ ] CLI: `mac-export-diagram`.

## 10. Benchmarks and Tests

- [ ] Добавить benchmarks: nominal, queue critical, buffer overflow, resource exhausted, stale PHY KPI, sensing conflict, PHY ack timeout.
- [ ] Добавить broken benchmarks: wrong channel semantics, continuous guard, missing `A_ENV_MAC`, silent accept, missing ack timeout path.
- [ ] Добавить golden fixtures: `mac_contract_article.golden.json`, `mac_model_article.golden.xml`, `mac_model_article.readable.golden.xml`, `mac_queries_article.golden.q`.
- [ ] Добавить unit tests for extractor/generator/property pack/layout/reports/static validators.
- [ ] Добавить CLI smoke tests.
- [ ] Добавить MCP smoke checks.

## Definition of Done

- [ ] `mac-generate --tex MAC_resource_scheduling_formalization.tex --layout readable` пишет readable `model.xml`, `queries.q`, `contract.json` and maps.
- [ ] Static validation passes for generated MAC model.
- [ ] `mac-verify-property-pack --static-only` passes.
- [ ] MAC benchmark suite distinguishes positive and intentionally broken scenarios.
- [ ] MAC reports explain automata, policies, channels and failed traces in domain terms.
- [ ] Existing PHY tests and tools still pass.
