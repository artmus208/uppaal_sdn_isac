# MCP UPPAAL Command Reference

Этот файл фиксирует фактический интерфейс текущего репозитория: CLI-команды,
MCP tools для Codex/VS Code, режимы, встроенные имена и рабочие примеры.

## Базовые entrypoints

Из корня репозитория:

```bash
cd /mnt/c/Users/musta/Desktop/pySources/mcp_uppaal
```

Без установки пакета:

```bash
PYTHONPATH=src python3 -m uppaal_mcp.cli <command> [options]
```

После `pip install -e .`:

```bash
uppaal-verifyta <command> [options]
```

MCP-сервер для Codex/VS Code:

```bash
PYTHONPATH=src python3 -m uppaal_mcp
```

или после установки:

```bash
uppaal-mcp
```

## Переменные окружения

```bash
export UPPAAL_VERIFYTA_PATH="/mnt/c/Program Files (x86)/UPPAAL-5.0.0/bin/verifyta.exe"
export UPPAAL_MCP_WORKSPACE="/mnt/c/Users/musta/Desktop/pySources/mcp_uppaal/.uppaal_mcp_workspace"
export UPPAAL_TIMEOUT_SEC="60"
```

Windows-путь тоже поддерживается:

```text
C:\Program Files (x86)\UPPAAL-5.0.0\bin\verifyta.exe
```

## Глобальные CLI options

Глобальные options ставь до subcommand:

```bash
PYTHONPATH=src python3 -m uppaal_mcp.cli \
  --verifyta-path "/mnt/c/Program Files (x86)/UPPAAL-5.0.0/bin/verifyta.exe" \
  --workspace .uppaal_mcp_workspace \
  --timeout-sec 30 \
  version
```

Options:

```text
--verifyta-path PATH   путь к verifyta/verifyta.exe
--workspace DIR        директория для generated run artifacts
--timeout-sec SEC      default timeout для verifyta
```

## Generic CLI команды

### `version`

Печатает JSON с версией/banner `verifyta`.

```bash
PYTHONPATH=src python3 -m uppaal_mcp.cli version
```

### `list-examples`

Показывает встроенные examples.

```bash
PYTHONPATH=src python3 -m uppaal_mcp.cli list-examples
```

Встроенные examples:

```text
bounded_response
deadlock
deadlock_free
phy_contract_skeleton
queue_overflow
```

### `example NAME [--output-dir DIR]`

Печатает example как JSON или экспортирует `model.xml` и `queries.q`.

```bash
PYTHONPATH=src python3 -m uppaal_mcp.cli example deadlock_free

PYTHONPATH=src python3 -m uppaal_mcp.cli example deadlock_free \
  --output-dir .uppaal_mcp_workspace/example_deadlock_free
```

### `validate --model MODEL [--queries QUERIES]`

Статически валидирует UPPAAL XML и, если передан, query file.

```bash
PYTHONPATH=src python3 -m uppaal_mcp.cli validate \
  --model .uppaal_mcp_workspace/example_deadlock_free/model.xml \
  --queries .uppaal_mcp_workspace/example_deadlock_free/queries.q
```

### `verify --model MODEL [--queries QUERIES] [--options-preset PRESET] [-- VERIFYTA_OPTIONS...]`

Запускает `verifyta`.

Presets:

```text
normal              без дополнительных flags
trace_on_violation  добавляет -t0
diagnostic          добавляет -t0
```

Примеры:

```bash
PYTHONPATH=src python3 -m uppaal_mcp.cli verify \
  --model .uppaal_mcp_workspace/example_deadlock_free/model.xml \
  --queries .uppaal_mcp_workspace/example_deadlock_free/queries.q

PYTHONPATH=src python3 -m uppaal_mcp.cli verify \
  --model .uppaal_mcp_workspace/example_deadlock_free/model.xml \
  --queries .uppaal_mcp_workspace/example_deadlock_free/queries.q \
  --options-preset trace_on_violation

PYTHONPATH=src python3 -m uppaal_mcp.cli verify \
  --model model.xml \
  --queries queries.q \
  -- -u
```

## PHY CLI команды

В примерах ниже основной TeX:

```text
PHY_level_formalization_reviewed-2026-06-06-143000.tex
```

### `phy-extract [--tex TEX]`

Извлекает PHY contract IR из LaTeX. Без `--tex` используется дефолтный contract fixture.

```bash
PYTHONPATH=src python3 -m uppaal_mcp.cli phy-extract \
  --tex PHY_level_formalization_reviewed-2026-06-06-143000.tex
```

### `phy-generate [--tex TEX] [--output-dir DIR] [--mode MODE] [--layout readable|compact] [--no-observers] [--no-debug-counters] [--include-negative-scenarios]`

Генерирует `contract.json`, `model.xml`, `queries.q`, `model_map.md`, `template_map.md`, `channels_map.md`, `layout_validation.json`.

Layout modes:

```text
readable  default: semantic coordinates, separated labels and bend-points for UPPAAL GUI
compact   old dense one-line layout, useful only for tiny diffs
```

Modes:

```text
minimal                  A_SYS без observers и debug-counter queries
with_observers           default: closed A_SYS + bounded observers
with_debug_counters      включает classifier determinism counters
with_negative_scenarios  помечает модель как negative-suite related
with_extended_observers  добавляет ObsChannelReport/ObsSignalReport/ObsSensingReport/ObsPhyKpiReport
open_system              open A_SYS без ENV_* instances, queries wrapped через ass_env()
open                     alias для open_system
open-system              alias для open_system
```

Примеры:

```bash
PYTHONPATH=src python3 -m uppaal_mcp.cli phy-generate \
  --tex PHY_level_formalization_reviewed-2026-06-06-143000.tex \
  --layout readable \
  --output-dir .uppaal_mcp_workspace/phy_generated

PYTHONPATH=src python3 -m uppaal_mcp.cli phy-generate \
  --tex PHY_level_formalization_reviewed-2026-06-06-143000.tex \
  --mode minimal \
  --output-dir .uppaal_mcp_workspace/phy_generated_minimal

PYTHONPATH=src python3 -m uppaal_mcp.cli phy-generate \
  --tex PHY_level_formalization_reviewed-2026-06-06-143000.tex \
  --mode with_extended_observers \
  --output-dir .uppaal_mcp_workspace/phy_generated_extended

PYTHONPATH=src python3 -m uppaal_mcp.cli phy-generate \
  --tex PHY_level_formalization_reviewed-2026-06-06-143000.tex \
  --mode open_system \
  --output-dir .uppaal_mcp_workspace/phy_generated_open
```

### `phy-export-diagram [--model MODEL] [--tex TEX] [--layout readable|compact] [--output-dir DIR]`

Пишет человекочитаемые карты и дополнительную SVG/DOT-схему:

```text
model_map.md
template_map.md
channels_map.md
model.dot
model.svg
layout_validation.json
```

```bash
PYTHONPATH=src python3 -m uppaal_mcp.cli phy-export-diagram \
  --model .uppaal_mcp_workspace/phy_generated/model.xml \
  --output-dir .uppaal_mcp_workspace/phy_diagram
```

### `phy-property-pack [--tex TEX] [--output-dir DIR] [--no-observers] [--no-debug-counters] [--include-negative]`

Генерирует PHY property pack и metadata/provenance.

```bash
PYTHONPATH=src python3 -m uppaal_mcp.cli phy-property-pack \
  --tex PHY_level_formalization_reviewed-2026-06-06-143000.tex \
  --include-negative \
  --output-dir .uppaal_mcp_workspace/phy_property_pack
```

### `phy-report [--tex TEX] [--output-dir DIR] [--result-json FILE] [--trace-text FILE]`

Генерирует Markdown reports и traceability artifacts.

```bash
PYTHONPATH=src python3 -m uppaal_mcp.cli phy-report \
  --tex PHY_level_formalization_reviewed-2026-06-06-143000.tex \
  --output-dir .uppaal_mcp_workspace/phy_report

PYTHONPATH=src python3 -m uppaal_mcp.cli phy-report \
  --tex PHY_level_formalization_reviewed-2026-06-06-143000.tex \
  --result-json .uppaal_mcp_workspace/results.json \
  --trace-text .uppaal_mcp_workspace/trace.txt \
  --output-dir .uppaal_mcp_workspace/phy_report_with_trace
```

### `phy-run-artifacts --output-root DIR [--tex TEX] [--result-json FILE] [--trace-text FILE] [--verifyta-version TEXT] [--force]`

Пишет полный run layout с metadata/cache key.

```bash
PYTHONPATH=src python3 -m uppaal_mcp.cli phy-run-artifacts \
  --tex PHY_level_formalization_reviewed-2026-06-06-143000.tex \
  --output-root .uppaal_mcp_workspace/phy_run_artifacts \
  --verifyta-version "UPPAAL 5.0.0"

PYTHONPATH=src python3 -m uppaal_mcp.cli phy-run-artifacts \
  --tex PHY_level_formalization_reviewed-2026-06-06-143000.tex \
  --output-root .uppaal_mcp_workspace/phy_run_artifacts \
  --result-json .uppaal_mcp_workspace/results.json \
  --trace-text .uppaal_mcp_workspace/trace.txt \
  --force
```

### `phy-verify [--tex TEX] [--mode MODE] [--timeout-sec SEC]`

Генерирует PHY model и запускает verification.

Verify modes:

```text
closed           closed model, observers enabled
with_observers   alias для closed
observers        alias для closed
open_system      open-system model
open             alias для open_system
open-system      alias для open_system
minimal          minimal generator mode, observers disabled
base             no observers, default generator mode
no_observers     no observers, default generator mode
without_observers alias для no_observers
```

Важно: `phy-verify --mode with_extended_observers` сейчас не поддержан. Extended observers генерируются через `phy-generate --mode with_extended_observers`, а проверять их лучше через compact scenarios.

```bash
PYTHONPATH=src python3 -m uppaal_mcp.cli phy-verify \
  --tex PHY_level_formalization_reviewed-2026-06-06-143000.tex \
  --timeout-sec 12

PYTHONPATH=src python3 -m uppaal_mcp.cli phy-verify \
  --tex PHY_level_formalization_reviewed-2026-06-06-143000.tex \
  --mode minimal \
  --timeout-sec 30

PYTHONPATH=src python3 -m uppaal_mcp.cli phy-verify \
  --tex PHY_level_formalization_reviewed-2026-06-06-143000.tex \
  --mode open_system \
  --timeout-sec 30
```

### `phy-verify-property-pack --model MODEL --queries QUERIES [--timeout-sec SEC] [--no-explain] [--static-only]`

Проверяет property pack против модели.

```bash
PYTHONPATH=src python3 -m uppaal_mcp.cli phy-verify-property-pack \
  --model .uppaal_mcp_workspace/phy_generated/model.xml \
  --queries .uppaal_mcp_workspace/phy_generated/queries.q \
  --static-only

PYTHONPATH=src python3 -m uppaal_mcp.cli phy-verify-property-pack \
  --model .uppaal_mcp_workspace/phy_generated/model.xml \
  --queries .uppaal_mcp_workspace/phy_generated/queries.q \
  --timeout-sec 30
```

### `phy-list-scenarios`

Список compact observer scenarios.

```bash
PYTHONPATH=src python3 -m uppaal_mcp.cli phy-list-scenarios
```

Scenario names:

```text
obs_sense_report_success
obs_sense_report_violation
obs_freshness_success
obs_freshness_violation
obs_beam_recovery_success
obs_beam_recovery_violation
```

### `phy-scenario NAME [--output-dir DIR]`

Генерирует один compact scenario.

```bash
PYTHONPATH=src python3 -m uppaal_mcp.cli phy-scenario obs_beam_recovery_violation \
  --output-dir .uppaal_mcp_workspace/scenario_obs_beam_recovery_violation
```

### `phy-verify-scenario NAME [--timeout-sec SEC]`

Проверяет один compact scenario через `verifyta`.

```bash
PYTHONPATH=src python3 -m uppaal_mcp.cli phy-verify-scenario obs_beam_recovery_success \
  --timeout-sec 10
```

### `phy-verify-all-scenarios [--timeout-sec SEC]`

Проверяет все compact scenarios.

```bash
PYTHONPATH=src python3 -m uppaal_mcp.cli phy-verify-all-scenarios \
  --timeout-sec 10
```

### `phy-list-benchmarks`

Список PHY benchmark scenarios.

```bash
PYTHONPATH=src python3 -m uppaal_mcp.cli phy-list-benchmarks
```

Benchmark names:

```text
nominal_phy
channel_outage
interference_limited
mobility_limited
multipath_limited
signal_reconfiguring
signal_limited
beam_recovery_success
beam_handover_hint
beam_failure_timeout
sensing_probability_limited
sensing_freshness_limited
sensing_failure
phy_communication_degraded
phy_sensing_degraded
phy_joint_degraded
broken_report_channel_declared_as_chan
broken_continuous_guard
broken_c_rec_gt_d_bm
broken_phy_state_outside_a_ph
broken_missing_a_env
```

### `phy-benchmark NAME [--output-dir DIR]`

Генерирует один benchmark model.

```bash
PYTHONPATH=src python3 -m uppaal_mcp.cli phy-benchmark nominal_phy \
  --output-dir .uppaal_mcp_workspace/benchmark_nominal_phy
```

### `phy-validate-benchmarks`

Статически валидирует все benchmark scenarios.

```bash
PYTHONPATH=src python3 -m uppaal_mcp.cli phy-validate-benchmarks
```

## MCP config для Codex/VS Code

В `~/.codex/config.toml`:

```toml
[mcp_servers.uppaal]
command = "python3"
args = ["-m", "uppaal_mcp"]
env = {
  PYTHONPATH = "/mnt/c/Users/musta/Desktop/pySources/mcp_uppaal/src",
  UPPAAL_VERIFYTA_PATH = "/mnt/c/Program Files (x86)/UPPAAL-5.0.0/bin/verifyta.exe",
  UPPAAL_MCP_WORKSPACE = "/mnt/c/Users/musta/Desktop/pySources/mcp_uppaal/.uppaal_mcp_workspace",
  UPPAAL_TIMEOUT_SEC = "60"
}
```

После правки config перезапусти окно VS Code/Codex.

## MCP tools: generic UPPAAL

В Codex это не shell-команды. Это tools, которые вызываются по имени.

### `uppaal_version()`

```text
uppaal_version()
```

### `uppaal_validate_model(model_xml?, model_path?, queries?, query_path?)`

```text
uppaal_validate_model(
  model_path=".uppaal_mcp_workspace/example_deadlock_free/model.xml",
  query_path=".uppaal_mcp_workspace/example_deadlock_free/queries.q"
)
```

### `uppaal_verify(model_xml?, model_path?, queries?, query_path?, options?, options_preset?, timeout_sec?, keep_artifacts?)`

```text
uppaal_verify(
  model_path=".uppaal_mcp_workspace/example_deadlock_free/model.xml",
  query_path=".uppaal_mcp_workspace/example_deadlock_free/queries.q",
  timeout_sec=30
)

uppaal_verify(
  model_path=".uppaal_mcp_workspace/scenario_obs_beam_recovery_violation/model.xml",
  query_path=".uppaal_mcp_workspace/scenario_obs_beam_recovery_violation/queries.q",
  options_preset="trace_on_violation",
  timeout_sec=30
)
```

### `uppaal_verify_batch(items, options_preset?, timeout_sec?)`

```text
uppaal_verify_batch(
  items=[
    {"model_path": "m1.xml", "query_path": "q1.q"},
    {"model_path": "m2.xml", "query_path": "q2.q"}
  ],
  timeout_sec=30
)
```

### `uppaal_list_examples()`

```text
uppaal_list_examples()
```

### `uppaal_get_example(name)`

```text
uppaal_get_example(name="deadlock_free")
```

### `uppaal_explain_result(result)`

```text
uppaal_explain_result(result=<uppaal_verify result>)
```

## MCP tools: PHY-specific

### `phy_extract_contract(tex_text?, tex_path?)`

```text
phy_extract_contract(
  tex_path="PHY_level_formalization_reviewed-2026-06-06-143000.tex"
)
```

### `phy_validate_contract(contract_json?)`

```text
phy_validate_contract(contract_json=<contract>)
```

### `phy_generate_uppaal_model(contract_json?, tex_text?, tex_path?, profile?, include_observers?, debug_counters?, include_negative_scenarios?, mode?, layout?)`

```text
phy_generate_uppaal_model(
  tex_path="PHY_level_formalization_reviewed-2026-06-06-143000.tex",
  mode="with_observers",
  layout="readable",
  include_observers=true,
  debug_counters=true
)

phy_generate_uppaal_model(
  tex_path="PHY_level_formalization_reviewed-2026-06-06-143000.tex",
  mode="with_extended_observers"
)

phy_generate_uppaal_model(
  tex_path="PHY_level_formalization_reviewed-2026-06-06-143000.tex",
  mode="open_system"
)
```

### `phy_validate_layout(model_xml?, contract_json?)`

```text
phy_validate_layout(model_xml=<generated model_xml>)
```

Проверяет, что layout не схлопнулся: разные координаты locations/labels, violation справа, nominal слева, self-loops с nails, нет одной общей Y-линии.

### `phy_export_diagram(output_dir, model_xml?, contract_json?, tex_text?, tex_path?, profile?, layout?)`

```text
phy_export_diagram(
  output_dir=".uppaal_mcp_workspace/phy_diagram",
  model_xml=<generated model_xml>,
  layout="readable"
)
```

### `phy_generate_property_pack(contract_json?, model_xml?, profile?, include_observers?, debug_counters?, include_negative?)`

```text
phy_generate_property_pack(
  contract_json=<contract>,
  model_xml=<model_xml>,
  include_negative=true
)
```

### `phy_export_property_pack(output_dir, contract_json?, tex_text?, tex_path?, model_xml?, profile?, include_observers?, debug_counters?, include_negative?)`

```text
phy_export_property_pack(
  output_dir=".uppaal_mcp_workspace/phy_property_pack",
  tex_path="PHY_level_formalization_reviewed-2026-06-06-143000.tex",
  include_negative=true
)
```

### `phy_generate_report(contract_json?, tex_text?, tex_path?, model_xml?, queries?, result_json?, trace_text?, profile?)`

```text
phy_generate_report(
  tex_path="PHY_level_formalization_reviewed-2026-06-06-143000.tex",
  result_json=<verify_result>,
  trace_text=<trace_text>
)
```

### `phy_export_report(output_dir, contract_json?, tex_text?, tex_path?, model_xml?, queries?, result_json?, trace_text?, profile?)`

```text
phy_export_report(
  output_dir=".uppaal_mcp_workspace/phy_report",
  tex_path="PHY_level_formalization_reviewed-2026-06-06-143000.tex",
  result_json=<verify_result>
)
```

### `phy_export_run_artifacts(output_root, contract_json?, tex_text?, tex_path?, model_xml?, queries?, result_json?, trace_text?, profile?, verifyta_version?, verifyta_command?, options?, force?)`

```text
phy_export_run_artifacts(
  output_root=".uppaal_mcp_workspace/phy_run_artifacts",
  tex_path="PHY_level_formalization_reviewed-2026-06-06-143000.tex",
  result_json=<verify_result>,
  trace_text=<trace_text>,
  force=true
)
```

### `phy_verify_contract(tex_text?, tex_path?, contract_json?, profile?, mode?, include_observers?, timeout_sec?, artifact_root?, force?)`

```text
phy_verify_contract(
  tex_path="PHY_level_formalization_reviewed-2026-06-06-143000.tex",
  mode="minimal",
  timeout_sec=30
)

phy_verify_contract(
  tex_path="PHY_level_formalization_reviewed-2026-06-06-143000.tex",
  mode="open_system",
  timeout_sec=30,
  artifact_root=".uppaal_mcp_workspace/phy_runs",
  force=true
)
```

### `phy_verify_property_pack(model_xml?, model_path?, queries?, query_path?, explain?, timeout_sec?, static_only?)`

```text
phy_verify_property_pack(
  model_path=".uppaal_mcp_workspace/phy_generated/model.xml",
  query_path=".uppaal_mcp_workspace/phy_generated/queries.q",
  static_only=true
)
```

### `phy_check_no_continuous_guards(model_xml?, contract_json?)`

```text
phy_check_no_continuous_guards(model_xml=<model_xml>)
```

### `phy_check_channel_semantics(model_xml?, contract_json?)`

```text
phy_check_channel_semantics(model_xml=<model_xml>)
```

### `phy_check_alpha_profile(profile_json?)`

```text
phy_check_alpha_profile(profile_json={
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
})
```

### `phy_explain_counterexample(result_json, trace_text?, contract_json?)`

```text
phy_explain_counterexample(
  result_json=<verify_result>,
  trace_text=<verifyta_trace_text>,
  contract_json=<contract>
)
```

### `phy_list_profiles()`

```text
phy_list_profiles()
```

Built-in profiles:

```text
default              D_*=5
conservative_safety  D_*=4
stress               D_*=2
```

### `phy_get_profile(name)`

```text
phy_get_profile(name="stress")
```

### `phy_list_scenarios()`

```text
phy_list_scenarios()
```

### `phy_get_scenario(name, profile?)`

```text
phy_get_scenario(name="obs_beam_recovery_violation")
```

### `phy_verify_scenario(name, profile?, timeout_sec?)`

```text
phy_verify_scenario(
  name="obs_beam_recovery_success",
  timeout_sec=10
)
```

### `phy_verify_all_scenarios(profile?, timeout_sec?)`

```text
phy_verify_all_scenarios(timeout_sec=10)
```

### `phy_list_benchmarks()`

```text
phy_list_benchmarks()
```

### `phy_get_benchmark(name, profile?)`

```text
phy_get_benchmark(name="nominal_phy")
```

### `phy_validate_benchmarks(profile?)`

```text
phy_validate_benchmarks()
```

## Типовые рабочие сценарии

### Проверить built-in `deadlock_free`

```bash
PYTHONPATH=src python3 -m uppaal_mcp.cli example deadlock_free \
  --output-dir .uppaal_mcp_workspace/example_deadlock_free

PYTHONPATH=src python3 -m uppaal_mcp.cli verify \
  --model .uppaal_mcp_workspace/example_deadlock_free/model.xml \
  --queries .uppaal_mcp_workspace/example_deadlock_free/queries.q \
  --options-preset normal
```

Через MCP:

```text
example = uppaal_get_example(name="deadlock_free")
uppaal_verify(model_xml=example.model_xml, queries=example.queries, timeout_sec=30)
```

### Полный PHY flow из TeX

```bash
PYTHONPATH=src python -m uppaal_mcp.cli phy-extract \
  --tex PHY_level_formalization_reviewed-2026-06-06-143000.tex

PYTHONPATH=src python -m uppaal_mcp.cli phy-generate \
  --tex PHY_level_formalization_reviewed-2026-06-06-143000.tex \
  --mode with_observers \
  --layout readable \
  --output-dir .uppaal_mcp_workspace/phy_generated

PYTHONPATH=src python -m uppaal_mcp.cli phy-verify-property-pack \
  --model .uppaal_mcp_workspace/phy_generated/model.xml \
  --queries .uppaal_mcp_workspace/phy_generated/queries.q \
  --static-only

PYTHONPATH=src python -m uppaal_mcp.cli phy-verify \
  --tex PHY_level_formalization_reviewed-2026-06-06-143000.tex \
  --mode minimal \
  --timeout-sec 30

PYTHONPATH=src python -m uppaal_mcp.cli phy-report \
  --tex PHY_level_formalization_reviewed-2026-06-06-143000.tex \
  --output-dir .uppaal_mcp_workspace/phy_report
```

Через MCP:

```text
contract = phy_extract_contract(tex_path="PHY_level_formalization_reviewed-2026-06-06-143000.tex")
phy_validate_contract(contract_json=contract)
generated = phy_generate_uppaal_model(contract_json=contract, mode="with_observers", layout="readable")
phy_verify_contract(contract_json=contract, mode="minimal", timeout_sec=30)
phy_verify_all_scenarios(timeout_sec=10)
phy_export_report(
  output_dir=".uppaal_mcp_workspace/phy_report",
  contract_json=contract
)
```

### Получить trace на violation scenario

```bash
PYTHONPATH=src python3 -m uppaal_mcp.cli phy-scenario obs_beam_recovery_violation \
  --output-dir .uppaal_mcp_workspace/scenario_obs_beam_recovery_violation

PYTHONPATH=src python3 -m uppaal_mcp.cli verify \
  --model .uppaal_mcp_workspace/scenario_obs_beam_recovery_violation/model.xml \
  --queries .uppaal_mcp_workspace/scenario_obs_beam_recovery_violation/queries.q \
  --options-preset trace_on_violation
```

Через MCP:

```text
scenario = phy_get_scenario(name="obs_beam_recovery_violation")
result = uppaal_verify(
  model_xml=scenario.model_xml,
  queries=scenario.queries,
  options_preset="trace_on_violation",
  timeout_sec=30
)
phy_explain_counterexample(result_json=result, trace_text=result.stdout)
```
