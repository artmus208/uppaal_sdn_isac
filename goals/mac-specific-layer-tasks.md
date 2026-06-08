# MAC-Specific MCP Layer Tasks

Цель: масштабировать текущий PHY-specific MCP подход на
`MAC_resource_scheduling_formalization.tex`.

Итоговый MAC-слой должен уметь извлекать контракт из LaTeX, строить UPPAAL-модель
`A_SYS_MAC = A_MAC || A_ENV_MAC`, генерировать property pack, валидировать
MAC-семантику, запускать `verifyta`, объяснять counterexample и готовить основу
для следующих уровней SDN/RIC и Application.

## 0. Инварианты MAC-слоя

- [x] MAC не выполняет SDN rerouting, slice migration, global recovery или admission control.
- [x] MAC принимает только конечные PHY/MAC/SDN классы, а не сырые измерения.
- [x] Continuous MAC metrics не используются в UPPAAL guards.
- [x] Closed-system default: `A_SYS_MAC = A_MAC || A_ENV_MAC`.
- [x] `A_MAC = A_SCH || A_Q || A_BUF || A_RSRC || A_MAC_AGG`.
- [x] `mac_report` и `phy_kpi_report` объявляются как `broadcast chan`.
- [x] Command/ack channels объявляются как обычные `chan`.
- [x] Bounded guarantees проверяются observers, а не unbounded leads-to.

## 1. Reusable Layer Framework

- [x] Ввести общий layer contract shape: `layer_id`, `contract_ir`, extractor hooks, generator hooks, validators, reports, scenarios.
- [x] Оставить PHY рабочим baseline без регресса.
- [x] Добавить MAC как второй concrete layer без копирования PHY-кода вслепую.
- [x] Подготовить extension points для будущих SDN/RIC и Application layers.

## 2. MAC Contract IR

- [x] Описать `MacContractModel`: classes, channels, clocks, variables, automata, env, observers, properties, policies, reports, provenance.
- [x] Зафиксировать canonical template names: `A_SCH`, `A_Q`, `A_BUF`, `A_RSRC`, `A_MAC_AGG`, `A_ENV_MAC`.
- [x] Зафиксировать canonical observer names: `ObsPhyAck`, `ObsQueueCritical`, `ObsSensingCritical`, optional `ObsBufferOverflow`, `ObsMacReportFreshness`.
- [x] Добавить JSON serialization для отладки MCP tools.
- [x] Добавить schema validation для обязательных автоматов, clocks, channels, policies, observers и properties.

## 3. LaTeX Extractor

- [x] Реализовать section-aware extractor для `MAC_resource_scheduling_formalization.tex`.
- [x] Извлекать composition `A_MAC`.
- [x] Извлекать closed-system projection `A_SYS_MAC`.
- [x] Извлекать `alpha_MAC`, finite classes, class domains и conservative boundary policy.
- [x] Извлекать `mu_PHY->MAC` mapping и strictest-class priority.
- [x] Извлекать declarations: constants, clocks, channels, typedefs, shared variables.
- [x] Извлекать MAC policy table `P0..P7`.
- [x] Извлекать generated guard helpers `gP0..gP7`.
- [x] Извлекать locations/invariants/edge sketches для `A_SCH/A_Q/A_BUF/A_RSRC/A_MAC_AGG`.
- [x] Извлекать assumptions, guarantees, report interface и verification properties.
- [x] Добавить diagnostics: missing section, ambiguous policy, duplicate location, unsupported LaTeX construct.

## 4. Alpha MAC

- [x] Реализовать MAC class registry.
- [x] Генерировать UPPAAL declarations для MAC finite classes.
- [x] Валидировать profile/deadlines: `D_collect`, `D_sched`, `D_phy_ack`, `D_queue_crit`, `D_buf_report`, `D_mac_report`, `D_phy_report`.
- [x] Запретить raw continuous/counter tokens в guards: queue length samples, delay samples, loss rate, utilization, HARQ counters.
- [x] Проверять bounded domains for all MAC classes.
- [x] Проверять conservative boundary policy.

## 5. UPPAAL Generation

- [x] Генерировать declarations из MAC IR.
- [x] Генерировать `A_SCH`: `Idle`, `CollectKPI`, `SelectMode`, `ApplySchedule`, `WaitPHYAck`, `ScheduleFailure`.
- [x] Генерировать `A_Q`: `QueueNormal`, `QueueWarning`, `QueueCritical`, `QueueDraining`.
- [x] Генерировать `A_BUF`: `BufferSafe`, `BufferWarning`, `BufferOverflow`.
- [x] Генерировать `A_RSRC`: `ResourceAvailable`, `ResourceTight`, `ResourceConflict`, `ResourceExhausted`.
- [x] Генерировать `A_MAC_AGG`: `ReportIdle`, `ReportBuild`, `ReportSent`, `ReportStale`.
- [x] Генерировать `A_ENV_MAC`: `mac_tick!`, `phy_kpi_report!`, `sdn_policy_cmd!`, `service_priority!`, `phy_ack!`.
- [x] Генерировать `system A_SCH, A_Q, A_BUF, A_RSRC, A_MAC_AGG, A_ENV_MAC, ...;`.
- [x] Поддержать `minimal`, `with_observers`, `with_debug_counters`, `with_negative_scenarios`.
- [x] Добавить readable layout and compact layout.
- [x] Генерировать `model_map.md`, `template_map.md`, `channels_map.md`, `policy_map.md`.
- [x] Добавить Graphviz/SVG export.

## 6. Static Validators

- [x] Проверять required templates and init locations.
- [x] Проверять report/event broadcast semantics.
- [x] Проверять command/ack handshake semantics.
- [x] Проверять one sync label per transition.
- [x] Проверять no continuous MAC metrics in guards.
- [x] Проверять single-writer policy for `scheduleMode`, `macReason`, `mac_report_pending`, `silent_accept`.
- [x] Проверять no silent accept when `ResourceClass=RES_EXHAUSTED`.
- [x] Проверять PHY command completion: `phy_ack?` до `D_phy_ack` или `ScheduleFailure/mac_report!`.
- [x] Проверять queue critical bounded response.
- [x] Проверять buffer overflow bounded report.
- [x] Проверять sensing critical bounded response.
- [x] Проверять layout collapse, label density, readable violation/report zones.

## 7. Observers and Properties

- [x] Генерировать `ObsPhyAck`.
- [x] Генерировать `ObsQueueCritical`.
- [x] Генерировать `ObsSensingCritical`.
- [x] Генерировать optional `ObsBufferOverflow`.
- [x] Генерировать optional `ObsMacReportFreshness`.
- [x] Генерировать property pack: deadlock, observer safety, no silent accept, local invariants, reachability.
- [x] Сохранять `queries.q` and `queries.json` with metadata/provenance.
- [x] Генерировать negative property pack for intentionally broken models.

## 8. Reports, Artifacts, Trace Explanation

- [x] Добавить MAC reports: `report.md`, `traceability_matrix.md`, `alpha_profile_report.md`, `coverage_report.md`, `policy_report.md`, `properties.csv`.
- [x] Добавить run artifact layout with source, contract, model, queries, results, trace, metadata and cache key.
- [x] Объяснять MAC counterexamples: stale KPI, missed PHY ack, queue critical timeout, buffer overflow, resource exhaustion, blocked handshake.
- [x] Добавить compact root-cause classification: physical/input scenario, environment assumption violation, modeling error, abstraction artifact, unknown.

## 9. MCP Tools and CLI

- [x] MCP: `mac_extract_contract`.
- [x] MCP: `mac_validate_contract`.
- [x] MCP: `mac_generate_uppaal_model`.
- [x] MCP: `mac_generate_property_pack`.
- [x] MCP: `mac_verify_contract`.
- [x] MCP: `mac_verify_property_pack`.
- [x] MCP: `mac_check_alpha_profile`.
- [x] MCP: `mac_check_channel_semantics`.
- [x] MCP: `mac_validate_layout`.
- [x] MCP: `mac_export_diagram`.
- [x] MCP: `mac_explain_counterexample`.
- [x] MCP: `mac_list_scenarios`.
- [x] MCP: `mac_validate_benchmarks`.
- [x] CLI: `mac-extract`.
- [x] CLI: `mac-generate`.
- [x] CLI: `mac-property-pack`.
- [x] CLI: `mac-report`.
- [x] CLI: `mac-run-artifacts`.
- [x] CLI: `mac-verify`.
- [x] CLI: `mac-verify-property-pack`.
- [x] CLI: `mac-list-scenarios`.
- [x] CLI: `mac-scenario`.
- [x] CLI: `mac-verify-all-scenarios`.
- [x] CLI: `mac-list-benchmarks`.
- [x] CLI: `mac-validate-benchmarks`.
- [x] CLI: `mac-export-diagram`.

## 10. Benchmarks and Tests

- [x] Добавить benchmarks: nominal, queue critical, buffer overflow, resource exhausted, stale PHY KPI, sensing conflict, PHY ack timeout.
- [x] Добавить broken benchmarks: wrong channel semantics, continuous guard, missing `A_ENV_MAC`, silent accept, missing ack timeout path.
- [x] Добавить golden fixtures: `mac_contract_article.golden.json`, `mac_model_article.golden.xml`, `mac_model_article.readable.golden.xml`, `mac_queries_article.golden.q`.
- [x] Добавить unit tests for extractor/generator/property pack/layout/reports/static validators.
- [x] Добавить CLI smoke tests.
- [x] Добавить MCP smoke checks.

## Definition of Done

- [x] `mac-generate --tex MAC_resource_scheduling_formalization.tex --layout readable` пишет readable `model.xml`, `queries.q`, `contract.json` and maps.
- [x] Static validation passes for generated MAC model.
- [x] `mac-verify-property-pack --static-only` passes.
- [x] MAC benchmark suite distinguishes positive and intentionally broken scenarios.
- [x] MAC reports explain automata, policies, channels and failed traces in domain terms.
- [x] Existing PHY tests and tools still pass.
