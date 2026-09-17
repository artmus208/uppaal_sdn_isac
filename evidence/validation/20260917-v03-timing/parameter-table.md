# Полный указатель временных параметров

Сгенерировано audit.py из закреплённого XML; это статический разбор, не verification.

| Параметр | Значение | Использование | Интервал / роль | Ограничение |
|---|---:|---|---|---|
| phy.D_meas | 5 | core_or_boundary | measure_tick → channel_report; c_meas=0 при приёме и результате | Отчёт разрешён до 5, инвариант MeasurePending допускает 6; после 5 результат закрыт guard. Нет доказательства прогресса. |
| phy.D_sig | 5 | core_or_boundary | waveform_config → signal_report; c_sig=0 при каждой конфигурации | Повторная конфигурация сбрасывает текущий срок; не per-command oldest-outstanding контракт. |
| phy.D_sense | 5 | core_or_boundary | Приём child report в Idle → sensing_report; c_sense=0 при входе | ObsFreshness измеряет иной интервал: aos_ctrl_expired → sensing_report с FRESHNESSLIMITED. Не суммировать как одинаковые этапы. |
| phy.D_report | 5 | core_or_boundary | Приём child report → phy_kpi_report; каждый принятый child report, включая self-loop в PHYKpiReporting, сбрасывает c_report | Повторные child reports перезапускают срок; это latest-trigger, не oldest-outstanding. ObsSenseReport стартует sensing_degraded, endpoints отличаются. |
| phy.D_BM | 5 | core_or_boundary | Вход recovery_cmd либо misalignment/extra_ssb → beam_restored/handover_hint/beam_failure; c_rec | ObsBeamRecovery стартует recovery_start, который не совпадает со всеми сбросами core. Recovery_cmd не имеет отправителя в выбранном составе; другие входы проверять отдельно. |
| phy.D_child | 5 | declaration_only | Не используется вне объявления в выбранном XML/queries | Не обосновывает доставку/период/SSB в этой конфигурации. См. bus_D_bus и bus_T_input. |
| phy.D_net | 5 | declaration_only | Не используется вне объявления в выбранном XML/queries | Не обосновывает доставку/период/SSB в этой конфигурации. См. bus_D_bus и bus_T_input. |
| phy.T_meas | 5 | core_or_boundary | Верхняя граница нахождения MeasurePending: c_meas <= T_meas + J_meas = 6 | Это не период измерений. Внешние попытки задаёт T_input=5. |
| phy.J_meas | 1 | core_or_boundary | Добавка +1 к верхней границе MeasurePending | Односторонний запас, не симметричный jitter и не нижняя граница периода. |
| phy.T_report | 5 | declaration_only | Не используется вне объявления в выбранном XML/queries | Не обосновывает доставку/период/SSB в этой конфигурации. См. bus_D_bus и bus_T_input. |
| phy.J_SSB | 1 | declaration_only | Не используется вне объявления в выбранном XML/queries | Не обосновывает доставку/период/SSB в этой конфигурации. См. bus_D_bus и bus_T_input. |
| phy.tau_SSB | 4 | declaration_only | Не используется вне объявления в выбранном XML/queries | Не обосновывает доставку/период/SSB в этой конфигурации. См. bus_D_bus и bus_T_input. |
| mac.D_collect | 2 | core_or_boundary | mac_tick → PHY report либо fallback; c_sched=0 на tick | На report c_sched сбрасывается заново; сбор и SelectMode — отдельные интервалы. Missing/stale разрешает ранний fallback. |
| mac.D_sched | 5 | core_or_boundary | Вход SelectMode после KPI → ApplySchedule/отказ; новый c_sched | 2+5 ограничивает только последовательные стадии до ApplySchedule. В ApplySchedule нет инварианта; 2+5+3 не end-to-end срок от tick. ObsSensingCritical имеет иной flag-trigger. |
| mac.D_phy_ack | 3 | core_or_boundary | Отправка MAC мосту → соответствующий ACK либо ScheduleFailure; оба часа=0 на отправке | Принятое исправление #30/#31: граница <=3, sticky late, последовательные транзакции; полное ACK-свойство не проверено. |
| mac.D_queue_crit | 10 | core_or_boundary | Вход QueueCritical → QueueDraining или resource_reject; c_queue=0 | Начало по обнаружению queueClass, не по физическому приходу пакета; ресурсный отказ на =10. Flag-polling observer требует отдельного соответствия. |
| mac.D_buf_report | 4 | core_or_boundary | Вход BufferOverflow → mac_report либо уход при устранении overflow; c_buf=0 | Инвариант/отчёт =4; нет численной ёмкости очереди. Flag-polling observer не принят как per-event доказательство. |
| mac.D_mac_report | 5 | core_or_boundary | ReportIdle → ReportBuild сбрасывает c_report; публикация до 5 либо ReportStale на =5 | ReportStale не имеет инварианта: это не гарантированный срок публикации от установки pending. |
| mac.D_phy_report | 10 | declaration_only | Не используется вне объявления | Фактический source-age задаётся B_KPI, не этой константой. |
| sdn.D_mon | 5 | core_or_boundary | Приём MAC/PHY report в MonitorIdle → классификация telemetry; c_mon=0 при приёме | CollectReports <=5; missing/stale может разрешаться раньше. Это ожидание/классификация после report, не период мониторинга. |
| sdn.D_decision | 5 | core_or_boundary | Приём service request/MAC report/PHY report в PolicyIdle → outcome; c_dec=0 | Evaluate <=5. Нормальная принятая транзакция admission имеет транспорт+evaluation+транспорт <=7; существующий ObsSensingDecision измеряет flag-trigger. |
| sdn.D_rule_install | 8 | core_or_boundary | rule_miss → установка/forward/timeout; c_rule=0 при miss | RuleMiss и RuleInstalled без инвариантов; timeout на =8 может быть пропущен при задержке. Число 8 не доказывает обязательного разрешения. |
| sdn.D_rule_ack | 5 | core_or_boundary | Тот же c_rule от rule_miss → ACK в RuleInstalled | ACK <=5, install <=8: общий начальный момент, не сумма 8+5. D_bus=1 отсчитывается от flow_mod, не от rule_miss. |
| sdn.D_ctrl_ack | 5 | core_or_boundary | Отправка bus_ctrl_request из CommandBuild → ACK/timeout; c_ctrl_ack=0 на отправке | CommandSent без инварианта перед AwaitAck<=5; observer стартует по command_pending раньше или позже отправки. Нужен разбор задержки входа в AwaitAck и исходов. |
| sdn.D_recovery | 20 | core_or_boundary | link/node_failure сбрасывает c_rec → standby/reembedding исход или rollback на =20 | FailureDetected без инварианта; прямой rollback может начинаться позже. ObsRecovery отдельно опрашивает flags. Полный срок 30 не обоснован. |
| sdn.D_rollback | 10 | core_or_boundary | Отправка rollback_cmd сбрасывает c_rollback → ACK или RecoveryFailed на =10 | Сумма 20+10 применима к ветке перехода на rollback при c_rec=20; не ограничивает произвольное ожидание перед прямым rollback. |
| sdn.D_admission | 15 | observer_only | Только ObsAdmission: обнаружение pending → обнаружение serviceImpact; c_obs_admission | Core admission использует D_decision=5. Observer принимает NONE/DEGRADED/REJECTED без завершения pending; начальное NONE уже удовлетворяет response guard. Четвёртое значение FAILED исключено. |
| sdn.D_sec_ack | 10 | declaration_only | Не используется: A_SEC исключён из instance vector | Не распространять bound на выключенное расширение. |
| app.D_req | 3 | core_or_boundary | new_demand → RequestReady через RequestBuild; c_req=0 на demand и при подготовке | RequestReady без инварианта. Это срок подготовки, не отправки и не всей admission. |
| app.D_admission | 15 | core_or_boundary | service_request → accept/degraded/reject либо явный timeout; c_admission=0 на отправке | Timeout в RequestPending на =15. B_ADMISSION total стартует на той же отправке; APP observer имеет producer-age, но завершение опрашивается позднее. |
| app.D_event | 5 | declaration_only | Не используется вне объявления в выбранном XML/queries | Декларация не реализует числовой SLA; часть решений использует классы и literal source-age 5/10. |
| app.D_update | 3 | declaration_only | Не используется вне объявления в выбранном XML/queries | Декларация не реализует числовой SLA; часть решений использует классы и literal source-age 5/10. |
| app.D_fresh | 10 | declaration_only | Не используется вне объявления в выбранном XML/queries | Декларация не реализует числовой SLA; часть решений использует классы и literal source-age 5/10. |
| app.D_sla_warn | 5 | core_or_boundary | Полученное sla_warn → warning report либо переход в violation; core c_sla_warn и oldest-event age | SLAWarning <=5; observer использует coalescing latch, завершение определяется flags. Новые события не сбрасывают pending age. |
| app.D_sla_violation | 3 | core_or_boundary | Полученное sla_violation → report/reconfigure/terminate; core c_sla_violation и oldest-event age | SLAViolated <=3; report-consumption не означает выполнение reconfiguration. Flags не привязаны к отдельной повторной транзакции. |
| app.D_safety | 2 | observer_only | Первое pending событие safety_violation → report/reconfigure/terminate/rejection; producer-owned *_seq_age | Срок только observer; повторения coalesce без сброса oldest age. Позднее polling завершения/старые flags требуют соответствия выбранному контракту. |
| app.D_fresh_report | 3 | observer_only | Первое pending событие freshness_expired → report/reconfigure/terminate; producer-owned *_seq_age | Срок только observer; повторения coalesce без сброса oldest age. Позднее polling завершения/старые flags требуют соответствия выбранному контракту. |
| app.D_update_report | 3 | observer_only | Первое pending событие update_violation → report/reconfigure/terminate; producer-owned *_seq_age | Срок только observer; повторения coalesce без сброса oldest age. Позднее polling завершения/старые flags требуют соответствия выбранному контракту. |
| app.D_fa_report | 3 | observer_only | Первое pending событие fa_critical → report/reconfigure/terminate; producer-owned *_seq_age | Срок только observer; повторения coalesce без сброса oldest age. Позднее polling завершения/старые flags требуют соответствия выбранному контракту. |
| app.D_miss_report | 2 | observer_only | Первое pending событие miss_critical → report/reconfigure/terminate; producer-owned *_seq_age | Срок только observer; повторения coalesce без сброса oldest age. Позднее polling завершения/старые flags требуют соответствия выбранному контракту. |
| app.D_detect_warn | 5 | declaration_only | Не используется вне объявления в выбранном XML/queries | Декларация не реализует числовой SLA; часть решений использует классы и literal source-age 5/10. |
| app.D_detect_violation | 3 | declaration_only | Не используется вне объявления в выбранном XML/queries | Декларация не реализует числовой SLA; часть решений использует классы и literal source-age 5/10. |
| app.D_sensing_fresh | 10 | declaration_only | Не используется вне объявления в выбранном XML/queries | Декларация не реализует числовой SLA; часть решений использует классы и literal source-age 5/10. |

## Параметры интеграции

| Поле | Значение | Роль / интервал | Ограничение |
|---|---|---|---|
| layer_profiles | "default profiles recorded in inventory.json; APP constants from stored:app" | Pinned default profiles PHY/MAC/SDN, APP из stored XML | Полный набор 43 строк выше; enum codes не временные параметры. |
| D_cmd | 1 | MAC send / bridge receive → последовательные PHY handshakes + ACK; единый clock x=0 | Все фазы внутри 1, не по 1 на handshake. На =1 возможны доставка или loss; после потери MAC ждёт свой timeout=3. |
| D_bus | 1 | Локальные transport attempts от snapshot/accept до deliver/ACK либо loss | B_POLICY и dataplane не сбрасывают x между фазами; admission request/response сбрасываются отдельно. KPI p/m — отдельные clocks. |
| T_input | 5 | Попытка генерации PHY каждые 5; tick reset при попытке | Выбор loss/miss разрешён даже при готовности; pipeline busy сохраняет старый возраст. Период попыток, не гарантированных samples. |
| T_mac_tick | 5 | Попытка MAC tick каждые 5; local tick=0 | Потеря binary tick допустима; не гарантия завершения расписания. |
| T_demand | 1 | Один offer new_demand при bus_time=1 | Broadcast может быть не принят. Это абсолютное время от начала модели. |
| T_complete | 40 | Один offer service_complete при bus_time=40; раннее завершение по terminate | Не гарантированная длительность сервиса и не конечный горизонт исполнения всей модели. |
| fault_window | [12, 13] | Не более одного выбранного fault offer при bus_time в [12,13] | Ветка без отказа и drop разрешены; часы от начала модели, не от service start. |
| max_fault_events | 1 | Один проход ветки выбора fault | Структурное ограничение автомата, не clock bound. |
| max_requests_per_service | 1 | Один new_demand; один admission mailbox | Повторного сервиса нет. |
| max_outstanding_per_command_kind | 1 | Single-slot bridges и typed ACK/open flags | Не численный retry budget; повтор при busy не должен перезаписать mailbox. |
| freshness_warn_age | 5 | Возраст PHY source <5 fresh, >=5 stale до 10 | Сброс при генерации, не при доставке; latest overwrite инвалидирует предыдущую доставку; не max transport delay. |
| freshness_expire_age | 10 | Возраст PHY source >=10 expired | До первого sample missing; delivery не омолаживает источник. Два возраста разных источников не превращаются в одну физическую метрику. |
| justification | "Explicit abstract test choices for independent review, not calibrated network bounds. See interface-contract.md for ownership, loss and timeout rules." | Заданные choices абстрактного эксперимента | Нет физической калибровки, нормативного дедлайна или доказанного консервативного профиля. |
