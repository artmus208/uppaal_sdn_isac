# P3 — результаты проверки frozen baseline

Issue #39; PR #49 содержит промежуточный checkpoint, итоговый пакет — PR #50. **Evidence для review; P3 не принят и не закрыт.**
Полная модель Gate 1 не изменялась. Новых задач и исправлений модели нет.

## Главный результат

UPPAAL опроверг `A[] !mac_queue_overflow_seen` на полной композиции.
Контрпример `p3-20260923-003-02-C01-queue`: q проходит 0 → 1 → 2 → 3 → 4 → 5,
K=4; при последнем переходе overflow_seen=1. Пять разрешённых событий нагрузки
выбирают service=0, arrival=1. На этом же пути четыре фактических matching ACK
перехода `WaitPHYAck → Idle`; ACK по принятому контракту не обслуживает очередь.
Таким образом, наблюдаемое переполнение согласуется с разрешённым отсутствием
обслуживания. Оно не означает ошибку исполнения verifier или повреждение XML.

Точная цепочка узлов и переходов: `queue-counterexample.json`; raw symbolic
trace внутри архива 003: `02-C01-queue-trace1.xml`. Это 811 переходов, терминальный
State812. Трасса не объявляется кратчайшей. Из symbolic DBM не подставлены
выдуманные конкретные timestamps. Наличие matching ACK здесь — свидетельство
фактического успешного ACK на одном пути, не доказательство bounded response.

Второй отрицательный результат: безусловное
`mac_obs_ack_active --> !mac_obs_ack_active` опровергнуто (003 query 14).
Трасса заканчивается с active=1, late=0 и разрешённым нулевым циклом observer
буфера Wait ↔ Idle: bufferClass=OVERFLOW, report_sent=true, сбрасывается только
его clock. Это допускает time-stopped/Zeno noncompletion. Разбор и точные
DBM bounds: `ack-completion-counterexample.json`. Этот результат не переносится
на time-divergent bounded-response claim: C02 elapsed safety остаётся timeout.

Итого по 15 уникальным формулам: 4 satisfied (достижимость), 2 violated,
9 inconclusive из-за timeout. Всего 29 query executions в двух completed runs;
23 timeout, 6 explicit verdicts. Никакой универсальный safety query не объявлен
satisfied.

## Все запрошенные формулы

BFS = поиск в ширину, shortest trace; DFS = поиск в глубину, some trace.
Модель, формулы и exact symbolic representation прежние; приближённый/randomized
model checking не использовался. DFS повторяет только 14 BFS timeout-запросов.
`satisfied` означает истинность именно указанной формулы; для E<> это
достижимость, а не универсальная гарантия. `violated` — её отрицательный результат.
`timeout` означает отсутствие вердикта, не false и не true.

| Запрос | BFS, shortest trace | DFS, some trace |
|---|---|---|
| `C01-deadlock` | timeout | timeout |
| `C01-queue` | timeout | violated |
| `C01-attempts` | timeout | timeout |
| `attempt-protocol` | timeout | timeout |
| `C02-ack-elapsed` | timeout | timeout |
| `queue-nonempty` | satisfied | не повторялся |
| `queue-full` | timeout | satisfied |
| `queue-overflow` | timeout | satisfied |
| `attempt-start` | timeout | timeout |
| `attempt-primary` | timeout | timeout |
| `attempt-rollback` | timeout | timeout |
| `attempt-two` | timeout | timeout |
| `ack-start` | timeout | satisfied |
| `ack-timeout` | timeout | timeout |
| `ack-unconditional-completion` | timeout | violated |

Оставшиеся timeout не позволяют заявлять отсутствие deadlock, соблюдение
attempt limits или истинность C02. Наличие контрпримера queue уже исключает
утверждение о выполнении всего C01. Отрицательные результаты не скрыты и не
устранялись изменением query set.

## Evidence и точные входы

- Base/Gate merge: `adea99b05195191eec115621613d4190eba06bf0`.
- Baseline: `reviewer-r1-gate1-20260923`, frozen=true; все 57 file hashes и два
  aggregates проверены перед каждым запуском.
- Model SHA-256: `592678ed678ce8f70cf278f542e48bd2bb739969b53a962423d3e63f91e3e1e2`.
- Frozen selected query set SHA-256:
  `3027dedb1a68d21fce84efc532e3490602eade5306c5dafc9652d38cc4e2eb18`.
- UPPAAL 5.0.0 (rev. 714BA9DB36F49691), June 2023; raw version stdout сохранён
  в каждом архиве. Каждая individual query имеет собственный query_hash/run_id.
- 002 source: `efc7978f398f05f072712b3ca88e3c7cfe2cc87c`.
- 003 source: `a602ec48c2c00842f8461e13db32f7bbf283f0bc`.
- `p3-20260923-002/` и `p3-20260923-003/` содержат run.json, run.yaml,
  results.json и archive.json. run.yaml содержит source/generator hashes,
  полные parameters/vector, command, status, verdict, hardware, времени и память.
  Имена stdout/stderr/trace разрешаются внутри соответствующего архива.
- Raw archives: `evidence/verification/runs/p3-20260923-002.tar.xz` и `003.tar.xz`
  (полное имя второго: `p3-20260923-003.tar.xz`). Архивы проверены побайтово
  относительно исходных raw файлов; archive.json фиксирует SHA-256.

Run 001 остановлен до первого query из-за OEM/UTF-8 mismatch при чтении Windows
hardware metadata. Raw output/failure сохранены отдельно и не считаются
верификацией. Progress archives — промежуточные checkpoint, финальные архивы
002/003 являются полными результатами. Исторические ошибки не удалены.

## Ресурсы и ограничения

Последовательные native Windows процессы на AMD Ryzen 5 1400 (4 cores, 8 logical),
Windows 11 Pro 10.0.26200; native RAM 17106464768 bytes. Управление из WSL.
Лимит каждого запроса — 60 секунд; working-set stop threshold 2147483648 bytes
с polling 50 ms. Это наблюдаемый порог остановки, не hard allocation cap.
Память: Windows PeakWorkingSet64 плюс sampled private bytes; точные значения
по каждому запросу в results.json. Это запуск на рабочей станции с фоновой
активностью, не контролируемый benchmark P4.

Эта сборка не выдала итоговый счётчик explored states: он записан как null.
Прогресс `Load` сохранён в raw stderr и не подменяет итоговое число состояний.
C06/scalability conclusion остаётся зависимым от P4. Завершение orchestration
status=completed не означает status=success всех queries. Независимая приёмка
evidence не выполнена автором запуска.

## Воспроизведение и аудит

Из checkout опубликованной ветки с установленным проектом и PyYAML 6.0.3:

```bash
tar -xJf evidence/verification/runs/p3-20260923-002.tar.xz -C /tmp
tar -xJf evidence/verification/runs/p3-20260923-003.tar.xz -C /tmp
python -B evidence/verification/p3-20260923/audit.py /tmp/p3-20260923-002
python -B evidence/verification/p3-20260923/audit.py /tmp/p3-20260923-003
```

Для нового запуска нужен чистый checkout и новый run_id:

```bash
python -B evidence/verification/p3-20260923/run.py --run-id NEW_ID
python -B evidence/verification/p3-20260923/run.py --run-id ANOTHER_ID --search-order 1 --trace-kind 0 --ids C01-queue
```

Windows пути и окружение запуска указаны в native config/command. `run.py`
использует установленный D:/UPPAAL/app/bin/verifyta.exe через WSL interop;
для другой машины необходимо явно адаптировать runner и записать новый source
commit/run, не менять provenance уже сохранённого результата.

Финальные проверки: оба архива повторно извлечены, SHA-256 архивов и manifest
копии сверены, audits для всех 29 query records прошли. Полный software suite:
180 tests OK; coordination и FastMCP smoke — exit 0. Логи: `checks.txt`.
Это проверка воспроизводимости/evidence и программного окружения, не принятие P3.

Следующий шаг — review этих результатов в существующем #39. Принятие baseline
не отменено автоматически; семантическая правка требует нового принятого baseline.
Никакие незаявленные исправления очереди или новые задачи здесь не выполнялись.
