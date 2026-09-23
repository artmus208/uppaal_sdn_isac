# Gate 1 — пакет замены baseline, Issue #6

Статус: **подготовлен к рассмотрению; Gate 1 не принят**. P1/P2 приняты
пользователем и записаны в #15/#17/#19 и PR #47. Новых задач не создано.

Base: `a7a67f0c7ac74d6a7d4ccb2c5e9fbf12954c8150` (`read`).
Точный source commit с provenance compatibility: `a190e10df1b7ce4923f0d18c664b4eef8715eb58`
(опубликованная ветка этого PR).
Branch: `codex/vadimnbkg/6-gate1-baseline`; owner: vadimnbkg.

## Что предлагается зафиксировать

`proposed-baseline.yaml` заменяет исторический dirty capture новой точной
конфигурацией. Он пока содержит `frozen: false`, `gate_1.passed: false`.
Оригинал сохранён без изменений в `historical-candidate.yaml`.

- Полная XML композиция: `model.xml`, 50 процессов.
- Исходный candidate pack: `candidate-queries.q`.
- Набор для дальнейшей проверки: `selected-queries.q`, 15 запросов;
  все результаты пока null в `selected-queries.json`.
- Полная disposition candidate pack: `query-disposition.json`.
- Параметры и границы абстракции: `parameters.json`.
- Entity/process vector и queue/attempt overlays: `instance-vector.json`.
- Точные исходные generation metadata: `generation.json`.
- SHA-256 каждого входа и aggregates source/generator: в proposed manifest.

Модель и полный candidate query set побайтово совпадают с принятой P1/P2
конфигурацией. Selected queries — точная копия принятого #47 набора.
После разрешённого обновления provenance XML и queries остаются прежними,
но generator_hash и source_hash изменились и пересчитаны явно.
Исходный commit генерации и commit публикации generated artifacts различны:
первый указан выше, второй определяется HEAD этого PR. Это не dirty snapshot.

Ограничения принятого scope из #47 сохраняются полностью: время абстрактное,
физической калибровки нет; timing claims неисправленных observers не принимаются;
они остаются в полной композиции. C01/C02 ещё не доказаны. Не изменяются модели,
рукопись или принятые значения параметров. P3/P4 не начинаются до Gate 1.

## Инструмент

Точная версия: UPPAAL 5.0.0 (rev. 714BA9DB36F49691), June 2023.
`verifyta-version.txt` извлечён из сохранённого raw stdout принятого #46;
строка версии не подставлена вручную. `tool-evidence.json` содержит точный
run_id/status/model_hash/query_hash/tool_version, команду и ссылки на архив
для ранее выполненного engine-load `E<> true` на той же XML. Это подтверждение
работоспособности инструмента в записанном окружении на дату запуска, не
доказательство C01/C02 и не обещание доступности лицензии на любом компьютере.
Нового UPPAAL запуска этот governance пакет не выполняет.

## Воспроизведение

Python project dependencies и PyYAML 6.0.3. Из checkout исходного commit с
добавленным только этим пакетом:

```bash
python -B evidence/governance/20260906-baseline/gate1-20260923/prepare.py
python -B evidence/governance/20260906-baseline/gate1-20260923/check.py
python -B evidence/instantiation/20260923-recovery-attempts/audit.py
python scripts/check_coordination.py
```

`prepare.py` пересоздаёт proposed manifest и derived metadata и проверяет
равенство source Git blobs. `check.py` независимо сверяет каждый file hash и
оба aggregate с точными checkout bytes через существующий auditor #6.
Это static/hash audit, не model checking. Сохранённый результат — `audit.json`.

## Совместимость и окончательное решение

Пользователь разрешил минимальное изменение loader и regression test в #6.
Loader строго проверяет сохранённый historical-candidate.yaml по прежнему
SHA-256. Текущий baseline manifest записывается в context_document_hashes с
фактическим SHA-256 и ролью active_governance_record_audited_separately.
Модель не читает значения из этого governance record: его содержимое проверяет
отдельный hash audit. Генерация сама по себе **не подтверждает** валидность
или принятие активного manifest. Все остальные научные source pins сохраняются.
Так устранена циклическая зависимость manifest hash -> generator -> manifest.

Новый manifest установлен по штатному пути manifests/baselines/reviewer-r1.yaml
в этой PR-ветке как candidate/frozen=false. Его байты равны proposed-baseline.yaml.
Source commit закрепляет исходники генерации, включая историческую копию;
его active manifest ещё старый. Это намеренное разделение input snapshot и
последующей записи о нём. Старые generator metadata labels candidate и исходный
vector status сохраняются как provenance, не как текущее решение gate.

Проверки: профильные регрессии сохранения XML/query и отказа при повреждении
historical/scientific inputs; согласованность candidate/frozen flags; полный
software suite; аудит активного manifest и исходных Git pins. Результаты команд
и ограничения публикуются в checks.txt и active-audit.json.

Осталось только отдельное решение integrator по этому пакету Gate 1 и merge.
В существующем #6 записываются commit, model/generator/query hashes, parameters,
vector, tool version, время и субъект решения. Только после этого manifest
получает frozen=true и gate passed=true. Подтверждение изменения provenance
не трактуется как автоматическое принятие Gate 1. P3/P4 пока не разблокированы.
