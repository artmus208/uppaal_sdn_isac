# PHY Layer Usage

Этот слой нужен не для произвольных UPPAAL-моделей, а для статьи
`PHY_level_formalization_reviewed-2026-06-06-143000.tex`.

## Когда использовать какие tools

Generic tools:

```text
uppaal_validate_model
uppaal_verify
uppaal_verify_batch
uppaal_explain_result
```

Используй их, когда у тебя уже есть готовый `model.xml` и `queries.q`, и не нужна PHY-семантика статьи.

PHY-specific tools:

```text
phy_extract_contract
phy_validate_contract
phy_generate_uppaal_model
phy_generate_property_pack
phy_export_property_pack
phy_generate_report
phy_export_report
phy_export_run_artifacts
phy_verify_contract
phy_verify_property_pack
phy_check_channel_semantics
phy_validate_layout
phy_export_diagram
phy_explain_counterexample
phy_list_scenarios
phy_verify_scenario
phy_verify_all_scenarios
phy_list_benchmarks
phy_get_benchmark
phy_validate_benchmarks
```

Используй их, когда источник требований — текущий LaTeX PHY formalization.

## CLI сценарий

```bash
cd /mnt/c/Users/musta/Desktop/pySources/mcp_uppaal
PYTHONPATH=src python3 -m uppaal_mcp.cli phy-extract \
  --tex PHY_level_formalization_reviewed-2026-06-06-143000.tex
```

Сгенерировать модель и queries:

```bash
PYTHONPATH=src python3 -m uppaal_mcp.cli phy-generate \
  --tex PHY_level_formalization_reviewed-2026-06-06-143000.tex \
  --mode with_observers \
  --layout readable \
  --output-dir .uppaal_mcp_workspace/phy_generated
```

`readable` — default. Он раскладывает locations по смысловым зонам, разводит guard/sync/assignment labels, добавляет bend-points для self-loops/back edges/violation paths и пишет карты:

```text
.uppaal_mcp_workspace/phy_generated/
  contract.json
  model.xml
  queries.q
  model_map.md
  template_map.md
  channels_map.md
  layout_validation.json
```

Открывай в UPPAAL GUI именно generated `model.xml`, а смысловую навигацию смотри в `model_map.md`.

Режимы генерации:

```text
minimal                  A_SYS без observers и debug-counter queries
with_observers           default: A_SYS + bounded observers
with_debug_counters      включает classifier determinism counters
with_negative_scenarios  помечает run как связанный с negative benchmark suite
with_extended_observers  добавляет extended observer templates
open_system              open A_SYS без ENV_* instances, queries guarded by ass_env()
```

Layout modes:

```text
readable  default, нормальная схема для GUI
compact   плотная старая раскладка для минимальных diff-ов
```

Сгенерировать Graphviz/SVG карту:

```bash
PYTHONPATH=src python3 -m uppaal_mcp.cli phy-export-diagram \
  --model .uppaal_mcp_workspace/phy_generated/model.xml \
  --output-dir .uppaal_mcp_workspace/phy_diagram
```

Сгенерировать property pack как `.q` и JSON metadata:

```bash
PYTHONPATH=src python3 -m uppaal_mcp.cli phy-property-pack \
  --tex PHY_level_formalization_reviewed-2026-06-06-143000.tex \
  --include-negative \
  --output-dir .uppaal_mcp_workspace/phy_property_pack
```

Сгенерировать отчеты и traceability artifacts:

```bash
PYTHONPATH=src python3 -m uppaal_mcp.cli phy-report \
  --tex PHY_level_formalization_reviewed-2026-06-06-143000.tex \
  --output-dir .uppaal_mcp_workspace/phy_report
```

Сгенерировать полный run artifact layout с cache key:

```bash
PYTHONPATH=src python3 -m uppaal_mcp.cli phy-run-artifacts \
  --tex PHY_level_formalization_reviewed-2026-06-06-143000.tex \
  --output-root .uppaal_mcp_workspace/phy_run_artifacts \
  --verifyta-version "UPPAAL 5.0.0"
```

Layout:

```text
artifacts/<run_id>/
  source.tex
  contract.json
  model.xml
  queries.q
  results.json        # если передан result_json
  trace.txt           # если передан trace_text
  trace_explanation.md # если передан trace_text
  report.md
  traceability_matrix.md
  model_summary.md
  model_map.md
  template_map.md
  channels_map.md
  run_metadata.json
```

Запустить проверку:

```bash
PYTHONPATH=src python3 -m uppaal_mcp.cli phy-verify \
  --tex PHY_level_formalization_reviewed-2026-06-06-143000.tex \
  --timeout-sec 12
```

`phy_verify_contract` возвращает `run_metadata` и `artifacts`; если `artifact_root` не задан, используется workspace `phy_runs`.

Проверить benchmark suite без запуска `verifyta`:

```bash
PYTHONPATH=src python3 -m uppaal_mcp.cli phy-validate-benchmarks
```

Проверить property pack статически без запуска `verifyta`:

```bash
PYTHONPATH=src python3 -m uppaal_mcp.cli phy-verify-property-pack \
  --model .uppaal_mcp_workspace/phy_generated/model.xml \
  --queries .uppaal_mcp_workspace/phy_generated/queries.q \
  --static-only
```

Сгенерировать один benchmark:

```bash
PYTHONPATH=src python3 -m uppaal_mcp.cli phy-benchmark nominal_phy \
  --output-dir .uppaal_mcp_workspace/phy_benchmark_nominal
```

## Codex / MCP сценарий

Типовой порядок вызовов:

```text
1. phy_extract_contract(tex_path="PHY_level_formalization_reviewed-2026-06-06-143000.tex")
2. phy_validate_contract(contract_json=<result.contract>)
3. phy_generate_uppaal_model(contract_json=<contract>, include_observers=true, layout="readable")
4. phy_generate_property_pack(contract_json=<contract>, include_observers=true)
5. phy_verify_contract(contract_json=<contract>, timeout_sec=12)
6. phy_verify_property_pack(model_xml=<model>, queries=<queries>, static_only=true)
7. phy_generate_report(contract_json=<contract>, result_json=<verify.result>)
8. phy_validate_benchmarks()
```

Для отдельной проверки раскладки:

```text
phy_validate_layout(model_xml=<generated.model_xml>)
phy_export_diagram(output_dir=".uppaal_mcp_workspace/phy_diagram", model_xml=<generated.model_xml>)
```

Для записи файлов вместо in-memory отчета:

```text
phy_export_report(
  output_dir=".uppaal_mcp_workspace/phy_report",
  tex_path="PHY_level_formalization_reviewed-2026-06-06-143000.tex"
)
```

Для объяснения нарушения с текстовой трассой:

```text
phy_explain_counterexample(
  result_json=<verify result>,
  trace_text=<verifyta text trace or normalized trace text>,
  contract_json=<contract>
)
```

Отчет по той же трассе можно сразу записать в артефакты:

```bash
PYTHONPATH=src python3 -m uppaal_mcp.cli phy-report \
  --tex PHY_level_formalization_reviewed-2026-06-06-143000.tex \
  --result-json .uppaal_mcp_workspace/results.json \
  --trace-text .uppaal_mcp_workspace/trace.txt \
  --output-dir .uppaal_mcp_workspace/phy_report_with_trace
```

## Prompt для Codex

```text
Возьми PHY_level_formalization_reviewed-2026-06-06-143000.tex,
извлеки PHY contract через phy_extract_contract, проверь IR,
сгенерируй closed A_SYS с observers, сгенерируй property pack,
запусти phy_verify_contract с timeout_sec=12,
экспортируй report/artifacts и объясни failed queries в терминах PHY/SDN/ISAC.
```

## Profiles

Встроенные profiles доступны через:

```text
phy_list_profiles()
phy_get_profile("default")
phy_get_profile("conservative_safety")
phy_get_profile("stress")
```

Смысл простой:

```text
default              базовые дедлайны D_*=5
conservative_safety  более жесткие дедлайны D_*=4
stress               стрессовый профиль D_*=2
```

Любой custom profile должен иметь:

```json
{
  "name": "custom",
  "source": "user",
  "boundary_policy": "worse_class",
  "parameter_synthesis": false,
  "deadlines": {
    "D_meas": 5,
    "D_sig": 5,
    "D_sense": 5,
    "D_report": 5,
    "D_BM": 5
  }
}
```

`boundary_policy="worse_class"` принципиален: пограничное значение между good/bad уходит в худший класс. Parameter synthesis в этом слое специально не делается.

## Что реально покрыто сейчас

Extractor сейчас section-aware:

```text
sections
verbatim blocks
composition formulas A_PHY/A_SYS/A_ENV
ordered X_disc
clock reset table
core location invariants
channel declarations
class sets from align blocks
PHY automata location/transition sketches
ENV behavior sketches
assume/guarantee table
property queries
article markers and source line evidence
```

Он уже не просто ищет пару маркеров, но и не является полноценным LaTeX-to-TA компилятором. Полная замена canonical fixture для генерации transition semantics остается отдельной задачей.

Report export пишет:

```text
contract.json
model.xml
queries.q
profile.json
report.md
traceability_matrix.md
model_summary.md
model_map.md
template_map.md
channels_map.md
assume_guarantee_report.md
alpha_profile_report.md
coverage_report.md
publication_tables.md
properties.csv
```

Если передан `result_json`, дополнительно пишутся:

```text
results.json
violations.md
```

Если передан `trace_text`, дополнительно пишутся:

```text
trace.txt
trace_explanation.md
```

## Ограничения

Базовая timed-automata модель не доказывает радиофизику, вероятности и оптимальность `Pi_PHY`. Она проверяет реакцию на конечные классы, дедлайны, синхронизацию, контрактные violation paths и observer properties.

## Troubleshooting

- UPPAAL path в WSL должен указывать на Windows exe: `/mnt/c/Program Files (x86)/UPPAAL-5.0.0/bin/verifyta.exe`.
- Если Codex MCP не видит `uppaal`, перезапусти окно VS Code после правки `~/.codex/config.toml`.
- Если `verifyta` пишет про invalid query, сначала прогони `uppaal_validate_model(model_path, query_path)`.
- Если full observer verification раздувает state space, используй `phy_verify_contract`: он проверяет non-observer pack на closed model, а observers через compact scenarios.
- Если нужна трасса, сначала получи текст trace от `verifyta`/diagnostic run, потом передай его в `phy_explain_counterexample` или `phy-report --trace-text`.
- Если Windows/WSL path не читается, проверь путь через `wslpath` или передавай WSL-путь `/mnt/c/...`.
