# Целевые проверки будущих corrections

Статус: **specified, not run**. Новых model-checking results здесь нет.
Каждый correction использует оригинальный функциональный вариант, тот же вариант
с новым recorder и исправленную функциональную политику, когда она меняется.
Исходные наблюдатели не объявляются ошибочными по synthetic trace без machine run.

| Case | Сценарий | Ожидаемое различие / критерий |
|---|---|---|
| original | Восстановить закреплённые guards и clocks; управляемо задержать observer | Сохранить фактический результат старой модели; отдельно проверить witness раннего/позднего polling, не подставлять заранее verdict |
| fixed-timely | Start, matching end до D, observer получает ход после D | Новый recorder inactive, late=false; success/failure outcome различаются |
| late | End при D+1 в диагностическом mutant без functional invariant, затем новый start | late=true остаётся после второго start/end; приложить trace. Mutant не выдаётся за интегрированный candidate |
| no-completion-time | После start нет end, время может пройти D | Прямой bad-предикат достижим. Если fixed functional модель запрещает это, получить явный timeout/failure на D; удалить исход в отдельном mutant для отрицательного контроля |
| no-completion-stopped | После start бесконечный zero-time self-loop | elapsed safety может не обнаружить просрочку; completion не заявляется. Зафиксировать применённую семантику progress/time divergence |
| equality | End ровно D, а также конкурирующий timeout | Оба разрешённых исхода своевременны, strict lateness=false. D+1 — late; отрицательное время не генерируется |
| rapid-events | Два и более start/end в одном timestamp без шага observer | Каждый закрыт своим end; completed late никогда не исчезает |
| duplicate-start | Start во время active | Oldest age сохраняется, protocol_error отмечен для transaction contracts; для отдельно выбранного coalescing — один эпизод |
| stale-end | Unrelated ACK, duplicate старого end, новый эпизод | Не закрывает текущий эпизод; проверить typed channels и повторное использование слота |
| passive | Сравнить functional traces до/после recorder, скрыв monitoring updates | Те же timing/guards/channel choices. Наблюдатель не блокирует broadcast/binary sender, не добавляет clock reset core, не ограничивает время |

## Recovery-specific

- Link и node failures; standby, reembedding, прямой rollback; оба доступных
  маршрута не превращаются в принудительный приоритет без решения.
- Dispatch при r=0, r=19, r=20; исходный прямой rollback с ожиданием r>20
  исследовать в targeted original harness, не утверждать его достижимость в full model.
- Receiver занят на 20: новый локальный failure достижим без handshake;
  receiver готов на 20: rollback или failure разрешены.
- ACK standby/reembedding на 20, timeout→rollback на 20; rollback ACK/failed
  на b=10, общий elapsed<=30. Прямой rollback на 5 должен закончиться до 15.
- Недоступный failure_report receiver не блокирует локальный outcome;
  delivery failure и protocol recovery failure имеют отдельные evidence поля.
- Typed ACK другого канала и stale ACK после закрытия не меняют исход.
- Проверить deadlock/достижимость каждого исхода в каждом declared harness;
  отсутствие bad само по себе не является completion proof.

## Admission-specific

- Initial NONE и stale DEGRADED/REJECTED, FAILED без текущего outcome: запрос
  остаётся active. Реальный reject с любым согласованным impact закрывает SDN.
- Все пять SDN outcome-ветвей; spontaneous KPI-driven outcome не закрывает запрос,
  которого SDN не принимал. Проверить pre-state pending против same-edge tag.
- Два транспорта на их границах 1, Evaluate на 5: доставленный APP результат<=7.
- Потеря request: SDN diagnostic не открыт, APP timeout=15. Потеря response:
  SDN diagnostic закрыт, APP timeout=15. Safety downgrade до reject.
- APP result до 15 с observer после 15; duplicate после timeout; matching result
  на 15 vs локальный timeout на 15. Bridge total timeout не подменяет APP end.
- Broadcast sender/receiver корреляция: report предложен, но APP не принимает;
  staged payload без фактического APP transition не завершает admission.
- Последовательные повторения — только synthetic расширение текущего one-request
  envelope. Не выдавать их за поддержку нескольких requests в production candidate.

## Provenance и критерий принятия машинных проверок

Каждому variant/case/config — уникальный `run_id`, отдельные model/query bytes и
hashes. Сохранить source commit, generator hash, instance vector, параметры,
точную команду, фактически полученную tool_version, OS/runner/hardware, timestamps,
exit/status, stdout/stderr hashes и trace. Per-query результат обязателен.
`timeout`, `oom`, `error`, `license_blocked`, отсутствие результата — не success.
Negative-control ожидает достижимый bad, а не «все queries satisfied».

Отдельно индексировать original, recorder-only и functional-fixed variants.
Проверка пассивности относится к recorder-only. Functional recovery diff должен
быть явно описан и проверен как изменение политики, не trace equivalence.
Software unit tests и XML static checks сохраняются отдельно от UPPAAL.

Работа #31 — read-only regression reference: не повторять её реальные прогоны
без конкретного нового расхождения. Обычный software regression suite допустим.
Full-model ACK и прочие свойства, P3/P4 и Gate 1 не являются результатом этих
диагностик. Любое изменение full XML требует собственного model_hash.
