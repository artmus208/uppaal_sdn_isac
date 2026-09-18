# Решения для реализации и review

Статус всех новых решений: **выбрано автором #33, требуется независимое принятие**.
Исходная реализация не изменена. Ссылки `template:edge:N` раскрываются в
[source-anchors.json](source-anchors.json), hashes — в [inputs.json](inputs.json).

## Recovery: один эпизод, два бюджета

Начало R0 — приём `sdn_link_failure?` либо `sdn_node_failure?` самим A_REC
в StableConfig (`sdn_Template_A_REC:edge:0/1`). Offer внешней среды без приёма
не начинает эпизод. Возраст `r` сбрасывается только здесь; функциональный
`sdn_c_rec` уже имеет эту точку сброса. Ожидание в FailureDetected входит в r.

Конец R1 — переход этого эпизода в StableConfig по соответствующему typed ACK
либо локально зафиксированный RecoveryFailed с причиной. Это завершение
протокола восстановления, не успешный SLA, реальное восстановление радиоканала
или доставка failure_report внешнему потребителю. ACK другого типа не закрывает
эпизод. Доставка отчёта имеет отдельный статус и не задерживает локальный исход.

Выбранные требования:

- Не позднее `r=20`: успех, фактическая отправка rollback или локальный отказ.
- При rollback его возраст `b=0` устанавливается на фактической отправке
  `bus_rollback_request!`, а r не сбрасывается.
- После rollback ACK либо локальный отказ при `b=10`; итог `r<=30`.
- Дедлайны включают равенство. Просрочка: строго `>`, а не `>=`.
- При совпадении ACK и deadline допустимы своевременный ACK или явный timeout;
  приоритет успеха не добавляется. Результат тайм-аута не является успехом сервиса.

| Ветвь | Исходная структура | Выбранная диспозиция |
|---|---|---|
| Standby | edge:2, затем edge:5; c_rec от отказа, ACK<=20 | Ожидание dispatch входит в 20. ACK закрывает R1. По истечении 20 — rollback или локальный отказ |
| Reembedding | edge:3, edge:6; тот же c_rec | То же правило; typed flow ACK, не policy/rule/control ACK |
| Timeout standby/reembedding | edge:7/8 при c_rec=20, rollback clock=0 | Успешная отправка rollback на 20 даёт максимум ещё 10. Занятый/недоступный binary receiver не должен блокировать локальный отказ на 20 |
| Прямой rollback | edge:4, раньше без предела ожидания | Отправка при r<=20, b=0, конец не позднее r_dispatch+10<=30. Не выдавать 10 за полный срок от отказа |
| Нет подходящего dispatch к 20 | FailureDetected сейчас без инварианта | Функциональная коррекция: предел ожидания 20 и несинхронизированный локальный failed outcome на 20; возможность rollback на границе сохраняется |
| Rollback ACK | edge:9, b<=10 | Завершить тот же эпизод; сохранить elapsed/late evidence |
| Rollback без ACK | edge:10 при b=10, сейчас с failure_report! | Локальный failed outcome на 10 независимо от получателя отчёта. Отчёт отделить от исхода; не добавлять обязательный handshake наблюдателя |

В фазах standby/reembedding на 20 также нужен локальный fallback, если dispatch
rollback недоступен; нельзя исправить только FailureDetected. Локальный fallback
на границе разрешается недетерминированно, даже если доставка rollback возможна:
предположение об обязательном выборе готового транспорта не вводится. Reason
должен различать dispatch timeout и rollback timeout. В Rollback успех и failure
на 10 — два допустимых исхода, оба завершают эпизод своевременно.

Это **функциональное изменение** множества допустимых поведений относительно base,
отдельное от пассивного recorder. Не скрывать его под названием «починка observer».
Проверять два слоя: исходная функциональная модель + новый recorder (пассивность),
затем отдельно новая recovery-политика + тот же recorder (соответствие контракту).
Если reviewer отклонит функциональную политику, остаётся только stage-only claim;
общий failure-to-outcome<=30 тогда не заявляется.

Нет promise завершения на всех бесконечных трассах без продвижения времени.
Инвариант не выбирает переход и не исключает посторонние бесконечные zero-time
циклы. Отдельно проверяются deadlock, возможность завершения и completion under
заявленным условием time divergence; отсутствие Violation их не заменяет.

## Admission: три различных интервала

| Интервал | Начало | Конец | Предел |
|---|---|---|---:|
| APP admission | `app_A_REQ:edge:2`, APP send; a=0 | APP принимает matching accept/degraded/reject на edge:3/4/5 либо локальный timeout edge:13 | 15 |
| SDN admission diagnostic | `sdn_Template_A_POLICY:edge:0`, bus_admit_request при PolicyIdle; s=0 | Один из пяти outcome-переходов Evaluate edge:3..7, но только при открытом запросе | 15 |
| SDN evaluation | Вход Evaluate от request/KPI/MAC report, c_dec=0 | Фактический outcome Evaluate | 5 |

SDN-local 15 сохраняется как отдельное observer requirement; это не длительность
Evaluate. Не закрывать APP на SDN outcome: ответ ещё должен пройти транспорт и
быть принят APP. `serviceImpact` — payload/классификация, **не completion event**.
Начальное NONE, старый DEGRADED/REJECTED, FAILED без текущего outcome не завершают
запрос. Каждый реальный tagged reject закрывает SDN diagnostic вне зависимости
от кодирования impact. ACK/успех сервиса к этому контракту не относятся.

| Случай | Разбор и решение |
|---|---|
| Нормальный принятый запрос и доставленный ответ | Request transport<=1, Evaluate<=5, response transport<=1; 1+5+1<=7<=15. Каждый x сбрасывается на начале своего transport. Это условная верхняя граница, не гарантия выбора delivery |
| SDN не принял запрос / потеря запроса | SDN-local эпизод не открыт. APP остаётся pending до явного timeout на 15 |
| Потеря ответа | SDN-local эпизод закрыт на emission; APP закрывает timeout на 15. Не копировать SDN success в APP |
| Reject / запрещённый degraded | Соответствующий ответ завершает APP с отказом; StageOutcome/Safety могут изменить degraded в reject до передачи, но staging ещё не APP completion |
| Ответ и APP timeout на 15 | Сохраняются обе разрешённые альтернативы; только первый принятый исход закрывает эпизод. Поздний duplicate не переоткрывает и не переписывает исход |
| Bridge timeout | `Boundary_B_ADMISSION:edge:19` завершает ожидание моста, но не заменяет APP edge:13 и не сбрасывает APP age |
| Бесконечная остановка времени | Отсутствие elapsed violation не доказывает доставки/timeout. Отдельный no-completion case обязателен |

RequestBuild<=3 не входит в send-based 15. RequestReady может ждать неограниченно;
`T_demand` и `T_complete` не превращают их в end-to-end SLA.

В интегрированной адаптации все пять SDN outcome-переходов уже очищают pending;
в standalone SensingBoost этого нет. Исправление #33 нацелено на **интегрированный**
кандидат: нельзя механически переносить вывод standalone generator на его XML.
Bridge читает pending в pre-state, а `bus_outcome_for_request` публикуется на
исходящем переходе; сохранять порядок guards/updates. Initial/old impact не может
быть условием закрытия. Текущий envelope — один service request и single-slot
bridge; полноценная multi-request корреляция не заявляется.

## Пассивная регистрация времени

На каждый выбранный тип эпизода: `active`, clock `age`, sticky `late`;
при необходимости отдельный sticky `protocol_error`. Это monitoring state.
Функциональные guards/данные не должны зависеть от него. Observer только читает
эти поля; его scheduler не владеет reset/clear.

| Событие | Эффект |
|---|---|
| Start при !active | На фактическом start-переходе active=true, age=0. late не очищается |
| Start при active | Не сбрасывать oldest age. Для single-transaction recovery/admission — protocol_error; новое событие не «обслужено» этим старым эпизодом |
| Matching end при active, age<=D | Атомарно active=false. Observer, запущенный много позже, не создаёт ложную просрочку |
| Matching end при active, age>D | Атомарно late=true, active=false; поздний результат не стирает нарушение |
| No end, active && age>D | Плохое состояние определяется непосредственно этим предикатом; не требуется, чтобы polling-переход уже случился |
| Unmatched/duplicate end | Не закрывать новый/другой эпизод, не сбрасывать age/late; отдельно различать разрешённый unsolicited policy outcome и protocol error |
| Следующий эпизод без движения времени | Допустим после end; sticky late предыдущего сохраняется; observer может вообще не выполнить шаг между эпизодами |

Проверяемый предикат elapsed safety: `!late && !(active && age>D)` (и отдельная
проверка protocol_error). Если сохраняется location `Violation` для старого query,
нужно доказать соответствие его reachability этому предикату; одного незапланированного
перехода в Violation недостаточно для чтения snapshot состояния.

UPPAAL-реализация должна быть типокорректной. Для binary end-переходов допустимо
исчерпывающее разбиение исходного guard на `age<=D` и `age>D`, с одинаковыми
функциональными updates, без нового инварианта/задержки/синхронизации. Clock
comparison нельзя просто записать как произвольное boolean assignment.
Для broadcast receive нельзя добавлять clock guard, запрещённый используемой
семантикой инструмента. Admission completion может потребовать регистрации на
соответствующем sender с проверкой реального участия APP либо иной законной схемы;
guard готовности APP и порядок updates должны совпадать с исходным handshake.
Любые committed промежуточные states требуют отдельной проверки, что не теряются
функциональные interleavings; автоматически пассивными они не считаются.

Корреляция в конечном envelope обеспечивается открытым однослотовым эпизодом и
typed channel/реальным локальным переходом, не растущим без границы sequence int.
В расширенных harnesses повторения идут последовательно, а запоздалый ACK старого
эпизода при новом — отдельный negative case. Если требуется хранить идентификатор
через повторное использование слота, сначала определить конечную политику
drain/generation; modulo token без защиты от stale ACK не принимается.

Для остальных APP event latches текущая семантика **coalesced oldest outstanding**:
повторное однотипное уведомление не начинает новый deadline. Закрытие одним
matching response относится к агрегированному эпизоду, не доказывает ответ на
каждое уведомление. Исправление этих latches не включено в admission correction.
