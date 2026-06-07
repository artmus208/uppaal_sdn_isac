# PHY-Specific Layer Progress

Дата: 2026-06-07.

Цель полного backlog-а остается открытой: `PHY_SPECIFIC_LAYER_TASKS.md` описывает весь переход от MVP к PHY-specific assistant. Текущий commit/срез реализует фундамент, но не закрывает весь список задач.

## Реализовано в первом срезе

- `PhyContractModel` IR для статьи.
- Canonical article fixture через `build_default_contract()`.
- IR schema now includes `VariableSpec` and `EnvSpec` in addition to PHY automata, clocks, channels, observers, properties and contracts.
- Section-aware `phy_extract_contract(...)`:
  - извлекает структуру секций;
  - извлекает verbatim-блоки;
  - извлекает формулы композиции `A_PHY`, `A_SYS`, `A_ENV`;
  - извлекает ordered `X_disc` и 28 finite class sets из `align`-блоков;
  - извлекает 9 clocks с reset semantics из таблицы clocks;
  - извлекает 5 ключевых invariants: `MeasurePending`, `SignalReconfiguring`, `SensingEvaluating`, `PHYKpiReporting`, `BeamRecover`;
  - извлекает 45 channel declarations;
  - извлекает locations и transition sketches для `A_CH`, `A_SIG`, `A_BM`, `A_SQ`, `A_PH`;
  - извлекает behavior sketches для `ENV_CH`, `ENV_TARGET`, `ENV_MAC`, `ENV_NET`;
  - извлекает assume/guarantee таблицу для пяти PHY-автоматов и predicate evidence из verification-блока;
  - извлекает 17 property queries;
  - строит marker/line evidence для `A_PHY`, `A_ENV`, `A_SYS`, `alpha_PHY`, `A_CH/A_SIG/A_BM/A_SQ/A_PH`, `ENV_*`, observers и `Pi_PHY`;
  - возвращает diagnostics/coverage в `contract["extractor"]`.
- `alpha_PHY` registry:
  - список finite classes;
  - UPPAAL declarations;
  - запрет continuous guard tokens;
  - boundary-policy check with conservative `worse_class` requirement for safety-critical classes;
  - built-in profiles `default`, `conservative_safety`, `stress`;
  - простая демонстрационная `classify_sample(...)`.
- UPPAAL XML generator:
  - `A_CH`, `A_SIG`, `A_BM`, `A_SQ`, `A_PH`;
  - `ENV_CH`, `ENV_TARGET`, `ENV_MAC`, `ENV_NET`;
  - `ObsSenseReport`, `ObsFreshness`, `ObsBeamRecovery`;
  - closed `A_SYS`;
  - generation modes: `minimal`, `with_observers`, `with_debug_counters`, `with_negative_scenarios`;
  - generated query pack.
- Static semantic validators:
  - required PHY/ENV/observer templates;
  - broadcast reports/events;
  - handshake commands;
  - no continuous guards;
  - one sync per transition;
  - waveform-not-location for `A_SIG`;
  - `PHYState` single-writer;
  - `BeamRecover` no `c_rec > D_BM`;
  - observer wait locations have no `c_obs <= D` invariant;
  - observer syncs are passive `?` syncs over broadcast channels;
  - required inputs for `A_SQ` and `A_PH`.
  - generated priority helpers `highest_priority_CH()` and `highest_priority_SQ()` exist and are used.
  - `BeamRecover` has `beam_restored!`, `handover_hint!`, `beam_failure!` outcomes and `beam_failure!` uses `c_rec == D_BM`.
  - no unbounded leads-to queries for bounded deadlines;
  - all finite classes use bounded `int[0,N]` domains;
  - query instance/location references exist;
  - dangling command/report channels are detected;
  - reachability queries are checked against generated location names.
- Priority helper functions in generated declarations:
  - `highest_priority_CH()`
  - `highest_priority_SQ()`
- MCP tools:
  - `phy_extract_contract`
  - `phy_validate_contract`
  - `phy_generate_uppaal_model`
  - `phy_generate_property_pack`
  - `phy_export_property_pack`
  - `phy_generate_report`
  - `phy_export_report`
  - `phy_export_run_artifacts`
  - `phy_verify_contract`
  - `phy_verify_property_pack`
  - `phy_check_no_continuous_guards`
  - `phy_check_channel_semantics`
  - `phy_check_alpha_profile`
  - `phy_explain_counterexample`
  - `phy_list_profiles`
  - `phy_get_profile`
  - `phy_list_scenarios`
  - `phy_get_scenario`
  - `phy_verify_scenario`
  - `phy_verify_all_scenarios`
  - `phy_list_benchmarks`
  - `phy_get_benchmark`
  - `phy_validate_benchmarks`
- CLI commands:
  - `phy-extract`
  - `phy-generate`
  - `phy-property-pack`
  - `phy-report`
  - `phy-run-artifacts`
  - `phy-verify`
  - `phy-list-scenarios`
  - `phy-scenario`
  - `phy-verify-scenario`
  - `phy-verify-all-scenarios`
  - `phy-list-benchmarks`
  - `phy-benchmark`
  - `phy-validate-benchmarks`
- Compact observer scenarios:
  - `obs_sense_report_success`
  - `obs_sense_report_violation`
  - `obs_freshness_success`
  - `obs_freshness_violation`
  - `obs_beam_recovery_success`
  - `obs_beam_recovery_violation`
- First-level verifyta output normalizer:
  - formula verification events;
  - formula status events;
  - stderr tail;
  - failed-query domain classification for observer/deadlock/contract failures.
- Text trace parser:
  - delay/time events;
  - UPPAAL instance/location events with PHY meaning;
  - transition sync extraction;
  - domain class assignments;
  - root-cause candidates for missing/late reports, deadlock, blocked handshakes, impossible guards, contract violations and severe PHY classes;
  - counterexample classification as `possible_physical_scenario`, `abstraction_artifact`, `modeling_error`, `environment_assumption_violation`, or `unknown`;
  - deadline details: trigger, expected response, deadline and actual path;
  - beam recovery outcome status: missing/late/observed;
  - freshness delta when `AoS_BS` and `AoS_CTRL` are visible;
  - `phy_explain_counterexample(...)` includes parsed trace details when `trace_text` is provided.
- Static benchmark suite:
  - 16 positive/static PHY scenarios: `nominal_phy`, `channel_outage`, `interference_limited`, `mobility_limited`, `multipath_limited`, `signal_reconfiguring`, `signal_limited`, `beam_recovery_success`, `beam_handover_hint`, `beam_failure_timeout`, `sensing_probability_limited`, `sensing_freshness_limited`, `sensing_failure`, `phy_communication_degraded`, `phy_sensing_degraded`, `phy_joint_degraded`;
  - 5 intentionally broken scenarios: report channel declared as `chan`, continuous guard, `c_rec > D_BM`, `PHYState` written outside `A_PH`, missing `A_ENV`;
  - `phy_validate_benchmarks()` validates that positive scenarios pass static validation and broken scenarios fail for the expected reason.
- Report/artifact generation:
  - `report.md`
  - `traceability_matrix.md`
  - `model_summary.md`
  - `assume_guarantee_report.md`
  - `alpha_profile_report.md`
  - `coverage_report.md`
  - `publication_tables.md`
  - `properties.csv`
  - optional `violations.md` when `result_json` is provided.
  - optional `trace_explanation.md` when `trace_text` is provided.
- Run artifact layout:
  - `artifacts/<run_id>/source.tex`
  - `contract.json`
  - `model.xml`
  - `queries.q`
  - optional `results.json`
  - optional `trace.txt`
  - `report.md`
  - `traceability_matrix.md`
  - `model_summary.md`
  - `run_metadata.json`
  - cache key from source/profile/generator/verifyta/query/options hashes;
  - `force` bypass for cache overwrite.
- Property pack generation:
  - query `.q` text;
  - `queries.json` metadata with property name, category, interpretation and source provenance;
  - category summary;
  - static-check metadata for channel semantics, single-sync and no-continuous-guards checks;
  - negative property pack for intentionally broken benchmark models.
- Tests:
  - system Python: `44 tests OK, 1 skipped` when `mcp` package is absent;
  - `.venv`: `44 tests OK`.
  - golden fixtures:
    - `tests/fixtures/phy_contract_article.golden.json`
    - `tests/fixtures/phy_model_article.golden.xml`
    - `tests/fixtures/phy_queries_article.golden.q`
- CLI smoke:
  - `phy-report --tex PHY_level_formalization_reviewed-2026-06-06-143000.tex --output-dir .uppaal_mcp_workspace/phy_report_smoke` writes 11 artifacts.
  - `phy-generate --tex PHY_level_formalization_reviewed-2026-06-06-143000.tex --output-dir .uppaal_mcp_workspace/phy_generated_smoke` returns clean semantic and alpha validation.
  - `phy-validate-benchmarks`: `ok=true`, `count=21`.
  - `phy-benchmark nominal_phy --output-dir .uppaal_mcp_workspace/phy_benchmark_nominal`: positive static validation ok.
  - `phy-benchmark broken_missing_a_env --output-dir .uppaal_mcp_workspace/phy_benchmark_broken_missing_env`: expected missing ENV errors.
  - `phy-property-pack --include-negative --output-dir .uppaal_mcp_workspace/phy_property_pack_smoke`: writes `queries.q`, `queries.json`, `property_pack.json`, `negative_property_pack.json`.
  - `phy-verify-property-pack --model .uppaal_mcp_workspace/phy_generated_smoke/model.xml --queries .uppaal_mcp_workspace/phy_generated_smoke/queries.q --static-only`: `status=validated`.
  - `phy-generate --mode minimal --output-dir .uppaal_mcp_workspace/phy_generated_minimal_smoke`: returns clean semantic validation without observers.
  - `phy-run-artifacts --output-root .uppaal_mcp_workspace/phy_run_artifacts_smoke --verifyta-version "UPPAAL 5.0.0"`: writes artifact layout and returns stable cache hit on repeat without `--force`.
  - `list-examples`: returns `category`/`is_phy`, so `phy_contract_skeleton` is visible as a PHY example.
- MCP UPPAAL validation:
  - `uppaal_validate_model` on `.uppaal_mcp_workspace/phy_generated_smoke/model.xml` and `queries.q`: `ok=true`, 12 templates, 17 queries.

## Verifyta status

`phy_verify_contract` now runs the non-observer property pack one formula at a time.

Current fresh check on 2026-06-07: `verifyta.exe` is found, but Windows execution from WSL fails before UPPAAL starts:

```text
UtilBindVsockAnyPort:309: socket failed 1
```

So the generated model/query validation is green, but current `verifyta` execution is blocked by WSL interop state, not by UPPAAL syntax.

Last known successful verifyta run before the current WSL interop failure verified these as satisfied:

- `A[] not deadlock`
- `E<> A_PH.PHYNormal`
- `E<> A_PH.PHYSensingDegraded`
- `E<> A_PH.PHYCommunicationDegraded`
- `E<> A_PH.PHYJointDegraded`
- `A[] (A_PH.PHYNormal imply (comm_ok && sensing_qos_ok))`
- `A[] (ch_enabled_count <= 1)`
- `A[] (sq_enabled_count <= 1)`
- `A[] (A_BM.BeamRecover imply c_rec <= D_BM)`
- contract properties for `A_CH`, `A_SIG`, `A_BM`, `A_SQ`, `A_PH`

Current status returned by `phy_verify_contract` in this WSL session: `error` with the interop message above.

Observer templates are still generated inside the full `A_SYS`, but broad safety verification of those observers inside the full model is not used directly. Instead, `phy_verify_contract` verifies compact scenario models for each observer. This avoids the UPPAAL 5.0 state-space blow-up seen with the full guarded broadcast observer model.

Verified observer scenarios:

- `obs_sense_report_success`: `satisfied`
- `obs_sense_report_violation`: `not_satisfied`
- `obs_freshness_success`: `satisfied`
- `obs_freshness_violation`: `not_satisfied`
- `obs_beam_recovery_success`: `satisfied`
- `obs_beam_recovery_violation`: `not_satisfied`

For negative scenarios, `not_satisfied` is the expected result because the scenario intentionally violates the observer deadline property.

## Still not done

- Full LaTeX-to-IR compiler that replaces the canonical article fixture as the source of generated transition semantics.
- Full transition semantics for every automaton from the article, not just a verification-friendly baseline.
- Full observer verification inside the full `A_SYS`, or a redesigned observer encoding that avoids UPPAAL 5.0 guarded-broadcast state-space blow-up.
- Official `.xtr`/UPPAAL trace option integration; current parser handles text traces passed through `trace_text`.
- Counterexample explanation from full generated traces, including exact transition path reconstruction.
- CSV/publication table export and richer report polishing.
- Official result cache around actual `verifyta` execution; current cache is artifact-layout cache keyed by generated inputs/options.
- Current WSL interop failure prevents fresh `verifyta.exe` execution from this WSL session.
- Full checklist closure in `PHY_SPECIFIC_LAYER_TASKS.md`.
