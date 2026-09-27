# Предложение манифеста v2 — Issue #62

Статус: **proposal / not active**, подготовлен для review. Это governance deliverable,
а не новая научная приёмка или verification evidence.

- Issue: https://github.com/artmus208/uppaal_sdn_isac/issues/62
- Owner: `vadimnbkg`.
- Base: `read`, `fef5e9f71d58803727a63efc36ab944e08655a31`.
- Branch: `codex/vadimnbkg/62-manifest-v2`; target PR: `read`.
- Baseline как исторический вход: `reviewer-r1-gate1-20260923`.
- Atomic IDs: `N/A — coordination-only`; закрытие замечаний не заявляется.
- Разрешение: пользователь сказал «Делай!» после предложения подготовить v2
  и карту перехода в отдельном governance scope. Решение о подготовке записано
  в Issue #62; активация, merge и принятие научных результатов в него не входят.
- Write scope: два новых файла `manifests/v2.md`, `manifests/v2-migration.md`
  и этот evidence-каталог. Открытые Issues проверены перед назначением;
  пересечений с этими новыми путями не обнаружено. Старый #6 не переиспользуется.

## Артефакты и обоснование

[Манифест v2](../../../manifests/v2.md) задаёт контракт утверждений, типы evidence,
предпосылки редукций и композиции, осуществимость серии P4 и критерии завершения
статьи. [Карта перехода](../../../manifests/v2-migration.md) сохраняет все 25 ID,
owners и исторические решения; определяет отдельный scope будущей активации.

Основание пересмотра — мета-аудит статьи и диссертации Глониной, сопоставленный
с сохранёнными P1/P2, P3 и текущими generation inputs. Нужны более точные
границы утверждений и способы завершать обязательства, а не автоматическое
расширение текущей статьи до общего метода для произвольных сетей.

| Наблюдение | Изменение предложения |
|---|---|
| Истинность свойства, завершение запуска и приёмка результата различаются. | Независимые evidence/status/scope поля; отрицательные результаты и budget exhaustion не закрывают требования автоматически. |
| Локальная проверка требует отдельного переноса на композицию. | Контракт предпосылок, свойств, observer/harness и non-vacuity. |
| Подготовка произвольного instance family не следует из одной работающей конфигурации. | Предварительная осуществимость P4; новые semantics/generator требуют baseline decision. |
| Статистика simulation и exhaustive model checking решает разные задачи. | Разделение методов/затрат; R04 сохраняет собственную экспериментальную границу и P4 ownership. |
| Исторические v1/collaboration-v1 входят в закреплённые generation inputs. | Дополнительные proposal files; активная координация и historical inputs разделяются только будущей миграцией. |

Точные входные файлы и их SHA-256: [inputs.json](inputs.json). Источники и печатные
страницы перечислены в обоих документах. Сопоставление с диссертацией не является
доказательством применимости её теорем к нашей модели. Документы P1/P2 и P3
содержат собственную хронологию; их копирование в список входов не превращает
предложение решения в принятое решение. PR #61 этим пакетом не принимается.

## Проверка содержания

Вспомогательный агент автора проверил восемь аспектов: статус proposal,
ID/ownership, P3 milestones/P5, независимость evidence/status полей, отрицательные
результаты, transfer/non-vacuity, роли observers и семейство P4. Найденное
двусмысленное правило частичного query set исправлено: требуется `status=success`
и явный query verdict; partial stdout failed run остаётся диагностикой.
Уточнено, что вариации допускаются только внутри принятого семейства.
В R04 явно сохранено требование сравнивать экспериментальную границу.
Это содержательная самопроверка с помощью агента, не независимое approval.

## Воспроизведение технической проверки

Из корня отдельного чистого checkout опубликованного head:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e . PyYAML
.venv/bin/python evidence/governance/20260927-manifest-v2/check_proposal.py
.venv/bin/python scripts/check_coordination.py
.venv/bin/python scripts/check_coordination.py --audit-hashes --commit HEAD --output /tmp/manifest-v2-review-hashes.json
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -c "from uppaal_mcp.server import build_mcp; print(type(build_mcp()).__name__)"
.venv/bin/uppaal-verifyta list-examples
.venv/bin/uppaal-verifyta version
git diff --check fef5e9f71d58803727a63efc36ab944e08655a31...HEAD
```

Для hash audit нужен новый, ещё не существующий output path. Audit proposal
проверяет scope, owners из действующего YAML, локальные ссылки и сохранность
исторических inputs. Действующий coordination checker проверяет совместимость
v1 и его hashes, а не научную правильность/активацию v2. Ни эти проверки,
ни `verifyta version` не являются model checking.

Результаты: [validation.json](validation.json), [логи](logs/),
[hash audit](baseline-hashes.json), [окружение](environment.txt).
Все восемь команд завершились с exit code 0: 193 unit tests, proposal integrity,
coordination, 57 точных file hashes и aggregate hashes без расхождений, server
и examples smoke, доступность verifier и whitespace check. Строки о намеренных
hash mismatches внутри unit-test stdout относятся к отрицательным fixtures;
самостоятельный audit текущего baseline расхождений не обнаружил.
`verifyta --version` вернул UPPAAL 5.0.0 (rev. 714BA9DB36F49691); моделей в рамках
этой задачи не проверяли. После тестов меняются только summary/evidence artifacts,
тексты v2 и migration и код остаются на проверенном source tree.

## Сохранность результата

Тестируемый локальный source commit и опубликованный source commit имеют
одинаковое Git tree; точное соответствие записано в
[publication-source.json](publication-source.json). Публикация через GitHub API
меняет commit metadata/историю checkpoint, но не байты проверенных входов.
Полная локальная история дополнительно экспортирована в bundle в долговременном
checkout владельца; SHA-256 artifacts сохраняются в
[artifacts-sha256.json](artifacts-sha256.json). Финальный head с validation records
указан в PR и Issue #62; он не встраивается в собственные tracked bytes.

Следующий шаг — независимое review предложения; активация требует отдельного
scope по карте перехода. Научная приёмка и downstream workstreams этим пакетом
не открываются.
