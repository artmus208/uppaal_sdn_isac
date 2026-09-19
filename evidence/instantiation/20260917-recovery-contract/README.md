# Recovery 20/10: реализация #35, готова к независимому review

Автор продолжения: **vadimnbkg** (фактический GitHub account). Исходная
незавершённая заготовка — artmus208, передана пользователем в
[interrupted-author-context.md](interrupted-author-context.md). Её точные исходные
байты сохранены в `interrupted-author-context.md.gz`; читаемая копия нормализует
только переносы строк и хвостовые пробелы. Источник — пользовательский документ,
не восстановленный Git commit предыдущего автора.

Issue #35; process P2; atomic ID V03 — supporting input, основное решение в #15.
Base `44ff0e336c7bfc88e3ebe3da3d05699c2acef62f` (`read`, merged #37).
Ветка `codex/vadimnbkg/35-recovery-contract`. Передача продолжения и исключительного
права записи зарегистрирована в #19/#30/#35. Историческое назначение artmus208 в
спецификации не означает параллельного разрешения записи.

Принятая спецификация: [#33/#37](https://github.com/artmus208/uppaal_sdn_isac/pull/37#pullrequestreview-5245428835),
[contracts.md](../20260917-v03-contract-disposition/contracts.md),
[test-plan.md](../20260917-v03-contract-disposition/test-plan.md).
Её сроки и endpoints не пересматриваются.

## Изменение

Production diff затрагивает только `src/uppaal_mcp/integrated/adapt.py`:

- В `FailureDetected` введён предел `sdn_c_rec<=20`. Часы по-прежнему запускаются
  при фактическом приёме link/node failure A_REC, включая ожидание dispatch.
- В `FailureDetected`, `StandbySwitch`, `ReactiveReembedding` на 20 доступен
  локальный отказ без синхронизации; отправка rollback и своевременный ACK также
  разрешены, без приоритета одного исхода над другим.
- Rollback сохраняет локальный бюджет 10 от фактической отправки. Его отказ
  регистрируется локально; доставка `failure_report` вынесена в отдельный
  переход после исхода. `sdn_recovery_failure_kind` различает отказ на этапе
  dispatch/recovery (1) и rollback timeout (2); report_pending/sent не подменяют исход.
- Начало и конец наблюдения регистрирует A_REC на своих переходах. Late — sticky,
  новый эпизод не стирает просрочку. Duplicate start сохраняет старый age и
  выставляет отдельный protocol_error. Наблюдатель ничего не сбрасывает и не пишет.

Функциональная политика и регистрация реализованы отдельными функциями
`recovery_policy` и `record_recovery`. Вторую можно применить к исходному core:
это отдельный диагностический вариант recorder-only. Исчерпывающее разбиение
каждого binary/local end guard на `age<=30` и `age>30` сохраняет исходные choices,
updates и timing при стирании monitoring state. Никаких новых core invariants
от recorder, observer synchronizations или committed states нет. Пять программных
регрессий проверяют это структурно, а также неизменность остальных templates,
включая принятое исправление MAC ACK. Старые ACK verifier runs не повторялись.

Прямой bad-предикат: `sdn_obs_rec_late || (sdn_obs_rec_active && sdn_c_obs_rec>30)`;
protocol_error проверяется отдельно. `Violation` — достижимый свидетель bad/error,
а не обязательный синхронный snapshot. Никаких выводов об обязательном завершении
на бесконечных zero-time traces не делается.

## Машинные результаты

Проверенный **опубликованный clean source commit**:
`eed0b91c7eb56c4416e742d6d01c92cc492bc7ef`.
Run: **`recovery-35-20260919-003`**, runner exit **0**.
UPPAAL **5.0.0 (rev. 714BA9DB36F49691)**; полный фактический version output,
Windows/WSL environment, CPU/RAM и лимиты сохранены в [run.json](run.json).

- 22 целевые композиции, **123 per-query результата** совпали с ожиданиями,
  включая ожидаемые отрицательные ответы.
- Отдельный `E<> true` на полном сгенерированном XML завершился успешно. Это
  проверка загрузки/работы движка, не recovery/ACK-свойство полной модели.
- **168 software tests**, без failures/errors/skips; 37.099 s.
- Coordination, MCP construction, list-examples, pip check и diff check: exit 0.

[results-index.json](results-index.json) содержит каждый `run_id`, `status`,
`model_hash`, `query_hash`, `tool_version`, query, ожидание и фактический ответ.
[review-matrix.md](review-matrix.md) связывает случаи и hashes.
Все commands/stdout/stderr/traces/inputs находятся в
[runs/recovery-35-20260919-003.tar.xz](runs/recovery-35-20260919-003.tar.xz),
его hash — в [artifacts.json](artifacts.json). Сжатие без потерь; восстановление
и SHA256 всех сохранённых файлов проверены побайтно.

Полный XML SHA256: `6932cc7ed619eaac098f5b89ea5bf5966835b7ccce421ef5220029c9015ac888`.
Query set SHA256: `af9bbd8e73b1bc73eb7e957a89b826d24e04f1c2f1eed2f1b1e5bb4a55cd25b9`.
Generator SHA256: `d8b0b3178b886ad9ccac94de92848787ca09d30955961f01b43627fde234b692`.

## Сценарии и ограничения

Сохранены actual A_REC и ObsRecovery, остальные процессы заменены явно описанным
`RecoveryPeer`. Он задаёт точное время initial dispatch и typed ACK; отправка
link/node failure выбирается недетерминированно. Это отдельные harnesses, не
утверждение о достижимости тех же путей в полной композиции.

Проверены standby/reembedding с dispatch 0/19/20, прямой rollback 0/5/19/20,
ACK на 20 и rollback ACK/timeout на b=10, общий возраст до 30, недоступность
initial dispatch и rollback receiver, отсутствие report receiver, раздельная
доставка отчёта, delayed observer, повторные нулевые эпизоды и sticky late.
Исходный core с искусственно задержанным transport допускает dispatch после 30;
recorder-only сохраняет этот функциональный путь и обнаруживает просрочку.

No-completion mutant удаляет исходы и ограничивающие время инварианты, чтобы
проверить bad до любого end. Time-stopped peer, напротив, допускает бесконечный
нулевой self-loop: elapsed safety выполняется при отсутствии завершения.
Это явное свидетельство различия safety и completion, не обход контракта.

Typed ACK другого вида не синхронизируется с recovery-фазой. После завершения
одиночного production episode у старого ACK нет принимающего перехода A_REC.
Production envelope сохраняет один fault и один outstanding slot. Два эпизода
в rapid/late harness — синтетическое расширение с упорядоченным peer. Защита
от произвольного старого ACK того же типа при повторном использовании слота
в неограниченной многозапросной среде не заявляется; для такого расширения
нужен отдельный finite drain/generation контракт, как требует #33.

## Воспроизведение

Рабочее дерево перед новым прогоном должно быть clean. Используется отдельный
venv; Python окружение не обязано совпадать с Windows-окружением verifyta.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e .
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python evidence/instantiation/20260917-recovery-contract/check.py \
  --run-id recovery-35-independent-NEW \
  --verifyta /mnt/d/UPPAAL/app/bin/verifyta.exe
```

Каждый run-id уникален; существующие результаты не перезаписываются.
Для точного повторения recorded run checkout source commit, приведённый выше.
Для чтения исходных результатов без нового model checking:

```bash
python3 -B evidence/instantiation/20260917-recovery-contract/restore-run.py \
  evidence/instantiation/20260917-recovery-contract/runs/recovery-35-20260919-003.tar.xz \
  /tmp/recovery-review-NEW
python3 -B evidence/instantiation/20260917-recovery-contract/unpack.py \
  /tmp/recovery-review-NEW/recovery-35-20260919-003
```

Первый скрипт восстанавливает **точные сохранённые байты и проверяет все hashes**;
второй распаковывает XML/log/trace в исходные имена. Commands содержат фактические
абсолютные Windows/WSL paths запуска; при повторении заменить только пути своим
расположением восстановленных файлов. SHA256 verifier inputs относится к
несжатым XML/query bytes. Software checks не подменяют UPPAAL.

## Неудачные прогоны и передача

`archived-runs/` сохраняет 001 и 002 (runner exit 1) и их исходные журналы:
001 — ошибки peer scheduling/terminal quiescence и clock-disjunction guards;
002 — peer invariant ошибочно останавливал время no-completion mutant.
Дополнительно diff check выявил CRLF/trailing whitespace в неизменённых raw
Windows logs и пользовательском документе. Исходные байты сохранены в архивах,
а читаемая копия документа нормализована. Production исправление между этими
прогонами и успешным 003 не менялось. Оба software suite завершились успешно.
Для извлечения старых run archives применяются те же restore-run.py/unpack.py.

В этом WSL отсутствовал ensurepip; созданный venv был дополнен официальным
bootstrap.pypa.io/get-pip.py, затем выполнена обычная editable installation.
Git HTTPS push не имел credentials; публикация через GitHub connector, каждый
blob/tree сверяется с локальным Git. Полная локальная история, включая source
commits неудачных запусков, сохранена в bundles под
`D:/uppaal_mcp_handoffs/issue35-20260919/`. Публичный source для успешного 003
доступен непосредственно по commit SHA; независимость от временного checkout
не требует восстановления старых авторских сессий.

Приёмка требуется от reviewer, не являющегося автором artmus208/vadimnbkg.
#36 остаётся заблокирован до отдельного принятия/merge #35 и нового base/scope.
Полный triage #33, V03/#15, P1/P2 и Gate 1 **не принимаются** этим handoff.
Две коррекции сами по себе не объявляются достаточными для Gate 1: остаточные
PHY/MAC/SDN/APP замечания должны получить отдельное решение P1/P2/координатора
до freeze. Полные свойства и масштабируемость остаются работой P3/P4 после Gate 1.

## CI checkout correction

Первый GitHub Actions run [35432770322](https://github.com/artmus208/uppaal_sdn_isac/actions/runs/35432770322) завершился ошибкой setup новых тестов: shallow checkout не содержал Git object базового commit. Тест теперь читает уже сохранённый исторический XML и проверяет закреплённый SHA256 перед сравнением. Production-код, harnesses и bytes всех проверенных моделей не изменены; UPPAAL не повторялся. Локальные пять recovery regressions повторно прошли. Полный CI повторяется для обновлённого HEAD.
