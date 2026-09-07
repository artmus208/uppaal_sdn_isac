# Цель и задачи G1: Application / Service Layer

Каноническая запись выполнения находится в `goals/application_service_layer_formulated_tasks.md`.

## Цель G1

Сделать Application / Service Layer формальной частью UPPAAL-модели 6G ISAC для обнаружения малоразмерных БПЛА: сервисный уровень задает конечные требования, получает решение SDN/RIC, контролирует SLA и формирует проверяемые реакции без прямого управления PHY/MAC.

Статус: выполнено в `Application_service_layer_formalization.tex`.

## Задачи T1-T8

1. T1: формализовать сервисный запрос.
2. T2: формализовать SLA обнаружения БПЛА.
3. T3: задать жизненный цикл сервиса.
4. T4: задать политики service layer.
5. T5: подготовить UPPAAL global declarations.
6. T6: описать UPPAAL templates.
7. T7: описать observer-автоматы.
8. T8: задать UPPAAL queries.

## Acceptance gates

- В основном TeX-документе есть finite classes, clocks, channels, constants, shared variables, guards, templates, observers и queries.
- Payload каналов заменен shared variables.
- `service_request!` отделен от записи payload: `RequestBuild -> RequestReady -> RequestPending`.
- Safety-critical degraded mode запрещен при critical missed detection и expired freshness.
- Для admission, freshness, update period, false alarm, missed detection и safety-critical violation заданы observer-автоматы.
- Для SLA warning и SLA violation deadlines заданы отдельные observer-автоматы.
- Report/reconfigure/terminate флаги выставляются явными edge-фрагментами `A_SLA`.
- `PdClass` согласован с `MissedDetectionClass` через `detection_kpi_consistent()`.
- `degraded_allowed` принадлежит SDN/RIC; service layer не разрешает деградацию сам.
- Safety-critical degraded mode разрешен только как `DEG_COMM_LIMITED` при выполненном sensing SLA.
- Observer-автоматы запускаются через event counters `*_seq`.
- `REQ_STRICT/REQ_NORMAL/REQ_RELAXED` сопоставлены с наблюдаемыми KPI-классами.
- Следующий шаг: перенос declaration/template/query blocks в существующий `.xml/.xta` UPPAAL-проект.
