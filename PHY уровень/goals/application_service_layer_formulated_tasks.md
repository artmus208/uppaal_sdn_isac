# Выполнение G1: Application / Service Layer

## Цель G1

Сделать Application / Service Layer формальной частью UPPAAL-модели 6G ISAC для обнаружения малоразмерных БПЛА: сервисный уровень задает конечные требования, получает решение SDN/RIC, контролирует SLA и формирует проверяемые реакции без прямого управления PHY/MAC.

Статус G1: выполнено в `Application_service_layer_formalization.tex`.

## Задачи T1-T8, критерии приемки и evidence

| ID | Задача | Критерий приемки | Статус и evidence |
|---|---|---|---|
| T1 | Формализовать сервисный запрос. | Есть конечные классы `ServiceClass`, `CriticalityClass`, `DemandClass`, bounds для latency/reliability/sensing freshness/update/Pd/Pfa/Pmiss/accuracy/coverage; payload канала заменен shared variables. | Выполнено. Evidence: `Application_service_layer_formalization.tex`, строки 97-121, 293-330, 415-426, 690-695. |
| T2 | Формализовать SLA обнаружения БПЛА. | Есть `SLA_UAV`, `DetectionFreshnessClass`, `UpdatePeriodClass`, `FalseAlarmClass`, `MissedDetectionClass`, `AccuracyClass`, `CoverageClass`; заданы `SLA_OK`, `SLA_WARN`, `SLA_VIOLATED`. | Выполнено. Evidence: строки 161-225, 350-378. |
| T3 | Задать жизненный цикл сервиса. | Есть состояния `ServiceIdle`, `RequestBuild`, `RequestReady`, `RequestPending`, `Accepted`, `AcceptedDegraded`, `Rejected`, `Completed` и переходы приема/деградации/отказа/завершения. | Выполнено. Evidence: строки 125-140, 435-438, 444-477, 653-670. |
| T4 | Задать политики service layer. | Есть guards для admission, degraded accept/reject, SLA warning/violation, safety-critical reaction; degraded service запрещен при safety-critical missed detection или expired freshness. | Выполнено. Evidence: строки 142-158, 214-225, 380-426. |
| T5 | Подготовить UPPAAL global declarations. | Есть `clock`, `broadcast chan`, bounded typedefs, constants `D_req`, `D_admission`, `D_sla_warn`, `D_sla_violation`, `D_safety`, shared variables вместо payload. | Выполнено. Evidence: строки 232-330. |
| T6 | Описать UPPAAL templates. | Есть `A_REQ`, `A_SLA`, `A_CRIT`, `A_SVC_AGG` с locations, invariants и edge-фрагментами. | Выполнено. Evidence: строки 429-485. |
| T7 | Описать observer-автоматы. | Есть observers для admission deadline, freshness expiration, update period violation, false alarm critical, missed detection critical, safety-critical SLA violation. | Выполнено. Evidence: строки 487-562. |
| T8 | Задать UPPAAL queries. | Есть `A[] not deadlock`, запреты observer violation states, запрет degraded acceptance при safety-critical missed detection, TCTL-спецификации timely reports. | Выполнено. Evidence: строки 565-574, 713-751. |

## Фактически внесенные изменения

- В `Application_service_layer_formalization.tex` добавлен `RequirementClass_t` и shared variables: `latencyBoundClass`, `reliabilityClass`, `sensingUpdateBoundClass`, `sensingFreshnessBoundClass`, `pdMinClass`, `pfaMaxClass`, `pmissMaxClass`.
- Добавлен `build_uav_service_request()`, который перед `service_request!` заполняет сервисный запрос БПЛА через shared variables, а не через payload канала.
- Переход сервисного запроса разделен на `RequestBuild -> RequestReady -> RequestPending`: сначала записываются shared variables, затем выполняется `service_request!`.
- Добавлен observer `ObsSafetyCriticalViolation()` с clock `x` и deadline `D_safety`.
- Добавлен observer `ObsUpdatePeriodViolation()` с clock `x` и deadline `D_update_report`.
- В список UPPAAL queries добавлены `A[] not ObsUpdatePeriodViolation.Violation` и `A[] not ObsSafetyCriticalViolation.Violation`.
- Добавлены `PdClass`, `detection_kpi_consistent()` и query `A[] detection_kpi_consistent()` для согласования дискретных классов \(P_D\) и missed detection.
- Добавлены `ObsSlaWarningDeadline()` и `ObsSlaViolationDeadline()`.
- Добавлены edge-фрагменты `A_SLA`, которые реально выставляют `sla_warning_report_sent`, `sla_violation_report_sent`, `service_reconfigure_sent`, `service_terminate_sent`.
- Исправлено направление `service_reconfigure`: сервис формирует `service_reconfigure!`, а не принимает `service_reconfigure?`.
- `A_SVC_AGG` больше не дублирует `service_request!`; отправителем остается `A_REQ`.
- `degraded_allowed` больше не выставляется сервисом; владельцем записи является SDN/RIC.
- Добавлен `gSafetyAllowsDegraded()`: safety-critical degraded допускается только при `SLA^{sens}_{OK}` и причине `DEG_COMM_LIMITED`.
- Добавлены mapping-функции `pd_req_satisfied()`, `pfa_req_satisfied()`, `pmiss_req_satisfied()`, `freshness_req_satisfied()`, `update_req_satisfied()`, `quality_req_satisfied()`.
- Observer-автоматы переведены на event counters `*_seq`, чтобы deadline запускался от события, а не от произвольного чтения shared variable.
- Core admission/report/reconfigure channels переведены в handshake `chan`; monitoring/KPI events оставлены `broadcast chan`.

## Инварианты проекта

- Service layer не управляет PHY/MAC напрямую.
- Каналы UPPAAL не передают payload; перед синхронизацией отправитель обновляет shared variables.
- `Pd`, `Pfa`, `Pmiss`, accuracy и coverage не вычисляются timed automata, а поступают как конечные классы от нижних уровней или estimator-слоя.
- `AcceptedDegraded` запрещен для safety-critical missed detection и expired detection freshness.
- Модель не использует ИИ/ML; это аппроксимированные контрактные timed automata.

## Acceptance gates

- G1 покрыта задачами T1-T8.
- Каждая задача имеет критерий приемки и evidence в текущем `.tex`.
- Все payload-зависимые интерфейсы сведены к shared variables.
- Для критических событий есть observer-автоматы с clock/deadline.
- Safety-critical degraded mode ограничен через guards и queries.
- SLA report/reconfigure/terminate флаги выставляются в явных edge-фрагментах `A_SLA`.
- Конфликтные KPI-классы `PdClass` и `MissedDetectionClass` запрещены контрактным consistency guard.
- Request-to-KPI mapping задан через `REQ_STRICT/REQ_NORMAL/REQ_RELAXED`.
- Safety-critical degraded mode не может маскировать sensing-деградацию.
- В `.tex` нет отдельного нового UPPAAL-файла; документ описывает перенос в существующую модель.

## Следующий практический шаг для `.xml/.xta` UPPAAL

Перенести из `Application_service_layer_formalization.tex` блоки `global declarations`, `templates` и `queries` в существующий UPPAAL-проект. При переносе проверить коллизии имен `OK`, `LIMITED`, `FAILED`, `D_*`, каналов и shared variables с уже существующими PHY/MAC/SDN объявлениями. Если текущая версия UPPAAL требует явные `enum`, заменить демонстрационные `typedef int[...]` на `typedef enum`.
