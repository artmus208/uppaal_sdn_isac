# Совместная разработка несколькими ChatGPT/Codex-аккаунтами

Этот документ описывает операционный процесс. Научная декомпозиция и критерии
результатов находятся в `manifests/v1.md`; постоянные ограничения для агентов —
в `AGENTS.md`.

## 1. Модель совместной работы

ChatGPT-аккаунты не должны координироваться через память чатов. Общая схема такая:

```text
GitHub Issue (assignment + contract)
        ↓
one chat → one branch → one worktree/clone
        ↓
commit(s) + artifacts + test/evidence records
        ↓
Pull Request to protected `read` (handoff)
        ↓
independent review / gate decision
        ↓
`P9a Integration draft` → `P8 Language` → `P9b Final assembly` on `read`
        ↓
final integration PR: `read` → stable `main`
```

ChatGPT Projects помогают держать связанные чаты и источники вместе, но не
заменяют GitHub как межаккаунтный источник истины. Для каждого аккаунта можно
создать собственный local project, связанный только с его clone/worktree. Для
каждого deliverable запускается отдельный чат. См. официальную документацию:
<https://learn.chatgpt.com/docs/projects>.

Для параллельных изменений используй отдельные Git worktrees. Они дают каждому
чату независимый checkout, но используют общие Git metadata; одна и та же ветка
не может одновременно находиться в нескольких worktrees. См.:
<https://learn.chatgpt.com/docs/environments/git-worktrees>.

## 2. Роли без фиксированного списка участников

Имена и аккаунты в репозитории заранее не назначаются. Для каждого Issue явно
заполняются роли:

- `Owner` — единственный аккаунт, выполняющий deliverable;
- `Reviewer` — проверяет acceptance criteria и evidence;
- `Integrator` — принимает gate и объединяет совместные результаты;
- `Runner` — при необходимости выполняет реальный запуск UPPAAL на заявленном
  оборудовании; может совпадать с Owner, но provenance всё равно фиксируется.

Reviewer, принимающий gate, не может быть Owner того же результата.

Нельзя использовать общие пароли, ChatGPT-сессии, GitHub tokens или UPPAAL
license data. Каждый аккаунт использует собственные credentials и локальные
секреты. Секреты не коммитятся.

## 3. Однократная ручная настройка GitHub

Эти действия требуют прав администратора репозитория и выполняются через
GitHub UI. Они не появляются автоматически после добавления этого файла.

1. Дать каждому реальному GitHub-аккаунту необходимый доступ к репозиторию.
2. Защитить обе ветки `main` и `read` через branch protection rule или ruleset.
   `main` является стабильной веткой, `read` — integration branch текущего
   reviewer round. Для обеих веток:
   - запретить прямые изменения и требовать Pull Request;
   - требовать минимум одно одобрение;
   - сбрасывать устаревшее одобрение после новых commits;
   - требовать разрешения review conversations;
   - запретить force push и удаление ветки;
   - применять правила также к администраторам либо явно документировать каждое
     исключение;
   - после первого успешного запуска CI сделать обязательным check
     `Python 3.12 tests and coordination checks`. Не указывать check до его
     появления в GitHub: до этого результаты команд прикладываются к PR вручную.
3. Включить Issues и Pull Requests.
4. Создать labels как минимум для процессов `P0`–`P8`, `P9a`, `P9b`, состояний
   `ready`, `blocked`, `in-review`, `accepted`, типа `governance` и gates.
5. Проверить, что merge возможен только после одобрения Reviewer/Integrator и
   выполнения обязательных checks.
6. Направлять workstream PRs в `read`. После `P9b Final assembly` открывать
   отдельный финальный integration PR из `read` в `main`.

Защита ветки не заменяет write scopes: GitHub защищает merge, а scope защищает
параллельные процессы от конфликтующих изменений.

## 4. Onboarding нового аккаунта

1. Получить доступ к <https://github.com/artmus208/uppaal_sdn_isac> под
   собственным GitHub-аккаунтом.
2. Выбрать стабильный короткий `<account-id>` для имён веток. Не записывать в
   документацию вымышленные имена.
3. Настроить Git identity локально в своём clone/worktree:

   ```bash
   git config user.name "<git-name>"
   git config user.email "<git-email>"
   ```

4. Прочитать назначенный Issue, `AGENTS.md`, этот файл и относящиеся к задаче
   manifests, прежде всего `manifests/v1.md`.
5. Проверить зависимости и Gate 1. Если Issue не содержит deliverable,
   acceptance criteria или write scope, не начинать изменения — сначала
   дополнить Issue.
6. Создать отдельный ChatGPT/Codex chat только для этого Issue и передать ему
   Issue URL/number, `<base-ref>`, base commit и разрешённый write scope.
7. Создать отдельную ветку и отдельный worktree/clone по инструкции ниже.

## 5. Контракт GitHub Issue

Один Issue описывает один принимаемый deliverable. Рекомендуемый шаблон:

```text
Process: P0..P7 | P8 Language | P9a Integration draft | P9b Final assembly
Deliverable:
Atomic IDs: C01..C06 | R01..R07 | V01..V05 | I01..I06 | D01
Owner account:
Reviewer:
Integrator:
Base ref:
Base commit:
Target branch: read
Input manifests and hashes:
Dependencies:
Required gate:
Write scope:
Read-only inputs:
Out of scope:
Acceptance criteria:
Expected artifacts:
Verification required: yes/no
Status: ready/claimed/blocked/in-review/accepted
```

Atomic IDs стабильны и не содержат номера/префикса reviewer. Используй `C01`, а
не `Reviewer2-C01`. Допустимые диапазоны: `C01–C06`, `R01–R07`, `V01–V05`,
`I01–I06`, `D01`. ID нельзя перенумеровывать или повторно назначать другому
смыслу; каждый ID имеет ровно одного Owner. Префиксы обозначают `CORE`,
`RELATED`, `VALIDATION`, `INDEPENDENT`, `DEFERRED` соответственно.
Для чисто координационной задачи, не закрывающей reviewer requirement, укажи
`N/A — coordination-only` и объясни цель в поле `Deliverable`.

Правила claim:

- Owner назначает себя через GitHub assignee или получает явное назначение.
- После назначения Issue переводится из `ready` в `claimed`.
- Второй аккаунт не начинает тот же Issue и не использует тот же write scope.
- Блокер записывается в Issue с выполненными проверками и требуемым решением.
- Передача задачи другому аккаунту оформляется сменой assignee и handoff-комментарием
  с веткой, commit, незавершёнными пунктами и состоянием артефактов.

## 6. Изолированная рабочая копия

Никогда не используй общий dirty checkout. Сначала проверь:

```bash
git status --short
git fetch origin
```

### Вариант A: отдельный worktree

Из чистого основного clone:

```bash
git worktree add \
  ../uppaal_sdn_isac-<account-id>-<issue-number> \
  -b codex/<account-id>/<issue-number>-<deliverable-slug> \
  <base-ref>
cd ../uppaal_sdn_isac-<account-id>-<issue-number>
```

`<base-ref>` всегда берётся из Issue. Для текущего reviewer round нормальный
пример — `origin/read`; не подставляй `origin/main` по умолчанию.

Если worktree создан приложением ChatGPT/Codex с detached `HEAD`, используй
кнопку `Create branch here` либо создай именованную ветку до первого commit:

```bash
git switch -c codex/<account-id>/<issue-number>-<deliverable-slug>
```

### Вариант B: отдельный clone

```bash
git clone git@github.com:artmus208/uppaal_sdn_isac.git \
  uppaal_sdn_isac-<account-id>-<issue-number>
cd uppaal_sdn_isac-<account-id>-<issue-number>
git fetch origin
git switch -c codex/<account-id>/<issue-number>-<deliverable-slug> <base-ref>
```

Не checkout-ь чужую ветку и не подключай два аккаунта к одной рабочей папке.

## 7. Установка и базовые проверки

Требуется Python 3.10 или новее. Окружение создаётся отдельно в каждом
worktree/clone:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
```

Основной test suite:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -v
```

Smoke checks:

```bash
python -c "from uppaal_mcp.server import build_mcp; print(type(build_mcp()).__name__)"
uppaal-verifyta list-examples
```

Проверка доступности реального verifier:

```bash
uppaal-verifyta version
```

`uppaal-verifyta version` не является model checking run. Ошибка запуска,
лицензии, WSL interop или сети должна быть дословно зафиксирована в PR; её нельзя
заменять вручную указанной строкой версии.

Для изменения конкретного слоя добавляй его generator/static checks из
`COMMAND_REFERENCE.md`. В PR перечисляй точные команды, exit codes и результат.

## 8. Write scopes и конфликтные файлы

Issue перечисляет пути буквально или узким glob. Пример:

```text
Write scope:
- src/uppaal_mcp/sdn/**
- tests/test_sdn_layer.py
- tests/fixtures/sdn_*.golden.xml
```

Если фактический diff содержит другой путь, PR не готов к review.

Особые правила:

- `levels_tex/samplepaper.tex` изменяют только `P9a Integration draft` и
  `P9b Final assembly`;
- `P8 Language` возвращает отдельный `editorial patch`, но не применяет его к
  рукописи;
- любой файл в `manifests/` меняется только отдельным governance Issue с явным
  manifest-specific write scope и принятым решением Integrator;
- generated artifacts должны иметь уникальный `run_id`/каталог; один процесс не
  перезаписывает артефакты другого;
- изменение shared interface или schema требует отдельного решения, потому что
  оно меняет входы нескольких процессов.

Для проверки scope перед PR:

```bash
git status --short
git diff --name-only <base-ref>...HEAD
git diff --check <base-ref>...HEAD
```

## 9. Verification и evidence

Различай два результата:

```text
static validation: XML/query/reference checks without model checking
verification: real UPPAAL/verifyta execution with machine result
```

Для каждого verification run сохраняются и передаются:

```text
run_id
status
source_commit
source_hash
generator_hash
model_hash
query_hash
parameter_set
instance_vector
tool_version
command
operating_environment
hardware_description
runtime
peak_memory
states_explored
result_per_query
stdout_reference
stderr_reference
counterexample_reference
```

Поля, которых инструмент не выдаёт, помечаются `not_available`; их нельзя
выдумывать. `status=error`, `timeout`, `oom`, пустой `result_per_query` или
отсутствующий hash не подтверждают verification claim.

P3 и P4 могут запускаться параллельно после Gate 1, но каждый пишет отдельные
immutable runs. Общий evidence bundle собирается из принятых runs; два процесса
не редактируют один results-файл одновременно.

## 10. Gates

### Gate 1 — Frozen model baseline

P0 сначала публикует baseline candidate. P1 и P2 проверяют и дополняют его
решениями по validation, параметрам, instantiation и abstraction. Gate 1
принимается только после P1/P2 и превращает candidate во frozen baseline для P3,
P4 и последующей привязки P5.

Обязательная запись в Issue/PR:

```text
base_commit
base_ref
manuscript_hash
model_source_hash
generator_hash
query_set_hash
parameter_set
instance_vector
tool_version
gate_reviewer
decision: accepted/rejected
decision_reference
```

Изменение любого frozen input создаёт новую версию baseline и требует нового
решения Gate 1. Hardware не является глобальным полем baseline: он записывается
на каждый run.

P5 классифицируется как `RELATED`. Его draft можно готовить после P1/P2, но
закрыть P5 можно только после P3: каждый принятый сценарий должен ссылаться на
принятый `verification_run_id`.

### Process acceptance

Процесс принят, когда Reviewer проверил acceptance criteria, команды, scope и
артефакты и записал `accepted` в Issue/PR. PR без такого решения остаётся
`in-review`.

### Integration sequence

```text
accepted P1..P7
       ↓
P9a Integration draft
       ↓
P8 Language (editorial patch only)
       ↓
P9b Final assembly
       ↓
final consistency check on `read`
       ↓
integration PR: `read` → `main`
```

Если `P8 Language` обнаружил содержательную, а не редакторскую проблему, она
возвращается в соответствующий процесс новым Issue, а не исправляется скрытно в
P8.

## 11. Commits и Pull Requests

Commit должен быть небольшим, воспроизводимым и относящимся к одному Issue.
Рекомендуемый заголовок:

```text
<process>: <imperative deliverable summary> (#<issue-number>)
```

Перед push:

```bash
git status --short
git diff --check
PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -v
git push -u origin codex/<account-id>/<issue-number>-<deliverable-slug>
```

Workstream PR открывается в защищённую ветку `read`, а не в `main`, и содержит
следующие handoff-поля:

```text
Issue: Closes #<issue-number>
Process:
Deliverable:
Owner account:
Base commit:
Base ref:
Head commit:
Target branch: read
Write scope:
Changed paths:
Input manifest/hash:
Artifacts and hashes:
Commands executed:
Test results and exit codes:
Verification evidence: run_id/status/model_hash/query_hash/tool_version or N/A
Known failures/limitations:
Dependencies and gate decisions:
Reviewer reproduction steps:
Out-of-scope findings:
```

Правила review:

- Reviewer сверяет diff с `Write scope` и acceptance criteria.
- Для generated files Reviewer проверяет их происхождение и hashes.
- Verification claim проверяется по машинному результату, а не по тексту автора.
- Failure или ограничение окружения не скрывается; Reviewer решает, блокирует ли
  оно acceptance.
- Изменения после review требуют повторной проверки; устаревшее approval должно
  быть сброшено настройкой branch protection.
- Integrator объединяет только принятые PRs и записывает ссылку на gate decision.
- После принятия `P9b Final assembly` Integrator открывает отдельный финальный
  integration PR `read` → `main`; прямой push или workstream PR в `main`
  запрещён.

## 12. Handoff между чатами или аккаунтами

Новый чат не должен восстанавливать состояние по пересказу старого чата. Передача
содержит в GitHub Issue/PR:

```text
current status
branch
head commit
base commit
completed acceptance criteria
remaining work
changed paths
commands and results
artifact/run references
blockers and required decision
```

После handoff новый Owner начинает с чтения Issue, manifests и diff. Это делает
работу воспроизводимой даже при потере или недоступности истории ChatGPT.
