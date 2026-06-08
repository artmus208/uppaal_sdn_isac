# MAC-Specific Layer Progress

Дата: 2026-06-08.

Статус: MAC-specific MCP layer v1 implemented.

Цель: реализовать MAC-specific MCP слой для
`MAC_resource_scheduling_formalization.tex` по шаблону PHY-specific слоя и с
reusable extension point для будущих SDN/RIC и Application layers.

## Реализовано

- Reusable layer adapter:
  - `src/uppaal_mcp/layers.py`;
  - shape: `layer_id`, source, extractor/generator/validator/report/scenario hooks.
- MAC package:
  - `src/uppaal_mcp/mac/ir.py`;
  - `defaults.py`;
  - `extractor.py`;
  - `alpha.py`;
  - `generator.py`;
  - `validators.py`;
  - `layout.py`;
  - `property_pack.py`;
  - `reports.py`;
  - `trace.py`;
  - `scenarios.py`;
  - `benchmarks.py`;
  - `tools.py`.
- MAC source:
  - `MAC_resource_scheduling_formalization.tex`.
- Target composition:
  - `A_MAC = A_SCH || A_Q || A_BUF || A_RSRC || A_MAC_AGG`;
  - `A_SYS_MAC = A_MAC || A_ENV_MAC`.
- Generated UPPAAL templates:
  - `Template_A_SCH`;
  - `Template_A_Q`;
  - `Template_A_BUF`;
  - `Template_A_RSRC`;
  - `Template_A_MAC_AGG`;
  - `Template_A_ENV_MAC`.
- Generated UPPAAL instances:
  - `A_SCH`;
  - `A_Q`;
  - `A_BUF`;
  - `A_RSRC`;
  - `A_MAC_AGG`;
  - `A_ENV_MAC`.
- Generated observers:
  - `ObsPhyAck`;
  - `ObsQueueCritical`;
  - `ObsSensingCritical`;
  - `ObsBufferOverflow`;
  - `ObsMacReportFreshness`.
- MAC extractor:
  - section-aware article scan;
  - composition evidence;
  - declaration block detection;
  - policy table `P0..P7` detection;
  - line markers for `alpha_MAC`, `mu_PHY->MAC`, `A_MAC`, `A_ENV_MAC`, observers and properties;
  - diagnostics in `contract["extractor"]`.
- `alpha_MAC`:
  - finite class registry;
  - built-in profiles: `default`, `conservative_safety`, `stress`;
  - deadline/profile validation;
  - no-continuous-guard check for raw queue/delay/loss/utilization/HARQ tokens.
- MAC generator:
  - modes: `minimal`, `with_observers`, `with_debug_counters`, `with_negative_scenarios`;
  - layouts: `readable`, `compact`;
  - stable query names via `Template_*` + instance names;
  - maps: `model_map.md`, `template_map.md`, `channels_map.md`, `policy_map.md`.
- Static validators:
  - required templates/instances;
  - report broadcast semantics;
  - command handshake semantics;
  - one sync label per edge;
  - no continuous MAC guards;
  - single-writer policy for key variables;
  - no `silent_accept=true`;
  - PHY ack success/timeout path;
  - observer shape;
  - query instance/location references;
  - readable layout validation.
- Property pack:
  - `.q` text;
  - `queries.json` metadata;
  - static-check metadata;
  - negative property pack metadata.
- Reports/artifacts:
  - `report.md`;
  - `traceability_matrix.md`;
  - `model_summary.md`;
  - `alpha_profile_report.md`;
  - `coverage_report.md`;
  - `policy_report.md`;
  - `properties.csv`;
  - `model_map.md`;
  - `template_map.md`;
  - `channels_map.md`;
  - `policy_map.md`;
  - run artifact layout with cache key.
- Trace explanation:
  - missed/late PHY ack;
  - queue critical timeout;
  - buffer overflow;
  - resource exhaustion;
  - deadlock/blocked handshake classification.
- Benchmarks:
  - `nominal_mac`;
  - `queue_critical`;
  - `buffer_overflow`;
  - `resource_exhausted`;
  - `stale_phy_kpi`;
  - `sensing_conflict`;
  - `phy_ack_timeout`;
  - `broken_report_channel_declared_as_chan`;
  - `broken_continuous_guard`;
  - `broken_missing_a_env_mac`;
  - `broken_silent_accept`;
  - `broken_missing_ack_timeout`.
- Golden fixtures:
  - `tests/fixtures/mac_contract_article.golden.json`;
  - `tests/fixtures/mac_model_article.golden.xml`;
  - `tests/fixtures/mac_model_article.readable.golden.xml`;
  - `tests/fixtures/mac_queries_article.golden.q`.
- Tests:
  - `tests/test_mac_layer.py`.
- CLI commands:
  - `mac-extract`;
  - `mac-generate`;
  - `mac-export-diagram`;
  - `mac-property-pack`;
  - `mac-report`;
  - `mac-run-artifacts`;
  - `mac-verify`;
  - `mac-verify-property-pack`;
  - `mac-list-scenarios`;
  - `mac-scenario`;
  - `mac-verify-scenario`;
  - `mac-verify-all-scenarios`;
  - `mac-list-benchmarks`;
  - `mac-benchmark`;
  - `mac-validate-benchmarks`.
- MCP tools:
  - `mac_extract_contract`;
  - `mac_validate_contract`;
  - `mac_generate_uppaal_model`;
  - `mac_validate_layout`;
  - `mac_export_diagram`;
  - `mac_generate_property_pack`;
  - `mac_export_property_pack`;
  - `mac_generate_report`;
  - `mac_export_report`;
  - `mac_export_run_artifacts`;
  - `mac_verify_contract`;
  - `mac_verify_property_pack`;
  - `mac_check_alpha_profile`;
  - `mac_check_channel_semantics`;
  - `mac_explain_counterexample`;
  - `mac_list_scenarios`;
  - `mac_get_scenario`;
  - `mac_verify_scenario`;
  - `mac_verify_all_scenarios`;
  - `mac_list_benchmarks`;
  - `mac_get_benchmark`;
  - `mac_validate_benchmarks`.
- Docs:
  - `COMMAND_REFERENCE.md` now includes MAC flow, modes and benchmark names.

## Smoke Evidence

- `PYTHONPATH=src python3 -m uppaal_mcp.cli mac-extract --tex MAC_resource_scheduling_formalization.tex`
  - extractor `ok=true`.
- `PYTHONPATH=src python3 -m uppaal_mcp.cli mac-generate --tex MAC_resource_scheduling_formalization.tex --layout readable --output-dir .uppaal_mcp_workspace/mac_generated_smoke`
  - semantic validation `ok=true`;
  - alpha validation `ok=true`;
  - layout validation `ok=true`.
- `PYTHONPATH=src python3 -m uppaal_mcp.cli mac-generate --mode minimal --output-dir .uppaal_mcp_workspace/mac_generated_minimal_smoke`
  - semantic validation `ok=true`.
- `PYTHONPATH=src python3 -m uppaal_mcp.cli mac-property-pack --include-negative --output-dir .uppaal_mcp_workspace/mac_property_pack_smoke`
  - writes `queries.q`, `queries.json`, `property_pack.json`.
- `PYTHONPATH=src python3 -m uppaal_mcp.cli mac-verify-property-pack --model .uppaal_mcp_workspace/mac_generated_smoke/model.xml --queries .uppaal_mcp_workspace/mac_generated_smoke/queries.q --static-only`
  - status `validated`.
- `PYTHONPATH=src python3 -m uppaal_mcp.cli mac-report --tex MAC_resource_scheduling_formalization.tex --output-dir .uppaal_mcp_workspace/mac_report_smoke`
  - writes 17 report/model/map files.
- `PYTHONPATH=src python3 -m uppaal_mcp.cli mac-export-diagram --model .uppaal_mcp_workspace/mac_generated_smoke/model.xml --output-dir .uppaal_mcp_workspace/mac_diagram_smoke`
  - writes DOT/SVG/maps/layout validation.
- `PYTHONPATH=src python3 -m uppaal_mcp.cli mac-run-artifacts --tex MAC_resource_scheduling_formalization.tex --output-root .uppaal_mcp_workspace/mac_run_artifacts_smoke --verifyta-version "UPPAAL 5.0.0"`
  - writes artifact layout with metadata/cache key.
- `PYTHONPATH=src python3 -m uppaal_mcp.cli mac-validate-benchmarks`
  - `ok=true`, `count=12`.
- Generic MCP `uppaal_verify` on generated MAC model:
  - query `E<> A_SCH.SelectMode`;
  - status `satisfied`;
  - elapsed about 110 ms.
- Generic MCP `uppaal_verify` on generated MAC model:
  - query `A[] (resourceClass == RES_EXHAUSTED imply !silent_accept)`;
  - status `timeout` at 30 seconds after large state-space exploration.
  - This is state explosion, not XML syntax failure.

## Test Evidence

- `PYTHONPATH=src python3 -m compileall -q src tests`
  - OK.
- `PYTHONPATH=src python3 -m unittest tests.test_mac_layer`
  - `Ran 9 tests ... OK`.
- `PYTHONPATH=src python3 -m unittest discover -s tests`
  - `Ran 61 tests ... OK (skipped=1)`.
- `.venv/bin/python -c "from uppaal_mcp.server import build_mcp; print(type(build_mcp()).__name__)"`
  - `FastMCP`.

## Known Limits

- MAC v1 is article-specific, not a universal MAC compiler.
- Extractor is section-aware and evidence-producing, but canonical semantics still come from the MAC contract fixture/defaults.
- Full universal `A[]` verification on the closed generated MAC model can hit state explosion; current practical gate is static semantic validation, benchmark mutation split, and small reachability smoke via `verifyta`.
- SDN/RIC and Application layers are not implemented yet; only extension points and design pattern are prepared.

## Acceptance Checklist

- [x] `mac-extract --tex MAC_resource_scheduling_formalization.tex` returns validated contract JSON.
- [x] `mac-generate --layout readable --output-dir ...` writes model, queries, contract and maps.
- [x] `mac-property-pack --output-dir ...` writes query metadata.
- [x] `mac-verify-property-pack --static-only` passes.
- [x] `mac-validate-benchmarks` passes with expected positive/broken split.
- [x] MCP tools expose the same workflow as CLI.
- [x] Existing PHY functionality remains green.
