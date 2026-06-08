# MCP UPPAAL

Текущий репозиторий уже содержит MVP MCP-сервера для UPPAAL:

```text
src/uppaal_mcp/
  config.py       env/config + дефолтный UPPAAL 5.0.0 path
  paths.py        WSL <-> Windows path conversion
  validation.py   статическая XML/Q проверка
  verifyta.py     verifyta runner + JSON result parser
  server.py       MCP tools через FastMCP
  cli.py          локальная проверка без MCP-клиента
  builtin_examples/
```

Реализованные MCP tools:

```text
uppaal_version()
uppaal_validate_model(model_xml?, model_path?, queries?, query_path?)
uppaal_verify(model_xml?, model_path?, queries?, query_path?, options?, timeout_sec?)
uppaal_verify_batch(items)
uppaal_list_examples()
uppaal_get_example(name)
uppaal_explain_result(result)
```

Сервер принимает и текст модели/query, и пути к файлам. Для твоей установки UPPAAL ожидаемый путь:

```text
/mnt/c/Program Files (x86)/UPPAAL-5.0.0/bin/verifyta.exe
```

или Windows-вариант:

```text
C:\Program Files (x86)\UPPAAL-5.0.0\bin\verifyta.exe
```

Оба варианта поддерживаются.

## Быстрый запуск из WSL

```bash
cd /mnt/c/Users/musta/Desktop/pySources/mcp_uppaal
python3 -m venv .venv
. .venv/bin/activate
pip install -e .
uppaal-verifyta version
uppaal-verifyta list-examples
```

Если не ставить пакет, ядро можно гонять так:

```bash
cd /mnt/c/Users/musta/Desktop/pySources/mcp_uppaal
PYTHONPATH=src python3 -m uppaal_mcp.cli version
PYTHONPATH=src python3 -m uppaal_mcp.cli list-examples
```

## Подключение к Codex через VS Code

Рабочая команда MCP-сервера:

```bash
cd /mnt/c/Users/musta/Desktop/pySources/mcp_uppaal
PYTHONPATH=src python3 -m uppaal_mcp
```

Типовой MCP config:

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

Если ставишь через `.venv`, лучше так:

```toml
[mcp_servers.uppaal]
command = "/mnt/c/Users/musta/Desktop/pySources/mcp_uppaal/.venv/bin/python"
args = ["-m", "uppaal_mcp"]
env = {
  UPPAAL_VERIFYTA_PATH = "/mnt/c/Program Files (x86)/UPPAAL-5.0.0/bin/verifyta.exe",
  UPPAAL_MCP_WORKSPACE = "/mnt/c/Users/musta/Desktop/pySources/mcp_uppaal/.uppaal_mcp_workspace",
  UPPAAL_TIMEOUT_SEC = "60"
}
```

## Проверка

Локально проверено:

```text
PYTHONPATH=src python3 -m unittest discover -s tests
Ran 53 tests: OK (skipped=1)

.venv/bin/python -m unittest discover -s tests
Не перегонялось в этом срезе.

.venv/bin/python -c "from uppaal_mcp.server import build_mcp; print(type(build_mcp()).__name__)"
FastMCP

.venv/bin/uppaal-verifyta version
В текущем WSL-сеансе Windows interop падает:
UtilBindVsockAnyPort: socket failed 1
```

То есть путь к `verifyta.exe` найден, но запуск Windows exe из WSL сейчас сломан на уровне окружения. Static validation, генерация XML/Q и MCP tool registration проходят.

Встроенные модели:

```text
bounded_response       satisfied
deadlock               not_satisfied
deadlock_free          satisfied
phy_contract_skeleton  satisfied
queue_overflow         satisfied
```

`uppaal_list_examples()` и `uppaal-verifyta list-examples` теперь возвращают `category` и `is_phy`, так что PHY examples не смешаны вслепую с generic examples.

Это пока именно MVP. Второй этап — PHY-specific слой из статьи: extractor из LaTeX, генерация `A_CH/A_SIG/A_BM/A_SQ/A_PH` плюс `A_ENV`/ENV-stubs для закрытой проверки, проверки `alpha_PHY`, report-channel semantics, observers и trace explanation.

Текущий прогресс по второму этапу вынесен отдельно:

```text
PHY_SPECIFIC_LAYER_TASKS.md     полный backlog
PHY_SPECIFIC_LAYER_PROGRESS.md  что уже реализовано и что еще не закрыто
```

Новые PHY-specific MCP tools уже подключены:

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
phy_check_no_continuous_guards
phy_check_channel_semantics
phy_check_alpha_profile
phy_validate_layout
phy_export_diagram
phy_explain_counterexample
phy_list_profiles
phy_get_profile
phy_list_scenarios
phy_get_scenario
phy_verify_scenario
phy_verify_all_scenarios
phy_list_benchmarks
phy_get_benchmark
phy_validate_benchmarks
```

CLI:

```bash
PYTHONPATH=src python3 -m uppaal_mcp.cli phy-extract --tex PHY_level_formalization_reviewed-2026-06-06-143000.tex
PYTHONPATH=src python3 -m uppaal_mcp.cli phy-generate --tex PHY_level_formalization_reviewed-2026-06-06-143000.tex --layout readable --output-dir .uppaal_mcp_workspace/phy_generated_smoke
PYTHONPATH=src python3 -m uppaal_mcp.cli phy-export-diagram --model .uppaal_mcp_workspace/phy_generated_smoke/model.xml --output-dir .uppaal_mcp_workspace/phy_diagram_smoke
PYTHONPATH=src python3 -m uppaal_mcp.cli phy-property-pack --tex PHY_level_formalization_reviewed-2026-06-06-143000.tex --include-negative --output-dir .uppaal_mcp_workspace/phy_property_pack_smoke
PYTHONPATH=src python3 -m uppaal_mcp.cli phy-report --tex PHY_level_formalization_reviewed-2026-06-06-143000.tex --output-dir .uppaal_mcp_workspace/phy_report_smoke
PYTHONPATH=src python3 -m uppaal_mcp.cli phy-run-artifacts --tex PHY_level_formalization_reviewed-2026-06-06-143000.tex --output-root .uppaal_mcp_workspace/phy_run_artifacts_smoke --verifyta-version "UPPAAL 5.0.0"
PYTHONPATH=src python3 -m uppaal_mcp.cli phy-verify --tex PHY_level_formalization_reviewed-2026-06-06-143000.tex --timeout-sec 12
PYTHONPATH=src python3 -m uppaal_mcp.cli phy-verify-property-pack --model .uppaal_mcp_workspace/phy_generated_smoke/model.xml --queries .uppaal_mcp_workspace/phy_generated_smoke/queries.q --static-only
PYTHONPATH=src python3 -m uppaal_mcp.cli phy-list-scenarios
PYTHONPATH=src python3 -m uppaal_mcp.cli phy-verify-all-scenarios --timeout-sec 10
PYTHONPATH=src python3 -m uppaal_mcp.cli phy-list-benchmarks
PYTHONPATH=src python3 -m uppaal_mcp.cli phy-validate-benchmarks
PYTHONPATH=src python3 -m uppaal_mcp.cli phy-benchmark nominal_phy --output-dir .uppaal_mcp_workspace/phy_benchmark_nominal
```

`phy-generate --output-dir` пишет не только `model.xml`, `queries.q`, `contract.json`, но и человекочитаемые карты:

```text
model_map.md
template_map.md
channels_map.md
layout_validation.json
```

Подробный рабочий сценарий PHY-specific слоя:

```text
docs/phy_layer_usage.md
```

---

Если под **MCP** ты имеешь в виду **Model Context Protocol**, то готового нормального публичного **MCP-сервера для UPPAAL** я не нашёл. Я бы исходил из того, что его **нет** или он не является заметным/поддерживаемым проектом.

Но сделать его **можно, и это довольно реалистично**. UPPAAL для этого хорошо подходит, потому что у него есть командный verifier `verifyta`: официальная документация прямо пишет, что verifier доступен через CLI-утилиту `verifyta` в `bin`-директории дистрибутива UPPAAL. ([docs.uppaal.org][1]) MCP как раз задуман как стандарт, через который AI-клиент вызывает внешние инструменты/источники данных через MCP-сервер. ([Anthropic][2])

Я бы делал так:

```text
LLM / Cursor / Claude / ChatGPT client
        ↓ MCP
uppaal-mcp-server
        ↓
verifyta / PyUPPAAL / XML parser
        ↓
model.xml + queries.q + traces
```

Минимальный набор MCP tools:

```text
uppaal_validate_model(model_xml) 
→ проверить XML/синтаксис/структуру

uppaal_verify(model_xml, queries)
→ запустить verifyta и вернуть satisfied / not satisfied / errors

uppaal_verify_with_trace(model_xml, query)
→ если свойство нарушено, вернуть контрпример/trace

uppaal_summarize_model(model_xml)
→ вытащить templates, clocks, channels, locations, edges, guards, invariants

uppaal_explain_result(output)
→ разобрать вывод verifyta человеческим языком

uppaal_check_property_pack(model_xml, property_pack)
→ прогнать пачку типовых свойств: deadlock, reachability, safety, liveness
```

Для MVP лучше писать на **Python + FastMCP** и просто оборачивать `verifyta` через `subprocess`. Есть ещё **PyUPPAAL**: он умеет загружать/редактировать UPPAAL-модель, запускать verification через `verifyta`, получать terminal output и парсить trace в `SimTrace`. ([GitHub][3]) Это прям почти готовая прослойка для MCP.

Важный момент: **не надо встраивать `verifyta` в свой репозиторий**. Лучше MCP-сервер принимает путь к локально установленному UPPAAL/`verifyta`. У UPPAAL лицензия не полностью свободная: он бесплатен только для академического использования, а коммерческое/частное/неакадемическое использование требует лицензии. ([it.uu.se][4])

Примерный каркас tool-а:

```python
import subprocess
import tempfile
from pathlib import Path
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("uppaal-mcp")

VERIFYTA_PATH = "C:\\Program Files (x86)\\UPPAAL-5.0.0\\bin\\verifyta.exe"

@mcp.tool()
def uppaal_verify(model_xml: str, queries: str) -> dict:
    """
    Run UPPAAL verifyta on a model.xml and queries.q.
    """
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        model_path = tmp_path / "model.xml"
        query_path = tmp_path / "queries.q"

        model_path.write_text(model_xml, encoding="utf-8")
        query_path.write_text(queries, encoding="utf-8")

        result = subprocess.run(
            [VERIFYTA_PATH, str(model_path), str(query_path)],
            capture_output=True,
            text=True,
            timeout=60,
        )

        return {
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "satisfied": "Formula is satisfied" in result.stdout,
            "not_satisfied": "Formula is NOT satisfied" in result.stdout,
        }

if __name__ == "__main__":
    mcp.run()
```

Моё мнение: **делать стоит**, особенно для твоей задачи с формализацией PHY/SDN. Это даст нормальный workflow:

```text
1. LLM читает твою формализацию.
2. Генерирует/правит UPPAAL XML.
3. Формирует queries.q.
4. Запускает verifyta.
5. Получает результат.
6. Если свойство падает — объясняет, где модель дырявая.
```


Итого: готового MCP для UPPAAL я не нашёл; сделать можно; MVP — 1–2 вечера, нормальная версия с trace parsing, property packs и XML-анализом — уже отдельный небольшой open-source проект.

[1]: https://docs.uppaal.org/toolsandapi/verifyta/ "verifyta :: UPPAAL Documentation"
[2]: https://www.anthropic.com/news/model-context-protocol "Introducing the Model Context Protocol \ Anthropic"
[3]: https://github.com/Jack0Chan/PyUPPAAL "GitHub - Jack0Chan/PyUPPAAL: PyUPPAAL is a python package basically for reflecting UPPAAL's model editing, verification, and counter-example parsing operations into scripts. · GitHub"
[4]: https://www.it.uu.se/research/group/darts/uppaal/download.shtml "Download | UPPAAL"



# Задачи  
Да, задач сильно больше, чем просто “обернуть `verifyta` в MCP”. Сам wrapper — это самая лёгкая часть. Нормальный MCP-сервер для UPPAAL надо делать как маленькую инженерную платформу вокруг формальной верификации.

Я бы разбил задачи так.

## 1. Контракт MCP-tools

Нужно решить, какие действия сервер вообще предоставляет модели:

```text
uppaal.validate_model
uppaal.verify
uppaal.verify_batch
uppaal.get_model_summary
uppaal.get_templates
uppaal.get_clocks
uppaal.get_channels
uppaal.get_queries
uppaal.explain_error
uppaal.explain_counterexample
uppaal.generate_property_pack
uppaal.check_deadlocks
uppaal.check_reachability
uppaal.check_timing_bounds
```

То есть не просто “запусти UPPAAL”, а дать LLM нормальные атомарные операции.

## 2. Workspace и файловая модель

Нужно сделать изоляцию рабочих директорий:

```text
workspace/
  models/
    model.xml
  queries/
    queries.q
  traces/
  reports/
  cache/
```

Задачи:

* принимать модель как текст, путь к файлу или прикреплённый файл;
* сохранять временные `.xml` и `.q`;
* чистить мусор;
* версионировать запуски;
* не давать MCP-серверу читать весь диск;
* делать reproducible run: модель + queries + версия UPPAAL + параметры запуска.

## 3. Адаптер к UPPAAL / `verifyta`

Нужно реализовать нормальный runner:

```text
verifyta_adapter.py
```

Он должен:

* находить `verifyta`;
* проверять версию UPPAAL;
* запускать с timeout;
* ограничивать память;
* ловить `stdout`, `stderr`, `returncode`;
* различать ошибки модели, ошибки query, timeout, crash;
* уметь batch-запуски;
* возвращать структурированный JSON, а не сырой лог.

Пример результата:

```json
{
  "status": "not_satisfied",
  "query": "A[] not deadlock",
  "time_ms": 1842,
  "stdout": "...",
  "stderr": "",
  "trace_available": true
}
```

## 4. Парсер UPPAAL XML

Без парсера MCP-сервер будет тупым терминалом. Нужен разбор модели:

* templates;
* locations;
* initial locations;
* transitions;
* guards;
* invariants;
* resets;
* synchronizations;
* clocks;
* bounded integers;
* channels;
* committed/urgent locations.

Это особенно важно, потому что UPPAAL-модели — это не просто timed automata, а расширенный язык с bounded integer variables, urgency и subset of CTL query language. Это прямо отмечается в работе по моделированию DoS-атак через UPPAAL. 

## 5. Static sanity checks

До запуска `verifyta` MCP должен сам находить тупые ошибки:

```text
- нет initial location
- clock объявлен, но нигде не используется
- channel объявлен, но нет pair !/?
- location недостижим
- transition никогда не сработает
- invariant противоречит guard
- reset clock отсутствует, хотя clock используется как таймер цикла
- dead branch
- query ссылается на несуществующую location
```

Для твоей SDN-ISAC модели это особенно важно: у тебя в тексте прямо есть требование, что каждое состояние должно быть достижимо хотя бы по одной трассе, иначе это мёртвая логическая ветвь. 

## 6. Генерация property packs

Это уже самое полезное для статьи. MCP должен уметь генерировать типовые наборы свойств:

```text
Deadlock freedom:
A[] not deadlock

Reachability:
E<> Controller.Reconfigured

Safety:
A[] not (Queue.Overflow)

Bounded response:
A[] PacketLost imply Controller.ReactsWithinDeadline

Recovery:
A[] ChannelFailed imply A<> StableConfiguration

Policy consistency:
A[] FlowRuleInstalled imply SwitchTableConsistent
```

В твоей модели уже перечислены типовые запросы: отсутствие deadlock, достижимость значимых состояний, ограниченность очередей, согласованность правил и таблиц потоков, подтверждение до deadline, обработка packet-in, отказа канала и деградации зондирования. Это почти готовый seed для `uppaal.generate_property_pack`. 

## 7. Перевод требований в UPPAAL-запросы

Отдельная задача — сделать слой:

```text
natural language / domain requirement
        ↓
formal property template
        ↓
UPPAAL query
```

Например:

```text
"После отказа канала система должна либо перейти в устойчивую конфигурацию, либо откатиться"
```

в:

```text
A[] Channel.Failed imply A<> (Controller.Stable || Controller.Rollback)
```

Но тут нужна осторожность: LLM будет легко генерировать красивые, но неверные формулы. Поэтому нужен валидатор: существуют ли такие automata/location/variables в модели.

## 8. Counterexample parser

Вот это прям must-have. Если свойство не выполняется, сервер должен не просто вернуть лог UPPAAL, а превратить trace в понятную трассу:

```text
t=0    PHY.Normal
t=3    MAC.QueueGrowth
t=5    MAC.Overflow
t=5    Controller.NoRule
t=8    PacketDropped
```

И дальше:

```json
{
  "violation": "Queue overflow before controller reaction",
  "path": [
    {"time": 0, "automaton": "PHY", "state": "Normal"},
    {"time": 3, "automaton": "MAC", "state": "QueueGrowth"},
    {"time": 5, "automaton": "MAC", "state": "Overflow"}
  ],
  "likely_cause": "controller_deadline too loose or queue bound too small"
}
```

Это не фантазия: в работах по автоматной верификации отдельной задачей прямо выделяется преобразование контрпримера в путь в системе автоматов. 

## 9. Маппинг трассы обратно в предметную область

Для статьи по SDN-ISAC нужно, чтобы контрпример объяснялся не так:

```text
Controller.l3 -> Switch.l7 -> Queue.l2
```

а так:

```text
Контроллер не успел установить flow rule до переполнения очереди.
Пакет был отброшен без явно указанной причины.
Это нарушает свойство bounded response для packet-in.
```

То есть нужен domain layer:

```text
UPPAAL entity → SDN/ISAC meaning
```

Например:

```json
{
  "Controller.Reconf": "реактивная перенастройка",
  "MAC.BufferFull": "переполнение буфера",
  "PHY.SensingDegraded": "ухудшение качества зондирования",
  "Service.SLAViolated": "нарушение SLA"
}
```

## 10. Шаблоны моделей для твоей иерархии

Для SDN-ISAC я бы сделал не один универсальный генератор, а набор template builders:

```text
build_phy_automaton()
build_mac_queue_automaton()
build_sdn_controller_automaton()
build_service_sla_automaton()
build_failure_detector()
build_reconfiguration_policy()
build_packet_flow()
```

У тебя в модели уже есть 4 слоя: PHY, MAC, SDN/control plane и сервисный уровень; автоматы взаимодействуют через интерфейсы и события.  Это можно прямо превратить в domain-specific API MCP-сервера.

## 11. Борьба со взрывом состояний

Это будет боль. Не “может быть”, а точно будет.

Нужны задачи:

* ограничение счётчиков;
* bound для очередей;
* ограничение числа пакетов;
* ограничение числа попыток реконфигурации;
* выключение необязательных подсетей;
* композициональная проверка;
* проверка по слоям;
* абстрактная модель → детализированная модель только для проблемного компонента.

Это совпадает с твоей идеей иерархии: не строить один монолитный автомат для всей сети, потому что он будет сложным, плохо интерпретируемым и склонным к взрывному росту состояний.  В лекционных материалах по model checking это ровно называется “state explosion problem”, а среди способов борьбы называются символьная верификация, редукция частичных порядков и композициональная верификация. 

## 12. Кэширование результатов

Запуски `verifyta` могут быть тяжёлыми. Нужно кэшировать:

```text
hash(model.xml + queries.q + verifyta_version + flags)
        ↓
verification_result.json
```

Чтобы не гонять одно и то же по 100 раз, когда LLM просто переформулирует вопрос.

## 13. Генерация отчётов

Полезный MCP-tool:

```text
uppaal.generate_report(model, queries, results)
```

Выход:

```text
- список проверенных свойств
- статус каждого свойства
- время проверки
- найденные нарушения
- краткая интерпретация
- фрагменты трасс
- рекомендации по исправлению модели
```

Для статьи можно сразу получать таблицу:

| Property | Query | Result | Interpretation |
| -------- | ----- | ------ | -------------- |

## 14. Benchmark suite

Нужны тестовые модели:

```text
- tiny deadlock model
- queue overflow model
- bounded response model
- channel failure recovery model
- SDN packet-in model
- sensing degradation model
- intentionally broken model
```

И отдельно regression tests: модель должна падать там, где ожидается падение, и проходить там, где ожидается прохождение.

Это не формальность. В benchmark-библиотеке для parametric timed model checking прямо говорится, что без стабильного набора benchmark-ов трудно честно оценивать новые алгоритмы и инструменты. 

## 15. Интеграция с другими инструментами

UPPAAL хорош для обычных timed automata, но если ты полезешь в параметры, синтез параметров и неизвестные timing constants, одного UPPAAL может быть мало.

Потенциальные адаптеры:

```text
UPPAAL      → обычная верификация timed automata
IMITATOR    → parametric timed automata / parameter synthesis
Spin        → untimed/discrete automata / LTL
Python      → генерация моделей, отчётов, графов
Graphviz    → визуализация автоматов
```

Но в MVP я бы **не лез в parameter synthesis**. Общие PTA быстро упираются в неразрешимость: в обзоре по parametric timed automata прямо сказано, что для общих PTA большинство нетривиальных задач неразрешимы, а ограничения на число параметров или область параметров в общем случае не спасают. 

## 16. Безопасность

Так как MCP-сервер будет запускать внешнюю бинарь, нужны:

```text
- sandbox/temp directory
- запрет произвольных shell-команд
- subprocess без shell=True
- timeout
- max file size
- max query count
- max model size
- kill process tree
- allowlist путей
```

Иначе LLM случайно или через prompt injection может устроить мусор.

## 17. Packaging

Нужно сделать нормальную установку:

```text
pip install uppaal-mcp
```

или:

```text
docker run -v ./models:/workspace uppaal-mcp
```

Конфиг:

```toml
[uppaal]
verifyta_path = "/opt/uppaal/bin/verifyta"
timeout_sec = 60
workspace = "./workspace"
max_model_size_mb = 20
```

## 18. Документация и примеры

Минимум:

```text
examples/
  simple_deadlock/
  sdn_packet_in/
  queue_overflow/
  channel_failure_recovery/
  phy_sensing_degradation/
```

И README:

```text
- как поставить UPPAAL
- как указать verifyta
- как подключить MCP в Claude/Cursor/другой клиент
- какие tools доступны
- пример запуска
- пример отчёта
```

## Какой backlog я бы сделал

### MVP

```text
1. MCP server skeleton
2. verifyta runner
3. validate_model
4. verify(model, queries)
5. parse stdout/stderr
6. timeout/resource limits
7. simple JSON result
8. 5 тестовых UPPAAL-моделей
```

### Нормальная версия

```text
9. XML parser
10. model summary
11. query validator
12. property pack generator
13. batch verification
14. counterexample parser
15. report generator
16. caching
```

### Исследовательская версия под твою статью

```text
17. SDN-ISAC domain templates
18. PHY/MAC/SDN/Service automata builders
19. mapping trace → SDN-ISAC explanation
20. automatic property generation from article requirements
21. benchmark suite for SDN-ISAC scenarios
22. comparison: static resource split vs SDN-controlled orchestration
23. export tables/figures for paper
```

Моё мнение: начинать надо не с “генерации UPPAAL XML из текста”, а с **надёжного verifier-assistant**:

```text
модель есть → MCP проверяет → объясняет → показывает контрпример → предлагает правку
```

Генерация модели с нуля — красивая, но грязная задача. А вот проверка, property packs, counterexample explanation и отчёты — это прям полезный инструмент для статьи и диссертации.



# Задачи связанные с PHY_level_formalization_reviewed-2026-06-06-143000.tex  
Да. Для этого `.tex` есть прям отдельный слой задач, которых нет в обычном “UPPAAL MCP”. Файл уже не просто про запуск `verifyta`, а про **контрактную PHY-модель с абстракцией радиофизики в конечные классы**, five-automata composition и observer-автоматы.

Самые важные специфичные задачи:

## 1. Extractor из LaTeX-спецификации в машинную модель

MCP должен уметь вытаскивать из `PHY_level_formalization...tex`:

```text
A_CH, A_SIG, A_BM, A_SQ, A_PH
ENV_CH, ENV_TARGET, ENV_MAC, ENV_NET
clocks
channels
enums/classes
assumptions
guarantees
transition schemes
observer automata
UPPAAL queries
```

То есть отдельный tool:

```text
phy_spec.extract_contract_model(tex)
```

Выход:

```json
{
  "automata": ["A_CH", "A_SIG", "A_BM", "A_SQ", "A_PH"],
  "env": ["ENV_CH", "ENV_TARGET", "ENV_MAC", "ENV_NET"],
  "clocks": ["c_meas", "c_sig", "c_sense", "c_report", "c_rec", "c_ssb", "aos_bs", "aos_ctrl", "c_obs"],
  "broadcast_channels": ["channel_report", "signal_report", "beam_report", "sensing_report", "phy_kpi_report"],
  "handshake_channels": ["measure_tick", "pilot_config", "waveform_config", "beam_cmd", "recovery_cmd"]
}
```

Это специфично именно для твоего файла, потому что там PHY задан как композиция пяти автоматов плюс `ENV`, а не как произвольная UPPAAL-модель.

## 2. Генератор UPPAAL-модели из PHY-контракта

Нужен tool:

```text
phy_spec.generate_uppaal_model(contract_json)
```

Он должен собирать `.xml` не “как получится”, а строго по архитектуре:

```text
A_PHY = A_CH || A_SIG || A_BM || A_SQ || A_PH
A_SYS = A_PHY || A_ENV
```

В твоей общей модели ISAC PHY — это первый уровень иерархии, который порождает KPI вроде CRB, Pd, Pfa, AoS, coverage и resolution, но не симулирует I/Q-физику полностью.  В `.tex` это уже уточнено жестче: timed automata проверяют реакцию на дискретные классы, а не вычисляют SINR/Pd/CRB.

## 3. Валидатор “не тащи радиофизику в guards”

Это прям критичная специфичная задача.

MCP должен проверять, что в guards автоматов нет такого:

```text
SINR_c < SINR_min
Pd < 0.95
CRB_R > threshold
Rfa > Rfa_max
```

А должно быть только:

```text
SINRClass == LOW
PdClass == FAILED
CRBClass == UNUSABLE
AoSClass == EXPIRED
```

Tool:

```text
phy_spec.check_no_continuous_phy_guards(model)
```

Потому что статья явно разводит:

```text
estimator / analytic layer → alpha_PHY → finite classes → timed automata
```

Это хорошая правка. Обычные timed automata работают с конечной дискретной логикой, часами, guards и resets; базовая теория timed automata как раз строится вокруг конечного числа real-valued clocks и constraints на переходах, а не вокруг вычисления радиофизических вероятностей. 

## 4. Реестр `alpha_PHY` и проверка консервативности

В `.tex` есть центральная функция:

```text
alpha_PHY: X_meas × X_cfg → X_disc
```

Для MCP нужны tools:

```text
phy_alpha.list_classes()
phy_alpha.validate_thresholds()
phy_alpha.classify_sample(meas, cfg)
phy_alpha.check_boundary_policy()
phy_alpha.generate_enum_declarations()
```

Особенно важно проверить правило:

```text
boundary(good, bad) → bad
```

То есть пограничные и неопределенные случаи уходят в худший класс. Это нужно, чтобы safety-проверки не были липовыми.

## 5. Проверка приоритетной классификации `A_CH`

Для `A_CH` нужна отдельная задача:

```text
phy_ch.check_priority_determinism()
```

Проверять надо порядок:

```text
Outage > Blockage > InterferenceLimited >
MobilityLimited > MultipathLimited > ChannelNominal
```

И гарантировать:

```text
ch_enabled_count <= 1
```

Иначе автомат канала станет недетерминированным при одновременных нарушениях, например:

```text
SINRClass = OUTAGE
PowerClass = LOW
IClass = CRITICAL
```

Правильный результат — `OUTAGE`, а не случайный выбор между несколькими переходами.

## 6. Проверка `A_SIG`: waveform как переменная, а не состояние

В `.tex` важная архитектурная правка: `OFDM`, `OTFS`, `AFDM`, `SC`, `OTHER` — это значения переменной `W`, а не отдельные состояния.

MCP должен ловить ошибочную генерацию:

```text
Location_OFDM
Location_OTFS
Location_AFDM
```

и требовать:

```text
int W in {OFDM, OTFS, AFDM, SC, OTHER}
```

А состояния должны быть:

```text
SignalNominal
PilotBasedSensing
PayloadAssistedSensing
SignalReconfiguring
SignalLimited
```

Tool:

```text
phy_sig.check_waveform_not_state()
```

## 7. Проверка `A_BM`: recovery deadline

Это одна из самых конкретных задач.

В `.tex` исправлена типичная ошибка:

```text
BeamRecover invariant: c_rec <= D_BM
```

Значит переход с guard:

```text
c_rec > D_BM
```

никогда не сработает. Правильно:

```text
c_rec == D_BM
```

Tool:

```text
phy_bm.check_recovery_deadline_semantics()
```

Он должен искать невозможные guards вида:

```text
location invariant: c <= D
transition guard: c > D
```

и выдавать ошибку:

```text
Переход недостижим: invariant запрещает c_rec > D_BM.
Используй c_rec == D_BM или убери invariant и проверяй deadline observer-ом.
```

## 8. Проверка “ровно один outcome” для beam recovery

Для `A_BM` нужен property pack:

```text
если вошли в BeamRecover,
то не позже D_BM должно случиться ровно одно:
beam_restored!
handover_hint!
beam_failure!
```

Tool:

```text
phy_bm.generate_recovery_observer()
```

И запрос:

```text
A[] not ObsBeamRecovery.Violation
```

Плюс отдельная проверка взаимоисключения outcome-событий.

## 9. Проверка `A_SQ`: sensing quality зависит от трех отчетов

В предыдущей версии, судя по рецензии, была архитектурная дырка: sensing quality могла зависеть не от всех нужных источников. В текущей версии `A_SQ` слушает:

```text
channel_report?
signal_report?
beam_report?
```

MCP должен проверять, что `A_SQ` реально получает все три входа, иначе модель опять станет слабой.

Tool:

```text
phy_sq.check_required_inputs()
```

Плюс проверка приоритета:

```text
SensingFailure > FreshnessLimited > AccuracyLimited >
ProbabilityLimited > FalseAlarmLimited > CapacityLimited >
CoverageLimited > SensingQoSOk
```

## 10. Проверка `A_PH`: единый источник истины для `PHYState`

`PHYState` должен обновлять только `A_PH`.

Tool:

```text
phy_ph.check_single_writer()
```

Он должен запрещать такое:

```text
A_CH updates PHYState
A_SQ updates PHYState
A_BM updates PHYState
```

И требовать:

```text
A_CH/A_SIG/A_BM/A_SQ публикуют reports
A_PH читает reports
A_PH обновляет PHYState
```

Это важно, иначе будут гонки и противоречивые состояния.

## 11. Проверка каналов: report = broadcast, command = handshake

Очень специфичная задача для этого `.tex`.

Должно быть:

```text
broadcast chan channel_report, signal_report, beam_report, sensing_report, phy_kpi_report;
```

А команды:

```text
chan measure_tick, pilot_config, waveform_config, beam_cmd, recovery_cmd;
```

Tool:

```text
phy_sync.check_channel_semantics()
```

Он должен ловить:

```text
channel_report declared as chan
```

и ругаться, потому что обычный handshake в UPPAAL синхронизируется только с одним получателем. А report нужен одновременно `A_SQ`, `A_PH` и observer-автоматам. UPPAAL действительно расширяет базовые timed automata практическими механизмами вроде integer variables, broadcast channels, urgent/committed locations; это как раз тот уровень, на котором надо аккуратно строить модель. 

## 12. Проверка “один sync на edge”

В `.tex` явно сказано: если нужны и деградация, и отчет, нельзя пихать два sync на один переход. Нужно либо:

```text
channel_report!
```

с payload-флагом деградации, либо отдельная self-loop:

```text
Outage -- phy_outage! --> Outage
```

Tool:

```text
phy_spec.check_single_sync_per_transition()
```

Это полезно, потому что LLM при генерации UPPAAL легко напишет невалидную псевдомодель.

## 13. Генератор observer-автоматов из deadline-условий

В `.tex` правильно замечено: `p --> q` в UPPAAL — это unbounded leads-to, дедлайн он не задает.

Нужны tools:

```text
phy_observer.generate_bounded_response_observer(trigger, response, deadline)
phy_observer.generate_freshness_observer()
phy_observer.generate_beam_recovery_observer()
phy_observer.generate_contract_observer()
```

Например:

```text
sensing_degraded? → phy_kpi_report? within D_report
aos_ctrl_expired? → SensingState == FreshnessLimited within D_sense
recovery_start? → beam_restored/handover_hint/beam_failure within D_BM
```

## 14. Генератор `ENV`-stub автоматов

Без `ENV` модель открытая, и `A[] not deadlock` будет либо бессмысленным, либо случайным.

Нужен tool:

```text
phy_env.generate_closed_environment()
```

Он должен создавать:

```text
ENV_CH      → measure_tick!
ENV_TARGET  → target_detected!, классы PRS/Beam/Blockage
ENV_MAC     → pilot_config!, waveform_config!, recovery_cmd!, extra_ssb_cmd!
ENV_NET     → mac_report_delivered!, controller_report_delivered!
```

Это специфично для файла, потому что там `ENV` явно не считается PHY-компонентом, а нужен только для закрытой проверки.

## 15. Проверка assume–guarantee цепочки

В `.tex` есть цепочка:

```text
Gar_CH, Gar_SIG, Gar_BM → Ass_SQ
Gar_CH ∧ Gar_SIG ∧ Gar_BM ∧ Gar_SQ → Ass_PH
Gar_PH → Ass_MAC/SDN
```

Нужны tools:

```text
phy_contract.extract_assumptions()
phy_contract.extract_guarantees()
phy_contract.check_closure()
phy_contract.generate_contract_queries()
```

Запросы:

```text
A[] (ass_ch()  imply not A_CH.ContractViolation_CH)
A[] (ass_sig() imply not A_SIG.ContractViolation_SIG)
A[] (ass_bm()  imply not A_BM.ContractViolation_BM)
A[] (ass_sq()  imply not A_SQ.ContractViolation_SQ)
A[] (ass_ph()  imply not A_PH.ContractViolation_PH)
```

Это лучше, чем просто “проверить модель”, потому что статья именно про контрактную PHY-модель.

## 16. Counterexample classifier: физический сценарий или артефакт абстракции

В `.tex` прямо есть важная мысль: counterexample может быть либо реальным сценарием, либо артефактом грубой over-approximation.

Нужен tool:

```text
phy_cex.classify_counterexample(trace, alpha_PHY, estimator_constraints)
```

Результат:

```json
{
  "counterexample_type": "possible_physical_scenario | abstraction_artifact | unknown",
  "reason": "Boundary class over-approximation caused simultaneous LOW and OUTAGE classes",
  "suggested_action": "Replay trace in estimator/simulator"
}
```

Это прям хорошая научная фишка для статьи: MCP не просто показывает трассу, а помогает отделить ошибку модели от допустимой консервативной абстракции. В model checking counterexample вообще является ключевым результатом при невыполнении спецификации: модель проверяется против формулы, а при нарушении строится контрпример. 

## 17. PHY-specific property pack

Для этой статьи property pack должен быть не общий, а такой:

```text
Deadlock:
A[] not deadlock

Reachability:
E<> A_PH.PHYNormal
E<> A_PH.PHYSensingDegraded
E<> A_PH.PHYCommunicationDegraded
E<> A_PH.PHYJointDegraded

Aggregation consistency:
A[] (A_PH.PHYNormal imply (comm_ok && sensing_qos_ok))

Classifier determinism:
A[] (ch_enabled_count <= 1)
A[] (sq_enabled_count <= 1)

Contract:
A[] (ass_ch() imply not A_CH.ContractViolation_CH)
...

Bounded degradation report:
A[] not ObsSenseReport.Violation

Freshness:
A[] not ObsFreshness.Violation

Beam recovery:
A[] not ObsBeamRecovery.Violation
```

Tool:

```text
phy_property_pack.generate()
```

## 18. Проверка priced/weighted расширения для `Pi_PHY`

В `.tex` есть важное ограничение: `Pi_PHY` — это не часть обычного timed automaton, если он используется как накопленная стоимость.

MCP должен ловить, если кто-то пытается проверить оптимальность:

```text
minimize Pi_PHY
```

в обычном UPPAAL TA без priced/weighted semantics.

Tool:

```text
phy_score.check_score_semantics()
```

Ответ должен быть:

```text
Pi_PHY можно:
1) оставить внешним SDN-score после отчета;
2) или переводить модель в priced/weighted timed automata.
В базовой TA-модели проверяются классы и deadlines, не оптимальность score.
```

Это корректно: weighted timed automata — отдельное расширение, где costs назначаются локациям и переходам, а optimal reachability уже решается как отдельная задача. 

## 19. Не лезть в parameter synthesis внутри UPPAAL-MCP

В этом `.tex` много порогов:

```text
SINR_min
Pd_min
Rfa_max
AoS_max
D_report
D_sense
D_BM
```

Очень соблазнительно сделать MCP, который “подбирает параметры”. Но это лучше вынести отдельно. Для general parametric timed automata быстро начинается ад: у PTA многие нетривиальные задачи неразрешимы, а даже ограничение числа параметров или области параметров не всегда спасает. 

Нормальная задача MCP:

```text
phy_threshold.instantiate_profile(profile_name)
```

Например:

```json
{
  "profile": "conservative_safety",
  "D_report": 10,
  "D_sense": 5,
  "D_BM": 8
}
```

А не “найди все параметры, при которых свойства выполняются”.

## Итоговый backlog именно под этот `.tex`

### MVP

```text
1. Спарсить enums/classes из X_disc.
2. Спарсить clocks и channels.
3. Разделить channels на broadcast reports и handshake commands.
4. Сгенерировать skeleton UPPAAL для A_CH/A_SIG/A_BM/A_SQ/A_PH.
5. Сгенерировать A_ENV как композицию ENV stubs.
6. Сгенерировать базовые queries.
7. Запустить verifyta.
8. Вернуть отчет: какие свойства прошли, какие нет.
```

### Полезная версия

```text
9. Проверить alpha_PHY: нет continuous guards.
10. Проверить priority determinism для A_CH и A_SQ.
11. Проверить c_rec == D_BM в BeamRecover.
12. Проверить single writer для PHYState.
13. Проверить single sync per transition.
14. Сгенерировать observer-автоматы для deadlines.
15. Распарсить counterexample в терминах PHY/SDN/ISAC.
```

### Исследовательская версия

```text
16. Counterexample replay against estimator/simulator assumptions.
17. Сравнение разных threshold profiles.
18. Генерация таблицы свойств для статьи.
19. Генерация traceability matrix: утверждение в статье → автомат → query → результат.
20. Экспорт артефактов: model.xml, queries.q, results.json, report.md.
```

Моё мнение: для этой статьи самый ценный MCP — не “универсальный UPPAAL-запускатель”, а **PHY-contract verifier assistant**. Он должен знать, что такое `alpha_PHY`, `A_CH`, `A_SIG`, `A_BM`, `A_SQ`, `A_PH`, report channels, ENV-stubs и bounded observers. Тогда это будет реально научный инструмент, а не просто обертка над `verifyta`.
