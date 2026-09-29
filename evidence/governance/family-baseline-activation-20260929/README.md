# Оформление baseline семейства UAV — Issue #74

Основание: [решение пользователя/Integrator A/B и P1/P2](https://github.com/artmus208/uppaal_sdn_isac/pull/73#issuecomment-5890790922).
Пакет #73 принят и слит; его входы закреплены commit
`c439b0811c8f0063ee44e968587d08a46361b4b4`.
База этой работы: `read`, `939ccbcba8d6d3381eb4c4288a0cd6de432dfd2d`.

## Что закреплено

`manifests/baselines/uav-family-r1.yaml` материализует принятое семейство N=1…4
как **frozen inputs**. Поле `frozen: true` относится к принятой области входов;
статус `frozen_inputs_pending_operational_activation` и отдельный контракт
активации не позволяют считать наличие этого файла разрешением запуска.
Это новая схема finite-family-input-baseline, а не замена исторической схемы.
Она записана в JSON-подмножестве YAML и проверяется без внешних зависимостей.

Скопированы точные четыре записи моделей из принятого пакета: hashes исходников,
генератора, XML, параметров, instance vectors, интерфейсной инвентаризации и
всех 30 отдельных P4-запросов. Версия UPPAAL взята из сохранённого evidence.
Она не является утверждением о доступности лицензии/инструмента на будущем host.

A/B и applicability уже приняты пользователем; повторная научная приёмка тех же
решений не запрашивается. Работа оформляет их операционное использование.
Достижимость обслуживания остаётся открытой. Таймауты не дают verdict.
R03/R04/C06, работоспособность сети, fairness, SLA, физическая калибровка и
перенос P3 не принимаются этим manifest.

## Совместимость и выбор

`manifests/current.json`, исторический baseline и все frozen generation inputs
сохранены побайтно. Default `metadata.baseline_manifest` и исторический
`gates.gate_1.decision_source` в v2 продолжают ссылаться на reviewer-r1.yaml.
Добавленный `family_baseline_selection` задаёт отдельный выбор для P4:
его Issue обязан закрепить ID, SHA-256 manifest, source commit и решение
активации. Для явно выбранного семейства gate определяется его решением об
области входов и последующей записью операционной активации. Исторический
Gate 1 сохраняется в собственной области.

Это декларативный контракт назначения задачи, а не автоматический selector
в runner. Никакой запуск не начинается от появления manifest или успешного
аудита. P4 требует отдельно принятого протокола, ресурсов и разрешения запуска.

Исторический `scripts/check_coordination.py --audit-hashes` проверяет прежнюю
single-model схему. Новый `scripts/check_family_baseline.py` проверяет семейство.
В обычном режиме ему не нужна Git history (включая shallow CI): он проверяет
106 неизменных входов и seals принятого пакета. Единственный изменённый вход
контекста — operational collaboration-v2.yaml — остаётся привязанным к старому
commit в provenance; текущая версия проверяется на явную политику выбора.
`--audit-history` дополнительно сверяет все 107 исходных Git blobs.
Это не исключение для model/generator/query drift: все такие входы проверяются
в текущем дереве. Новая политика не используется историческим генератором.

## Воспроизведение

```sh
python3 -B evidence/governance/family-baseline-activation-20260929/materialize.py
python3 -B scripts/check_family_baseline.py
python3 -B scripts/check_family_baseline.py --audit-history
python3 -B scripts/check_coordination.py
PYTHONPATH=src python3 -B -m unittest discover -s tests -v
```

`materialize.py` по умолчанию только сравнивает; `--write` воссоздаёт новый manifest.
Для historical audit нужна полная история с исходным commit; ошибка его
отсутствия не подменяется успехом. Полный прежний hash-аудит требует PyYAML:

```sh
python3 scripts/check_coordination.py --audit-hashes --commit HEAD --output /tmp/historical-audit-UNIQUE.json
```

Команды, exit codes и логи этой работы сохраняются в `checks/`.
Все проверки статические/программные, новых запусков UPPAAL нет.

## Завершение активации

После независимой приёмки и слияния этого PR в `read` Integrator записывает в
Issue #74 решение с фактическим merge commit и временем UTC. Запись должна
закрепить ID `uav-family-r1-20260929`, hash нового manifest и разрешить его явный
выбор для P4 в принятой области A/B. Исторический default не переключается.
Запись делает операционную активацию доступной будущему P4 Issue. Источником
актуального статуса остаётся Issue, поэтому историческую отметку подготовки
в manifest не требуется переписывать следующим PR.

Готовый шаблон (поля заполняются только после реального события):

```text
Decision actor: user/integrator
Activation time UTC: <actual time>
Activation merge commit: <actual merge SHA>
Baseline ID: uav-family-r1-20260929
Manifest path: manifests/baselines/uav-family-r1.yaml
Manifest SHA256: <hash at activation merge commit>
Input scope / P1/P2 / A/B decision: PR73#issuecomment-5890790922
Activation: accepted for explicit P4 Issue selection in that limited scope
Historical baseline/default: unchanged
Service reachability: OPEN
P4 execution authorization: NOT GRANTED by this activation
```

## Handoff

Issue #74; P0; N/A — coordination-only. Owner `vadimnbkg`, independent
Reviewer/Integrator `artmus208 / user-integrator`.
Branch `codex/vadimnbkg/74-family-baseline`; base указан выше; точный опубликованный
HEAD и PR записываются в Issue. Working tree перед handoff: clean.
Scope: новый family manifest, collaboration-v2.yaml, отдельные checker/tests,
этот каталог evidence. Другие manifests, source/model/query и manuscript не менялись.

Durable transport: canonical remote branch и полный bundle
`/mnt/d/uppaal_mcp/evidence/governance/family-baseline-activation-20260929/handoff/final.bundle`.
Следующий шаг — независимая приёмка PR и запись активации по шаблону выше.

## Полученные результаты

Все 209 unit tests прошли, включая девять новых тестов семейства. Coordination,
воспроизведение manifest, текущий/исторический аудит семейства и MCP/CLI smokes
завершились с exit 0. Исторический single-model audit системным Python сверил
57 файлов и агрегаты без расхождений.

Первый historical audit в test virtualenv завершился с exit 2: `No module named
'yaml'`. Он сохранён в validation.json/historical-audit.log. Повтор выполнен
системным Python с уже установленным PyYAML 6.0.3; команда, причина и успешный
результат записаны в historical-audit-retry.json. Поэтому общий первый запуск
проверяющего процесса имеет exit 1, хотя unit suite и все остальные проверки
прошли; эта ошибка окружения устранена успешным повтором аудита.
