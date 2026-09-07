Проверка базовой работоспособности UPPAAL MCP — 6 сентября 2026

Базовое ядро работает в существующем окружении с `mcp 1.27.2`, однако обнаружены воспроизводимые дефекты запуска и обработки результатов. Считать всю систему исправной нельзя.

Изучены `AGENTS.md`, `CONTRIBUTING.md`, `manifests/v1.md`, `manifests/collaboration-v1.yaml`, активный `manifests/baselines/reviewer-r1.yaml`, инструкции CLI и CI. Проверен commit `11bd69bdca9a1209f820258b3732b3c865f79035` ветки `read`. В запросе указан отсутствующий путь `D:\uppaal\_mcp\manifests`; фактические manifests находятся в `D:\uppaal_mcp\manifests`.

Запуски выполнены в отдельном detached worktree `repo/` этого каталога. Python — 3.14.5, Windows; это не воспроизведение Ubuntu/Python 3.12 из CI. Исходный checkout содержит пользовательские изменения; его исходники не редактировались. Текущие XML дополнительно скопированы в `current-files/` и проверены статически. Issue не назначен: результат является локальной диагностикой, не принятой работой P0/P3, gate decision или PR. Публикация в GitHub не выполнялась.

**Подтверждённые проблемы, в порядке приоритета**

1. **P1 — неверный положительный статус runner при ошибке или неполном выводе.** Для двух запросов синтетический вывод одного успешного запроса, `returncode=1` и `stderr="syntax error"` даёт общий `status="satisfied"`. Один результат из двух при exit 0 также даёт этот статус. `src/uppaal_mcp/verifyta.py:316` рассматривает результаты раньше кода возврата и ошибок; полнота результатов относительно queries не проверяется. Это может привести к ошибочному verification claim. Нужны приоритет ошибок процесса и проверка полноты результатов. Семь случаев с воспроизводящим скриптом: [runner-diagnostic/README.md](runner-diagnostic/README.md), [JSON](runner-diagnostic/synthetic_runner_results.json). Эти случаи полностью синтетические; они не являются model checking evidence.

2. **P1 — чистая установка не запускает MCP.** `python -m pip install -e .` установил `mcp 2.1.1`, разрешённый зависимостью `mcp>=1.0.0` (`pyproject.toml:12`). Импорт `mcp.server.fastmcp.FastMCP` в `server.py:19` для этой версии не работает. Ошибка ошибочно описывается как отсутствие установленного пакета. Проверены `build_mcp()` и запуск настоящего stdio-сервера: оба завершаются ошибкой. При этом test suite пишет `OK (skipped=1)`, потому что `tests/test_phy_layer.py:582` превращает этот RuntimeError в пропуск теста. Следует определить поддерживаемую версию SDK и сделать проверку обязательного MCP-запуска чувствительной к несовместимости. [Installation log](install.log), [startup stderr](cli-smoke/build-mcp.stderr.txt), [MCP diagnostics](mcp-smoke/README.md).

3. **P2 — exit code CLI не отражает сбой.** Для `error`, `timeout`, `tool_not_found` CLI возвращает код 0 и только печатает JSON (`src/uppaal_mcp/cli.py:270`, `:278`, `:688`). Подтверждено отдельными дочерними процессами; безусловный успех shell-команды не означает успех операции. Реальная команда `uppaal-verifyta version` без настройки пути также вернула JSON `tool_not_found` с exit 0. До исправления автоматизация должна анализировать статус JSON. [Synthetic cases](runner-diagnostic/synthetic_runner_results.json), [actual default-path result](cli-smoke/version-default.stdout.txt).

4. **P2 — локальные пути требуют настройки.** Путь по умолчанию в `src/uppaal_mcp/config.py:11` отсутствует. Реальный executable обнаружен в `D:\UPPAAL\app\bin\verifyta.exe`; с `--verifyta-path` он запускается. `mcp_conf.conf` содержит WSL-пути другого checkout `/mnt/c/Users/musta/...`; они не соответствуют текущей native Windows среде. Постоянная конфигурация не изменялась. Точная версия из процесса: `UPPAAL 5.0.0 (rev. 714BA9DB36F49691), June 2023`. Историческая запись baseline о проблеме лицензии в WSL не описывает результат нынешнего native Windows smoke-запуска. [Version result](cli-smoke/version-explicit.stdout.txt).

5. **P2 — baseline не соответствует текущим файлам и не заморожен.** Различаются 6 из 20 записанных файловых SHA-256: PHY model/query, MAC model/generator, SDN generator, Application XML. Общий `generator_hash` также различается; `source_hash` и хеш scientific plan совпадают. LF-нормализация не устраняет шесть различий. Структурная coordination-проверка контролирует только хеш scientific plan, поэтому её успех не подтверждает остальные хеши. Baseline сам содержит `candidate`, `frozen: false`, `Gate 1: pending`, пустые accepted runs и незаданные канонические параметры/instances/queries. Объединённая четырёхуровневая модель и принятый interface contract отсутствуют в baseline. [Exact expected/current hashes](runner-diagnostic/baseline_hash_comparison.json).

Дополнительное противоречие manifests: обязательное хранение runs в `evidence/runs/<run_id>/` (`collaboration-v1.yaml:492`) не входит в типовые write scopes P3/P4 (`:317`, `:349`). Это вопрос governance до оформления принимаемых evidence, не обнаруженный runtime-сбой. Никакие manifests не исправлялись в рамках этой диагностики.

**Результаты запусков**

| Проверка | Результат | Evidence |
|---|---|---|
| Чистая editable-установка, Python 3.14.5 | Установка завершена; `pip check` — exit 0; MCP 2.1.1 несовместим с сервером | [commands.json](cli-smoke/commands.json) |
| Unit suite в чистом окружении | 74 теста: 73 успешны, 1 пропущен; exit 0 | [unit-tests.log](unit-tests.log) |
| Unit suite с существующим MCP 1.27.2, исходники из чистого worktree | Все 74 теста успешны, без пропусков; exit 0 | [stderr](existing-env-tests/stderr.txt), [command](existing-env-tests/command.json) |
| MCP через stdio, существующий SDK | Initialize, 76 инструментов, 39 вызовов, 86 проверок без ошибок; ошибочный ввод обработан, сервер завершён | [MCP report](mcp-smoke/README.md) |
| Генерация PHY/MAC/SDN из явных TeX-путей, generic static validation, property packs `--static-only` | Все три слоя проходят доступные проверки; model checking здесь не выполнялся | [CLI commands and results](cli-smoke/commands.json) |
| Статические benchmark suites через MCP | 21 PHY + 12 MAC + 24 SDN случаев соответствуют ожиданиям, включая намеренно некорректные модели | [MCP summary](mcp-smoke/existing-mcp-1/summary.json) |
| Текущие XML из пользовательского checkout | 6 файлов проходят generic static checks; для 5 PHY/MAC/SDN моделей выполнены также layer static checks; Application — только generic static | [current files results](current-files/results.json) |
| Coordination и YAML | Coordination exit 0; оба YAML-manifest разбираются PyYAML 6.0.3, повторяющиеся ключи не обнаружены | [coordination.log](coordination.log), [YAML results](current-files/yaml-results.json) |

PHY semantic validation сообщает 21 предупреждение о broadcast-каналах без отправителей/получателей; они сохранены в MCP evidence. Отсутствие ошибок этих статических проверок не доказывает правильность сетевой модели.

**Реальный verifyta smoke**

Пять встроенных моделей выполнены отдельными запусками с таймаутом 10 секунд, `trace_on_violation` (`-t0`) и явным путём executable. Все пять процессов завершились с exit 0; получены явные результаты всех 13 запросов. Каждая ссылка ниже ведёт к записи с `run_id`, `status`, `model_hash`, `query_hash`, точной `tool_version`, командой, конфигурацией, средой, оборудованием и stdout/stderr. Статус `success` относится к полноте завершения запуска, а verdict каждого свойства записан отдельно.

| Модель | run_id / evidence | status | Результаты запросов |
|---|---|---|---|
| bounded_response | [20260906T154644Z-13e00b9de267-f45835fd](verifier-smoke/runs/20260906T154644Z-13e00b9de267-f45835fd/run.json) | success | 3 satisfied |
| deadlock | [20260906T154645Z-90d8bc09e9b7-3d400f0c](verifier-smoke/runs/20260906T154645Z-90d8bc09e9b7-3d400f0c/run.json) | success | Отсутствие deadlock: not_satisfied; достижимость Stuck: satisfied; trace сохранён |
| deadlock_free | [20260906T154645Z-61acd60a66c1-48c40263](verifier-smoke/runs/20260906T154645Z-61acd60a66c1-48c40263/run.json) | success | 2 satisfied |
| phy_contract_skeleton | [20260906T154646Z-9abb1f1c97ed-df5b904f](verifier-smoke/runs/20260906T154646Z-9abb1f1c97ed-df5b904f/run.json) | success | 3 satisfied |
| queue_overflow | [20260906T154646Z-624922da61a1-81167510](verifier-smoke/runs/20260906T154646Z-624922da61a1-81167510/run.json) | success | 3 satisfied; один из запросов подтверждает достижимость Overflow |

Это диагностические встроенные модели. Результаты не относятся к P3/frozen baseline, не подтверждают свойства полной модели статьи и не означают принятие Gate 1. Метрики states/peak memory помечены `not_available`: в этих запусках они не получены. Лицензия не менялась. GUI, WSL и GitHub branch protection не проверялись.

**Воспроизведение и сохранность**

Основные команды: `python -m pip install -e .`, `python -m unittest discover -s tests -v`, `python scripts/check_coordination.py`, `uppaal-verifyta list-examples`, `uppaal-verifyta version`, `uppaal-verifyta --verifyta-path "D:\UPPAAL\app\bin\verifyta.exe" version`. Точные cwd, executable, аргументы и environment overrides сохранены в linked JSON и скриптах `cli_check.py`, `verifier_check.py`, `current_files_check.py`, `mcp-smoke/smoke.py`, `runner-diagnostic/reproduce.py`. Повторный запуск следует выполнять в новом каталоге diagnostics, чтобы сохранить эти результаты.

Статус исходного checkout после проверки совпадает с исходным списком изменений; хеши проверенных текущих моделей не изменились за время проверки. Изолированный worktree чист. [Original status](current-files/original-git-status.txt), [isolated status](current-files/isolated-git-status.txt). Отчёт и evidence находятся вне репозитория; исправления кода, commits и PR не создавались.
