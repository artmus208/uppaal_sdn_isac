# Пакет активации v2 — Issue #64

Статус: **подготовлено для review; активация Integrator ещё не записана**.
Issue: https://github.com/artmus208/uppaal_sdn_isac/issues/64.
Owner: `vadimnbkg`; reviewer/integrator: `artmus208`, независимо от автора.
Process: P0; Atomic IDs: `N/A — coordination-only`.
Base: `read`, `09d5eac96128e9f90a428584dd661addb5488931`.
Branch: `codex/vadimnbkg/64-v2-activation`; PR target: `read`.

## Основание и результат

Предложение v2 принято review `artmus208` от 2026-09-28T19:49:56Z и merged
через [PR #63](https://github.com/artmus208/uppaal_sdn_isac/pull/63),
merge commit `6af33db047b3ef842036f5db7c5f9722f01fedaf`.
В review явно разрешена подготовка отдельного activation Issue/PR. Пользователь
поручил «PR слиты, давай делать шаг 3». Подготовка не является самостоятельным
решением автора об активации, merge или научной приёмке.

- `manifests/current.json` выбирает научный план, coordination contract,
  migration map, operational guide, baseline и ссылку на activation Issue.
- `manifests/collaboration-v2.yaml` сохраняет 25 IDs, primary ownership,
  P3 core/complete и зависимости P5/P9. Добавлены правила evidence, bounded
  uncertainty и осуществимости семейства P4 из принятого научного плана.
- `CONTRIBUTING-v2.md`, AGENTS и формы GitHub направляют новые задачи к pointer.
- Checker читает pointer без fallback на v1 и отдельно проверяет historical pins.
  Наличие configured pointer в workstream-ветке не означает activation approval.

`manifests/v1.md`, `manifests/collaboration-v1.yaml`, frozen baseline и
`CONTRIBUTING.md` сохраняются побайтно. Генератор и все `src/**` неизменны.
AGENTS уже был operational context, а не строгим model input; этот механизм
сохранён. Фактическое XML и candidate query set должны совпадать с frozen bytes.

При первой проверке обнаружено, что CONTRIBUTING.md тоже является strict pin:
попытка его обновить дала `ValueError: pinned source changed: CONTRIBUTING.md`
(12 tests прошли, один reproduction test завершился ошибкой). Собственная
правка восстановлена, инструкции вынесены в отдельный guide; scope Issue #64
уточнён до его создания. После исправления все 13 focused tests прошли.
Механизм pins и historical inventory не ослаблялись.

## Переход существующих задач

[open-issues-map.json](open-issues-map.json) фиксирует все Issues, наблюдавшиеся
открытыми при подготовке. Это одноразовое соответствие, не live status board.
Владельцы, scopes, обязательные зависимости и прошлые решения сохраняются;
новые scoped задачи после активации читают текущий pointer.

#62 завершил публикацию предложения через #63; передача записи v2/migration
к #64 зафиксирована в обоих Issues. Старые artifacts #62 воспроизводятся на
их commits: содержащиеся там проверки прежнего scope не предназначены для
будущих изменений AGENTS или активации. Они не переписываются.

PR #61 вошёл в base через `09d5eac…`. Эта миграция не принимает и не переоткрывает
P3 core/complete: используются отдельные decisions #39/#61 в их точном scope.
Deferral #36 и D01, отрицательные verdicts, timeout/error и доступность raw
artifacts не меняются. Ни один scientific workstream не объявляется разблокированным.

## Шаг 4 — как завершить активацию

1. Reviewer проверяет diff, evidence и сохранение historical inputs, затем
   принимает activation PR. Автор не заменяет это собственным review.
2. Integrator сливает activation PR в `read`.
3. Integrator записывает в Issue #64 точный merge commit, время начала применения
   и ссылку на PR. После этой записи новые задачи применяют v2 по current pointer.
   Отдельного третьего implementation PR или переписывания старых результатов
   для этого не требуется.

Шаблон записи после слияния (заполняется фактическими значениями):

```text
Активирую scientific plan manifests/v2.md и collaboration-v2.yaml
через manifests/current.json для новых задач в read.
Activation commit: <точный merge commit activation PR>
Effective at: <фактическое время в UTC>
Decision by: <Integrator>
Activation PR: <ссылка>
Scope: operational coordination only; historical inputs и прежние
scientific acceptance records сохраняются в исходной области.
Open-issue mapping: evidence/governance/20260928-v2-activation/open-issues-map.json
```

## Проверки и воспроизведение

Из корня отдельного checkout опубликованного head:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e . PyYAML
.venv/bin/python scripts/check_coordination.py
.venv/bin/python evidence/governance/20260928-v2-activation/check_activation.py
.venv/bin/python scripts/check_coordination.py --audit-hashes --commit HEAD --output /tmp/v2-activation-baseline-new.json
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -c "from uppaal_mcp.server import build_mcp; print(type(build_mcp()).__name__)"
.venv/bin/uppaal-verifyta list-examples
.venv/bin/uppaal-verifyta version
git diff --check 09d5eac96128e9f90a428584dd661addb5488931...HEAD
```

Hash-audit output path должен быть новым. Полная suite включает regression,
сравнивающую regenerated XML/candidate queries с frozen bytes и запрещающую
генератору чтение operational v2 inputs. Это воспроизведение/статическая проверка,
а не новый UPPAAL model-checking run.

Итог: **200 tests OK**, все восемь команд exit 0; 57 baseline file hashes и
aggregate hashes без расхождений. XML model hash, candidate-query hash и
generator hash совпали с frozen inputs. YAML parse, scope, локальные ссылки,
server/examples smoke и verifier availability успешны. Новых verification runs
нет. Строки о hash errors/mismatches внутри unit-test stdout относятся к
отрицательным fixtures; отдельный audit baseline расхождений не обнаружил.

Проверенный чистый source checkpoint: `a5b9c49b67976ed28a7282cef06bad98ac0196df`,
Git tree `4b356aa7a14ed1282bdc92139984e075b4aafc6a`.
После полного прогона добавлены только результаты/summary в этом evidence scope.
[validation.json](validation.json) содержит точные команды и exit codes;
[baseline-hashes.json](baseline-hashes.json), [logs/](logs/) и
[environment.txt](environment.txt) — сохранённые результаты и окружение.
[artifacts-sha256.json](artifacts-sha256.json) индексирует итоговые artifacts.

Полная локальная история сохранена в
`/mnt/c/users/musta/desktop/pysources/mcp_uppaal/evidence/governance/20260928-v2-activation/handoff/checked-source.bundle`.
Публикация через GitHub Git data API может менять commit metadata; равенство
публикуемого и локального финального Git tree проверяется перед handoff.
Точный опубликованный head и способ получения результата записываются в PR
и Issue #64; они не встраиваются в собственные tracked bytes.
