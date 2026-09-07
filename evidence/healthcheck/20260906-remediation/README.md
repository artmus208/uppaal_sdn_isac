# Исправления healthcheck от 6 сентября 2026

Координационный handoff: [Issue #1](https://github.com/artmus208/uppaal_sdn_isac/issues/1).
Owner: `carwasher`. Atomic IDs: `N/A — coordination-only`. Base ref: `origin/read`,
commit `11bd69bdca9a1209f820258b3732b3c865f79035`. Все PR направлены в `read`;
независимое review и принятие ожидаются. Эта запись — снимок результатов, а не
решение о merge или прохождении научного gate.

## Исправления по приоритету

| Пункт исходного отчёта | Результат | Handoff |
|---|---|---|
| 1, P1: ложный положительный статус runner | Ошибки процесса имеют приоритет; требуется полный набор результатов с согласованными query IDs; частичные данные сохраняются для диагностики | [Issue #2](https://github.com/artmus208/uppaal_sdn_isac/issues/2), [PR #8](https://github.com/artmus208/uppaal_sdn_isac/pull/8) |
| 2, P1: несовместимый MCP при чистой установке | Поддерживаемый SDK `mcp>=1.28,<2`; ошибка обязательного запуска больше не превращается в skipped test; проверяется настоящий stdio-старт | [Issue #3](https://github.com/artmus208/uppaal_sdn_isac/issues/3), [PR #7](https://github.com/artmus208/uppaal_sdn_isac/pull/7) |
| 3, P2: CLI возвращает 0 при сбое | Код 0 означает успешную операцию/ожидаемую отрицательную проверку, 1 — отрицательный результат проверки, 2 — сбой или неопределённый результат; JSON сохранён | [Issue #4](https://github.com/artmus208/uppaal_sdn_isac/issues/4), [PR #9](https://github.com/artmus208/uppaal_sdn_isac/pull/9) |
| 4, P2: пути Windows/WSL | Приоритет явных настроек и PATH, обнаружение native Windows UPPAAL, рабочий пример MCP-конфигурации и инструкции | [Issue #5](https://github.com/artmus208/uppaal_sdn_isac/issues/5), [PR #10](https://github.com/artmus208/uppaal_sdn_isac/pull/10) |
| 5, P2: дрейф baseline и отсутствие freeze | Полная сверка файловых и общих хешей реализована как отдельная диагностика. Изменение baseline и run-storage требует решения интегратора | [Issue #6](https://github.com/artmus208/uppaal_sdn_isac/issues/6), [конкретное предложение](governance-proposal.md) |

Каждый независимый результат подготовлен в своей ветке и worktree. Научные
модели, manuscript и manifests не редактировались. Исправления ещё не объединены
в `read`: нельзя использовать этот handoff как запись о принятии dependencies.

## Проверки программного поведения

- Runner: 22 focused tests, полный suite — 92 теста без skips/failures;
  все 7 синтетических случаев исходного отчёта дают ожидаемый статус.
- MCP: две чистые установки с SDK 1.28.0 и 1.29.1; в каждой 80 тестов без
  skips/failures, `pip check`, `build_mcp`, настоящий stdio initialize/list_tools
  с 76 инструментами.
- CLI: 86 тестов без skips/failures, включая 12 тестовых методов с реальными
  дочерними процессами; missing-tool `version` возвращает ожидаемый exit 2;
  сборка wheel, dependency и coordination checks завершились с exit 0.
- Конфигурация: 85 тестов без skips/failures; native verifyta найден без
  environment overrides. Исходное окружение MCP 1.27.2 и новое MCP 1.29.1
  проверены отдельно: оба stdio-сеанса перечислили 76 инструментов и выполнили
  по 4 read-only вызова. Пример конфигурации не меняет глобальные настройки
  Codex автоматически; перенос секций описан в README соответствующего PR.
- CI каждого из PR #7, #8, #9 и #10 завершился успешно. Workflow репозитория
  использует Ubuntu/Python 3.12. Локальные проверки выше использовали
  Windows 11/Python 3.14.5. Ссылки и commit SHA приведены в `results.json`.

Локальные README каждого исправления содержат команды воспроизведения и точные
пути к raw stdout/stderr. Git attributes в каталогах evidence сохраняют исходные
байты логов Windows; записанные хеши сверены с Git blobs. Неудачные промежуточные
попытки runner сохранены и явно отделены от финального run d.

Это программные regression checks и проверки запуска. Новое model checking
не выполнялось. Статические проверки, ответы синтетического verifyta и его
version banner не подтверждают свойства сетевой модели или Gate 1.

## Сверка baseline

[audit_baseline.py](audit_baseline.py) проверяет все записанные пары `path/sha256`
и общие `source_hash`/`generator_hash`, сохраняя ожидаемые и фактические значения.
Он не переписывает manifests; exit 1 означает дрейф или отсутствующие входы.

- [Текущий checkout](current-checkout-hashes.json): различаются 6 из 20
  файловых хешей и общий generator hash. Все пары и агрегаты независимо совпали
  с исходной диагностикой отчёта.
- [Точные Git blobs базового commit](base-commit-hashes.json): различаются
  7 из 20 файловых хешей и общий generator hash. Это отдельный набор байтов;
  исторический manifest был снят с dirty checkout.
- Source aggregate совпадает в обоих режимах. Structural coordination check
  проходит, но сам по себе не проверяет эти model/generator hashes.

Воспроизведение из корня отдельного worktree (выберите новые output paths):

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install PyYAML==6.0.3
.venv/Scripts/python.exe -B evidence/healthcheck/20260906-remediation/audit_baseline.py --repo D:/uppaal_mcp --output evidence/healthcheck/20260906-remediation/recheck-current.json
.venv/Scripts/python.exe -B evidence/healthcheck/20260906-remediation/audit_baseline.py --repo D:/uppaal_mcp --commit 11bd69bdca9a1209f820258b3732b3c865f79035 --output evidence/healthcheck/20260906-remediation/recheck-commit.json
```

Ожидаемый exit обоих audit-запусков на исходных входах — 1. Результаты
coordination/diff checks и сверки с исходным отчётом сохранены в [checks.json](checks.json).

## Оставшееся решение

В [Issue #6](https://github.com/artmus208/uppaal_sdn_isac/issues/6) предложены
явная замена исторического candidate после выбора clean commit и непересекающиеся
run-пути `evidence/verification/runs/<run_id>/` для P3 и
`evidence/scalability/runs/<run_id>/` для P4. Подробный текст для review:
[governance-proposal.md](governance-proposal.md).

`AGENTS.md` требует: «Любой файл в `manifests/` меняется только в отдельном
governance Issue с manifest-specific write scope и принятым решением Integrator».
Issue создан; принятое решение отсутствует. Поэтому manifests остаются
неизменными, baseline — candidate/unfrozen, Gate 1 — pending. Кроме решения по
формату нужны принятые результаты научных P1/P2, integrated model, interface
contract, параметры, instances и queries. Обновление хешей не заменяет их.

Дополнительное наблюдение передано координатору в Issue #1: downstream MAC/SDN
reports могут показывать отдельные частичные verdicts независимо от общего
статуса failed run. Они требуют отдельного назначения и scope при дальнейшем
исправлении; частичные результаты runner сохранены как диагностические данные.

## Сохранность и provenance

Исходный отчёт хранится без изменений в
`D:/uppaal_mcp_healthcheck_20260906_184139/REPORT.md`; его копия
[original-REPORT.md](original-REPORT.md) имеет SHA-256
`8822ba3eb6ff4f65482f3fc63e936512ef2fad0843592f8f5d3159a243af3194`.
Относительные ссылки внутри этой исторической копии разрешаются относительно
исходного каталога healthcheck. Исходные diagnostic artifacts не перезаписывались.

Состояние и хеши 60 пользовательских изменённых/неотслеживаемых файлов исходного
checkout записаны в [original-checkout-before.json](original-checkout-before.json).
Финальная сверка — [scope-and-artifact-audit.json](scope-and-artifact-audit.json):
проверены scopes четырёх коммитов, хеши их файлов в Git и сохранность исходного
checkout. [audit_handoff.py](audit_handoff.py) воспроизводит её, используя
`results.json`; для нового снимка передайте `--output <new-file.json>`, сохранив
существующий `scope-and-artifact-audit.json`. Координационный write scope этого Issue — только
`evidence/healthcheck/20260906-remediation/**`.
