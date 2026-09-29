# Результаты ограниченной серии P4 — Issue #76

Статус campaign-002: **completed**. Учтённый бюджет: 4984.387 / 7200 секунд.

Baseline: `uav-family-r1-20260929`; manifest SHA256 `5480bef5b00020735259f10eb43bdd9bc79ebc364a3bbcacad34c78fd0552cbf`.
Source commit запуска: `877fa69a29e1732db2b4047eebdd99591b185c77`.
Хост: Windows 11 build 26200, Ryzen 5 1400; native memory measurements на каждый запуск.

90 запланированных научных ячеек: `{'timeout': 72, 'success': 18}`.

Исходные записи: [campaign-002/runs.json](campaign-002/runs.json). Каждая запись содержит run_id, status, model_hash, query_hash, tool_version, команду, stdout/stderr, память и ссылки на трассы.
[CSV наблюдений](query-observations.csv) сохраняет отдельные повторы. Положительные и отрицательные verdict относятся только к своим точным model/query hashes.

## Время по запросам

Время — end-to-end native verifier, включая компиляцию и запись трассы. Медиана/диапазон приведены только для завершённых наблюдений **вместе** с числом цензурированных. При наличии таймаутов это не оценка безусловного времени. Отсутствие завершённых наблюдений обозначено —, а не нулём.

| Тип сравнения | N | Запрос | Завершено / 3 | Timeout | Memory stop | Не запущено | Медиана завершённых, с | Диапазон, с | Verdict завершённых |
|---|---:|---|---:|---:|---:|---:|---:|---|---|
| fixed-u0 | 1 | u0-queue-full | 3 | 0 | 0 | 0 | 12.467 | 8.970–14.383 | {'satisfied': 3} |
| fixed-u0 | 2 | u0-queue-full | 0 | 3 | 0 | 0 | — | — | {} |
| fixed-u0 | 3 | u0-queue-full | 0 | 3 | 0 | 0 | — | — | {} |
| fixed-u0 | 4 | u0-queue-full | 0 | 3 | 0 | 0 | — | — | {} |
| fixed-u0 | 1 | u0-queue-safety | 3 | 0 | 0 | 0 | 12.739 | 10.458–17.330 | {'violated': 3} |
| fixed-u0 | 2 | u0-queue-safety | 0 | 3 | 0 | 0 | — | — | {} |
| fixed-u0 | 3 | u0-queue-safety | 0 | 3 | 0 | 0 | — | — | {} |
| fixed-u0 | 4 | u0-queue-safety | 0 | 3 | 0 | 0 | — | — | {} |
| growing-global-predicate | 1 | family-queue-safety | 3 | 0 | 0 | 0 | 13.198 | 10.367–14.500 | {'violated': 3} |
| growing-global-predicate | 2 | family-queue-safety | 0 | 3 | 0 | 0 | — | — | {} |
| growing-global-predicate | 3 | family-queue-safety | 0 | 3 | 0 | 0 | — | — | {} |
| growing-global-predicate | 4 | family-queue-safety | 0 | 3 | 0 | 0 | — | — | {} |
| growing-global-predicate | 1 | joint-backlog | 3 | 0 | 0 | 0 | 2.792 | 1.986–3.241 | {'satisfied': 3} |
| growing-global-predicate | 2 | joint-backlog | 3 | 0 | 0 | 0 | 15.335 | 9.249–18.804 | {'satisfied': 3} |
| growing-global-predicate | 3 | joint-backlog | 3 | 0 | 0 | 0 | 43.503 | 27.799–58.968 | {'satisfied': 3} |
| growing-global-predicate | 4 | joint-backlog | 0 | 3 | 0 | 0 | — | — | {} |
| growing-global-predicate | 1 | shared-capacity | 0 | 3 | 0 | 0 | — | — | {} |
| growing-global-predicate | 2 | shared-capacity | 0 | 3 | 0 | 0 | — | — | {} |
| growing-global-predicate | 3 | shared-capacity | 0 | 3 | 0 | 0 | — | — | {} |
| growing-global-predicate | 4 | shared-capacity | 0 | 3 | 0 | 0 | — | — | {} |
| service-coverage | 1 | u0-service | 0 | 3 | 0 | 0 | — | — | {} |
| service-coverage | 2 | u0-service | 0 | 3 | 0 | 0 | — | — | {} |
| service-coverage | 3 | u0-service | 0 | 3 | 0 | 0 | — | — | {} |
| service-coverage | 4 | u0-service | 0 | 3 | 0 | 0 | — | — | {} |
| service-coverage | 2 | u1-service | 0 | 3 | 0 | 0 | — | — | {} |
| service-coverage | 3 | u1-service | 0 | 3 | 0 | 0 | — | — | {} |
| service-coverage | 4 | u1-service | 0 | 3 | 0 | 0 | — | — | {} |
| service-coverage | 3 | u2-service | 0 | 3 | 0 | 0 | — | — | {} |
| service-coverage | 4 | u2-service | 0 | 3 | 0 | 0 | — | — | {} |
| service-coverage | 4 | u3-service | 0 | 3 | 0 | 0 | — | — | {} |

## Наблюдаемая память

Максимум по трём попыткам, включая таймауты. Это наблюдаемый пик target process, а не память, необходимая для завершения запроса. Порог остановки 2048 MiB является выборочным; фактические интервалы измерений и overshoot сохранены в каждом run.

| N | Запрос | Максимум private / reported working set, MiB |
|---:|---|---:|
| 1 | family-queue-safety | 107.73 |
| 1 | joint-backlog | 73.26 |
| 1 | shared-capacity | 231.23 |
| 1 | u0-queue-full | 100.66 |
| 1 | u0-queue-safety | 107.74 |
| 1 | u0-service | 230.85 |
| 2 | family-queue-safety | 147.00 |
| 2 | joint-backlog | 105.99 |
| 2 | shared-capacity | 146.17 |
| 2 | u0-queue-full | 146.89 |
| 2 | u0-queue-safety | 146.54 |
| 2 | u0-service | 146.75 |
| 2 | u1-service | 147.10 |
| 3 | family-queue-safety | 182.93 |
| 3 | joint-backlog | 158.01 |
| 3 | shared-capacity | 182.99 |
| 3 | u0-queue-full | 183.00 |
| 3 | u0-queue-safety | 183.30 |
| 3 | u0-service | 182.95 |
| 3 | u1-service | 183.09 |
| 3 | u2-service | 182.97 |
| 4 | family-queue-safety | 209.57 |
| 4 | joint-backlog | 210.04 |
| 4 | shared-capacity | 210.68 |
| 4 | u0-queue-full | 210.26 |
| 4 | u0-queue-safety | 209.71 |
| 4 | u0-service | 210.54 |
| 4 | u1-service | 209.92 |
| 4 | u2-service | 209.67 |
| 4 | u3-service | 209.45 |

Зафиксированный максимальный интервал между отсчётами памяти — 0.618 с при запрошенных 50 мс; это не жёсткая гарантия частоты. Минимум доступной RAM перед запуском — 5.925 GiB (порог 3 GiB). Максимальный наблюдаемый пик target process — 231.23 MiB. Остановок по памяти не было.


## Подготовительные фазы

| Повтор | N | Фаза | Статус | Полное время, с | Генератор, с |
|---:|---|---|---|---:|---:|
| 1 | [1, 2, 3, 4] | generation | success | 1.333 | 1.003 |
| 2 | [1, 2, 3, 4] | generation | success | 1.699 | 1.268 |
| 3 | [1, 2, 3, 4] | generation | success | 1.644 | 1.208 |
| 1 | 1 | compile | success | 1.113 | — |
| 1 | 2 | compile | success | 1.814 | — |
| 1 | 3 | compile | success | 2.760 | — |
| 1 | 4 | compile | success | 3.764 | — |
| 2 | 1 | compile | success | 1.431 | — |
| 2 | 2 | compile | success | 2.934 | — |
| 2 | 3 | compile | success | 3.992 | — |
| 2 | 4 | compile | success | 4.650 | — |
| 3 | 1 | compile | success | 1.224 | — |
| 3 | 2 | compile | success | 3.446 | — |
| 3 | 3 | compile | success | 7.595 | — |
| 3 | 4 | compile | success | 5.379 | — |
| 1 | 1 | load-and-parse | success | 0.754 | — |
| 1 | 2 | load-and-parse | success | 1.417 | — |
| 1 | 3 | load-and-parse | success | 2.214 | — |
| 1 | 4 | load-and-parse | success | 3.187 | — |
| 2 | 1 | load-and-parse | success | 1.156 | — |
| 2 | 2 | load-and-parse | success | 1.883 | — |
| 2 | 3 | load-and-parse | success | 3.130 | — |
| 2 | 4 | load-and-parse | success | 4.091 | — |
| 3 | 1 | load-and-parse | success | 0.904 | — |
| 3 | 2 | load-and-parse | success | 3.790 | — |
| 3 | 3 | load-and-parse | success | 3.806 | — |
| 3 | 4 | load-and-parse | success | 3.881 | — |

Время генератора включает запуск Python и запись файлов; полное время фазы также включает восстановление pinned snapshot и сравнение. Подробные составляющие сохранены в SUMMARY.json. Compile/load измеряют отдельные свежие процессы.

## Service coverage workload

Каждая строка объединяет N отдельных service-запросов одного повтора. Сумма и максимум — фактически наблюдавшееся время, включая цензурированные попытки; это не время решения всей задачи, если хотя бы один запрос не завершён.

| Повтор | N | Завершено / N | Timeout | Не запущено | Наблюдаемая сумма, с | Наблюдаемый максимум, с |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 1 | 0 / 1 | 1 | 0 | 62.119 | 62.119 |
| 1 | 2 | 0 / 2 | 2 | 0 | 124.213 | 62.110 |
| 1 | 3 | 0 / 3 | 3 | 0 | 186.229 | 62.095 |
| 1 | 4 | 0 / 4 | 4 | 0 | 248.372 | 62.111 |
| 2 | 1 | 0 / 1 | 1 | 0 | 62.141 | 62.141 |
| 2 | 2 | 0 / 2 | 2 | 0 | 124.236 | 62.150 |
| 2 | 3 | 0 / 3 | 3 | 0 | 186.414 | 62.249 |
| 2 | 4 | 0 / 4 | 4 | 0 | 248.396 | 62.110 |
| 3 | 1 | 0 / 1 | 1 | 0 | 62.074 | 62.074 |
| 3 | 2 | 0 / 2 | 2 | 0 | 124.282 | 62.169 |
| 3 | 3 | 0 / 3 | 3 | 0 | 186.361 | 62.137 |
| 3 | 4 | 0 / 4 | 4 | 0 | 248.312 | 62.084 |

## Интерпретация и ограничения

Лимит поиска — 60 с; наблюдаемые таймауты около 62 с включают остановку и ожидание завершения процесса. Консервативный общий бюджет дополнительно включает запуск/завершение monitor. Генерация, prelaunch probes и Git checkpoints в verifier budget не входят. Случайный порядок запусков и контроль фоновой нагрузки не применялись; различия времени сами по себе не доказывают закон роста сложности.

Fixed-u0 запросы сравниваются отдельно от глобальных предикатов, растущих с N. N запросов uI-service — отдельная coverage-нагрузка, а не один запрос. Не предполагается симметрия UAV из-за фиксированного порядка уведомлений.

Таймаут/порог памяти означает отсутствие verdict и наблюдаемую границу выбранного бюджета; он не доказывает недостижимость, безопасность или универсальную границу масштабируемости. Все 30 service-попыток этой серии завершились таймаутом; достижимость обслуживания остаётся открытой. Даже отдельный положительный service verdict не установил бы fairness, SLA или полезное обслуживание после absorbing overflow.

Серия относится к затратам verifier на конкретных полных моделях. Физическая калибровка, работоспособность сети и перенос старых P3 результатов не заявляются. Старые запуски на другом хосте не включаются в повторы. Сопоставление с работой Глониной и полная приёмка R03/R04/C06 остаются вне этого ограниченного отчёта.

## Сохранённая остановка подготовки

campaign-001 остановлен на генерации из-за operational context hash drift до любых научных/compile/load запусков. Ошибка runner исправлена генерацией из pinned Git snapshot. Пользователь отдельно разрешил campaign-002; исходная попытка сохранена. Её 0.1355066079995595 с metadata включены в общий бюджет. Все 70 файлов генерации проверены побайтно, исторические inputs не изменялись.

Generation subprocess timing, snapshot preparation and copy/compare записаны отдельно в stdout каждой generation-ячейки. Compile-only и load — отдельные подготовительные фазы и не доказывают свойства.
