# P2: временные контракты после аудита V03

Задача [#33](https://github.com/artmus208/uppaal_sdn_isac/issues/33), автор
**artmus208**. Результат — спецификация для независимого review, а не исправленная
модель. V03 остаётся у #15; P1/P2 и Gate 1 этим документом не принимаются.

Выбран контракт recovery «принятый отказ → соответствующий локальный исход»
с общим пределом 30 и этапами 20/10. Admission сохраняет интервал от отправки
APP до соответствующего ответа либо явного APP timeout, предел 15.
Все величины — условные единицы плотного модельного времени; физическая шкала
и универсальная пригодность этих значений не заявляются.

## Входы и воспроизводимость

- Base: `read`, **49b33764b27b343b9354b234e4b4523430201872**.
- Supplement #32/#34: **4bf759fe7b76cf6c57d0d40e89ad238c9a1141e7**.
- Branch: `codex/artmus208/33-v03-contract-disposition`.
- Write scope: только `evidence/instantiation/20260917-v03-contract-disposition/**`.
- Точные hashes и read refs: [inputs.json](inputs.json).
- Точные исходные переходы: [source-anchors.json](source-anchors.json).
  `edge:N` — нулевой индекс в закреплённом XML, не строка Python.

Проверка входов #32 выполнена artmus208, который не является автором #32:
audit.py воспроизвёл 43/14 и hashes; check_audit.py — четыре проверки целостности.
Затем начало/конец recovery, SDN admission и APP admission сверены непосредственно
с XML и адаптацией. Их структурные выводы приняты как входы #33, не как принятие
всего процесса #32 или подтверждение достижимого контрпримера. PR #34 уже merged;
сам merge не используется вместо этой проверки. Более широкое научное review
остаётся отдельным решением.

## Как читать пакет

| Материал | Что решает |
|---|---|
| [contracts.md](contracts.md) | События, часы, все recovery-ветви, admission, равенства, пассивная регистрация |
| [triage.md](triage.md), [coverage.json](coverage.json) | Диспозиция каждой из 43 констант и 14 полей; что остаётся неисправленным |
| [test-plan.md](test-plan.md) | Original/fixed, late, equality, no-completion и rapid-event диагностики |
| [follow-ups.md](follow-ups.md) | Отдельные correction Issues, владельцы, будущий scope и блокеры пересечений |
| [checks.json](checks.json) | Выполненные команды, результаты и ограничения окружения |

## Что должен принять reviewer

1. Recovery endpoints и правило ожидания/отказа, включая прямой rollback.
2. Admission send-to-outcome/timeout и отдельный SDN-local интервал.
3. Общий протокол регистрации; отсутствие completion не заменяется успехом.
4. Диспозиции остальных строк — особенно PHY 5/6, rule 8/5 и APP coalescing.
5. Последовательность correction Issues и снятие scope-блокеров перед кодом.
6. Диагностическую матрицу; реальные машинные результаты потребуются в corrections.

Воспроизведение из корня clone с обоими read refs:

```sh
python3 -B evidence/instantiation/20260917-v03-contract-disposition/check.py
python3 -B scripts/check_coordination.py
```

Проверка сверяет Git bytes/hashes, извлечённые переходы и полное покрытие ключей.
Она не доказывает корректность выбранных контрактов, достижимость, progress или
результат UPPAAL. В этом пакете UPPAAL не запускался. Принятое исправление MAC ACK
#31 сохраняется; его диагностические прогоны не повторялись.
