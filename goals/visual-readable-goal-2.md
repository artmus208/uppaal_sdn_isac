# Visual Readable Goal 2

## Цель

Сделать generated UPPAAL-модели комфортно читаемыми в UPPAAL GUI: схемы временных автоматов должны открываться без ручной раскладки, а состояния, названия автоматов, invariants, guards, synchronisation labels, assignments и comments должны быть визуально разнесены и однозначно относиться к своим переходам или локациям.

## Найденные проблемы по `uppaal_screens`

- Labels переходов накладываются друг на друга, особенно в плотных автоматах `A_SCH`, `A_Q`, `A_BUF`, `A_SIG`, `A_BM`, `A_SQ`, `A_PH`.
- Длинные guards и assignments не переносятся достаточно хорошо и перекрывают соседние ребра, состояния и подписи.
- Self-loops в ENV-автоматах и рабочих шаблонах схлопываются вокруг одной точки.
- Parallel edges между одними и теми же состояниями идут почти по одной траектории и образуют неразборчивые пучки.
- MAC/SDN layout validation допускает плотные или повторно использованные координаты label как warnings, хотя визуально такие схемы уже неудобочитаемы.

## Задачи

- Обобщить layout engine для PHY/MAC/SDN: единые `Point`, `TransitionGeometry`, lanes, label offsets, bend-points/nails и wrapping длинных текстов.
- Перевести MAC и SDN с простых `label_point`/`nails_for` на PHY-подобный `transition_geometry`.
- Разнести semantic zones внутри шаблонов: nominal/base states слева, обработка и ожидание в центре, degradation/failure/violation справа или по отдельным верхним/нижним веткам.
- Улучшить layout для self-loops и parallel edges: каждый повторный переход должен получать отдельную lane, отдельные nails и отдельные координаты labels.
- Улучшить wrapping labels: переносить длинные guards, assignments и comments по читаемым границам, сохраняя валидный UPPAAL XML.
- Разнести invariants и names относительно локаций так, чтобы они не попадали на ребра и labels переходов.
- Усилить `layout_validation` для `readable`: dense/reused label coordinates должны становиться ошибкой, а не только warning, кроме явно разрешенных compact/env случаев.
- Обновить `model_map.md`, `template_map.md` и связанные layout artifacts, чтобы они описывали semantic zones и смысл переходов.
- Обновить golden fixtures и тесты для PHY/MAC/SDN после изменения координат.

## Критерии приемки

- `phy-generate`, `mac-generate` и `sdn-generate` с `--layout readable` выдают `layout_validation.ok == true` без density warnings.
- Схемы PHY/MAC/SDN читаются в UPPAAL GUI без ручного перемещения элементов.
- Labels одного перехода не имеют одинаковых координат и визуально разделены по типам: guard, synchronisation, assignment, comments.
- Self-loops имеют bend-points/nails и не лежат поверх location.
- Parallel edges между одинаковыми состояниями имеют разные lanes и не образуют один неразборчивый пучок.
- ENV self-loops не схлопываются вокруг одной точки.
- Violation/failure states находятся правее nominal/base states, если это не нарушает явно заданную семантическую зону.
- Golden fixtures обновлены осознанно, тесты проходят.
- Семантика модели не меняется: изменения касаются координат, wrapping labels, comments и layout artifacts, а не логики timed automata.

## Проверки после реализации

- `Get-Content -Raw goals\visual-readable-goal-2.md` читается корректно.
- Файл сохранен в UTF-8.
- `git diff -- goals/visual-readable-goal-2.md` показывает только новый goal-документ.
- Текущий test suite проходит после последующей реализации layout-задач.

## Допущения

- Старый `goals/visual-readable-goal.md` не изменяется.
- Этот документ фиксирует цель и задачи; непосредственные изменения layout-кода выполняются отдельным этапом.
