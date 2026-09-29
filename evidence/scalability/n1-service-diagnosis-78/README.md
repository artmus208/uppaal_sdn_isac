# Диагностика обслуживания N=1 — Issue #78

**Итог: вариант (c), причина таймаутов не установлена.** Машинного свидетельства
обслуживания полной исходной модели нет. Обязательная блокировка не доказана.
Установлены точный смысл запроса, условия локального перехода обслуживания и
несоответствие между grant и более сильным ожиданием «доставленный пакет / SLA».
Ранее сохранённые результаты доказывают достижимость непустой/полной очереди и
overflow, но не service. Новый UPPAAL-запуск не выполнялся.

Owner/account-id: **vadimnbkg**, подтверждённый GitHub account. Reviewer/Integrator:
**artmus208**. [Issue #78](https://github.com/artmus208/uppaal_sdn_isac/issues/78).
Process P2, поддержка R02/R05/R06; владение и приёмка R03/R04/C06 не меняются.
Base ref `origin/read`, точный base commit
`8237e8c2bec41aa1bb943cc33be1ac9586d03759` (merge #77).
Branch `codex/vadimnbkg/78-n1-service-diagnosis`.
Единственный write scope: `evidence/scalability/n1-service-diagnosis-78/**`.

## 1. Предмет проверки и принятые входы

Исследуется `uav-family-r1-20260929`, N=1: **50 автоматов**, включая SharedLoad,
частные PHY/MAC/SDN/APP, окружение и 22 observers. Входы приняты через #69/#71,
[A/B и ограниченную применимость P1/P2](https://github.com/artmus208/uppaal_sdn_isac/pull/73#issuecomment-5890790922),
[активацию #74/#75](https://github.com/artmus208/uppaal_sdn_isac/pull/75#issuecomment-5891123461)
и принятую серию #76/#77 из поручения. Последняя была слита в указанный base.
Применяется v2 по [решению #64](https://github.com/artmus208/uppaal_sdn_isac/issues/64#issuecomment-5878071165).
Current pointer сохраняет исторический baseline по умолчанию; семейство выбрано
явно для этой диагностики. Исторические P3 verdicts на него не переносятся.
Открытые Issue scopes проверены перед claim: пересечения нового каталога нет.

| Объект | Точное значение |
|---|---|
| Manifest | `manifests/baselines/uav-family-r1.yaml` |
| Manifest SHA256 | `5480bef5b00020735259f10eb43bdd9bc79ebc364a3bbcacad34c78fd0552cbf` |
| Model | `evidence/scalability/family-series-68/generated/n1/model.xml` |
| Model SHA256 | `5234cb087e5274798926d516dedc77d1f9542ea7df59cec39f83859771ce1385` |
| Query file | `evidence/scalability/family-series-68/generated/n1/p4/u0-service.q` |
| Query | `E<> family_grant_0` плюс завершающий LF |
| Query SHA256 | `5aeca4a4152577404ee725b1b2c2c697bdb02803c291742ce01c73b9a0d6c789` |
| Generator aggregate | `4b54f27d7925d07c9070a51d845dbee0659965b79e2d2baf3640157a12e9cdc8` |
| Family source aggregate | `a8854d7a40d8329b185bda911ff7ae8aa55fac129a7bce53854445efedb635d8` |
| Parameters SHA256 | `f89f9bb0cbaff4a45440533aa273fc38f2d9efdd34b77309b59187c6c75b9a18` |
| Instance vector SHA256 | `69b5105223a5dd3a2bae34513f6126416fdb15fad0b99a6b405f977332feddad` |

Все N=1 pins, declarations, system order, locations и transitions с исходными XML
line numbers сохранены в [model-inventory.json](model-inventory.json). Это
детерминированная статическая выгрузка, не результат model checking.

`family_grant_0` начинается с `false` и записывается только SharedLoad при выборе
`server=0`. Флаг хранит выбор последней завершённой эпохи; на следующем выборе
`server=-1` сбрасывается. Это не накопительный счётчик и не отдельный observer.
На переходе grant одновременно выполняется абстрактное вычитание единицы работы
из очереди **только если прежняя очередь не находилась в overflow**.
При одновременном arrival=1 длина очереди может не уменьшиться. В absorbing
состоянии q=5 флаг может стать true вообще без вычитания.

Следовательно, исходный query означает: **существует конечный префикс исполнения,
в котором UAV выбран общим сервером**. Он не требует command send, PHY ACK,
положительного admission, доставки физического пакета или SLA. `E<>` не содержит
гарантии для всех трасс; starvation на другой трассе не опровергает этот запрос.
Семантика reachability сверена с
[официальным описанием symbolic queries](https://docs.uppaal.org/language-reference/query-semantics/symb_queries/).

## 2. Причинная цепочка в точном XML

Ссылки в таблице ведут на неизменный XML в base commit; диапазоны ниже служат
для чтения, а точные labels доступны также в JSON inventory.

| Шаг | Templates, locations, guards и updates | Что это устанавливает |
|---|---|---|
| Инициализация | [XML:3–57](https://github.com/artmus208/uppaal_sdn_isac/blob/8237e8c2bec41aa1bb943cc33be1ac9586d03759/evidence/scalability/family-series-68/generated/n1/model.xml#L3): `family_last_server=-1`, grant=false, q=0, K=4, overflow=false. [XML:392–408](https://github.com/artmus208/uppaal_sdn_isac/blob/8237e8c2bec41aa1bb943cc33be1ac9586d03759/evidence/scalability/family-series-68/generated/n1/model.xml#L392): freshness=MISSING, scheduleMode=IDLE, priority flags=false. Clocks первоначально 0. | На первом tick обслуживать нечего. |
| Поступление | [SharedLoad:7704–7744](https://github.com/artmus208/uppaal_sdn_isac/blob/8237e8c2bec41aa1bb943cc33be1ac9586d03759/evidence/scalability/family-series-68/generated/n1/model.xml#L7704): Wait invariant `tick<=5`; Wait→Sample_1 guard `tick==5`; `arrival_0∈{0,1}`, шесть независимых классов `m1…m6` выбираются и сохраняются локально. | Это недетерминированный вход окружения, не APP packet-send и не внешняя обязательная посылка. |
| Очередь / service | [Sample_1→Publish_0:7746–7751](https://github.com/artmus208/uppaal_sdn_isac/blob/8237e8c2bec41aa1bb943cc33be1ac9586d03759/evidence/scalability/family-series-68/generated/n1/model.xml#L7746): `server∈{-1,0}`, guard `tick==5 && (server!=0 || (q>0 && mode∈{COMM,JOINT}))`. Update `q=(q>K ? q : q-[server=0]+arrival)`; sticky overflow, derived queueClass, sampled load classes, age=0/valid=true, grant/last_server, tick=0. | Проверяются старая очередь и уже выбранный MAC mode. Вычитание и прибавление атомарны. `server=-1` разрешён всегда. |
| Уведомление нагрузки | [Publish_0→Offer_0→Wait:7753–7766](https://github.com/artmus208/uppaal_sdn_isac/blob/8237e8c2bec41aa1bb943cc33be1ac9586d03759/evidence/scalability/family-series-68/generated/n1/model.xml#L7753): сначала broadcast `bus_new_mac_sample!`, затем binary `mac_mac_tick!` либо безусловный skip с `bus_tick_missed=true`. Sample_1/Publish_0/Offer_0 committed. | Grant уже записан до notifications. Потерянный последующий tick не отменяет состоявшийся grant. |
| Запуск MAC | [A_SCH:2865–2907](https://github.com/artmus208/uppaal_sdn_isac/blob/8237e8c2bec41aa1bb943cc33be1ac9586d03759/evidence/scalability/family-series-68/generated/n1/model.xml#L2865): Idle принимает `mac_mac_tick?`, сбрасывает c_sched, входит в CollectKPI (`c_sched<=2`). Broadcast `mac_phy_kpi_report?` переводит в SelectMode (`c_sched<=5`) со сбросом c_sched. Stale/missing или deadline допускает fallback CONSTRAINED. | Одна лишь свежая переменная не переводит scheduler: требуется уведомление, пока он в CollectKPI. Fallback при MISSING может сработать сразу, но не urgent. |
| PHY/KPI вход | [E_PHY_INPUT:4291–4459](https://github.com/artmus208/uppaal_sdn_isac/blob/8237e8c2bec41aa1bb943cc33be1ac9586d03759/evidence/scalability/family-series-68/generated/n1/model.xml#L4291): finite samples каждые 5 единиц, `bus_new_sample!`, offered/dropped `phy_measure_tick!`. PHY child reports и A_PH aggregate `phy_phy_kpi_report!` (например [2730](https://github.com/artmus208/uppaal_sdn_isac/blob/8237e8c2bec41aa1bb943cc33be1ac9586d03759/evidence/scalability/family-series-68/generated/n1/model.xml#L2730)). | Полная композиция содержит источник KPI. Его доставка и нужный порядок не гарантированы. |
| KPI bridge | [B_KPI:6377–6938](https://github.com/artmus208/uppaal_sdn_isac/blob/8237e8c2bec41aa1bb943cc33be1ac9586d03759/evidence/scalability/family-series-68/generated/n1/model.xml#L6377): report ставит pending и p=0; `pending && valid && p<=1` допускает Map. При age<5 устанавливается FRESH, при 5≤age<10 STALE, иначе MISSING; mappedResourceClass зависит от share/resource. Далее committed Map→Mac→Sdn→App→Notify→MacNotice→CtrlNotice→Return. | MAC KPI broadcast идёт после mapping, до SDN/APP notices. Loss и новые samples могут изменить путь. |
| Выбор режима | [gP0…gP7:410–419](https://github.com/artmus208/uppaal_sdn_isac/blob/8237e8c2bec41aa1bb943cc33be1ac9586d03759/evidence/scalability/family-series-68/generated/n1/model.xml#L410), [SelectMode→ApplySchedule:2920–2924](https://github.com/artmus208/uppaal_sdn_isac/blob/8237e8c2bec41aa1bb943cc33be1ac9586d03759/evidence/scalability/family-series-68/generated/n1/model.xml#L2920): gP0 exhausted запрещает нормальный выбор; gP1 overflow-class/violated delay или gP2 critical queue+demand выбирает COMM; gP3 sensing priority выбирает SENS; gP4 conflict выбирает JOINT; gP5 stale/missing выбирает CONSTRAINED; gP6 free/balanced выбирает JOINT. | Приоритет условий существенен: свежесть нужна номинальному пути gP6, но не обязательна для более ранних gP1/gP2/gP4. COMM не требует `sdn_comm_priority_allowed`. |
| Command/ACK | [ApplySchedule→WaitPHYAck:2927–2979](https://github.com/artmus208/uppaal_sdn_isac/blob/8237e8c2bec41aa1bb943cc33be1ac9586d03759/evidence/scalability/family-series-68/generated/n1/model.xml#L2927), B_PHY_MAC [5995–6104](https://github.com/artmus208/uppaal_sdn_isac/blob/8237e8c2bec41aa1bb943cc33be1ac9586d03759/evidence/scalability/family-series-68/generated/n1/model.xml#L5995). Команда binary, ACK deadline 3, bridge deadlines 1. | ApplySchedule не имеет invariant/urgent/committed. Можно сохранять выбранный mode до следующего shared tick без отправки команды. Service guard ACK не читает. |
| Наблюдение / APP | Grant виден непосредственно в Publish_0. APP E_SERVICE даёт demand в t=1 и предлагает completion в t=40 ([5862–5874](https://github.com/artmus208/uppaal_sdn_isac/blob/8237e8c2bec41aa1bb943cc33be1ac9586d03759/evidence/scalability/family-series-68/generated/n1/model.xml#L5862)); admission идёт через отдельный B_ADMISSION. | Нет связи «этот queue dequeue завершил этот APP request». APP/SLA получает telemetry, но grant не является его входным событием. |

В полном XML нет urgent locations; начальные locations не committed. Committed
цепочки запрещают течение времени и допускают interleaving с другими committed
переходами. Broadcast receivers участвуют согласно guards и system order; sender
update предшествует receiver updates. Это применённые правила
[семантики UPPAAL](https://docs.uppaal.org/language-reference/system-description/semantics/),
а не допущение о произвольном последовательном вызове компонентов.

На каждом `bus_new_mac_sample?` B_KPI сбрасывает pending/delivery-valid MAC.
PHY `bus_new_sample?` сбрасывает доставку PHY, выставляет freshness=MISSING и
может отменить текущую publication. Если MAC KPI broadcast прошёл до `mac_tick`,
scheduler в Idle его не принимает. Поэтому уведомления, начальные MISSING и
fallback могут направлять поиск в CONSTRAINED. Это разрешённые ветви, пока не
показано, что они обязательны для всех путей.

## 3. Clocks, observers, overflow и ручной кандидат

B_KPI `p<=1 && m<=1` не означает неизбежный timelock в t=1: предусмотрены как
pending-loss, так и `!pending` reset loops (6736–6837). MacNotice/CtrlNotice имеют
безусловные loss exits (6906/6922), поэтому отсутствие binary receiver само по
себе не запирает эту committed цепочку. У observers нет location invariants;
committed PHY observation states имеют разделённые выходы `clock<=D` и `clock>D`
(например 6993–7001). Статически обязательная остановка в этих местах не найдена;
глобальная deadlock freedom этим не установлена.

MAC ACK instrumentation стартует inactive и включается со сбросом возраста
только при отправке команды (421–422, 2931), не при выборе policy. Queue observer
запускает часы на Q_CRIT, а «разрешением» в пределах deadline считает выход из Q_CRIT, report, COMM
или CONSTRAINED (7183–7189). JOINT прямо не проверяется, однако уменьшение
очереди через JOINT может вывести queueClass из Q_CRIT. Это не observer dequeue.
APP episode flags первоначально false, их времена привязаны к своим recorded
событиям; SharedLoad не уведомляет их о grant. Старые observer limitations не
исправлялись и не используются как доказательство полезного service.

В q=5 очередь поглощает дальнейшие updates, overflow sticky. Grant при q=5
возможен локально, но q остаётся 5. При q≤4 service выбирает непустую очередь и
вычитает единицу до arrival; service не создаёт overflow. Overflow поэтому
искажает смысл исходной формулы, но не является необходимым условием service
и сам по себе не делает grant недостижимым.

**Ручной кандидат, без машинного replay/verdict:**

1. t=1: demand, RequestBuild→committed RequestReady→RequestPending. Нельзя
   «припарковать» APP в RequestReady. B_ADMISSION проходит StageRequest→OfferRequest
   и в t=2 берёт request-loss. APP admission deadline наступит позже t=10.
2. До t=5 выполнять пустые timer resets B_KPI. В t=5 SharedLoad выбирает arrival=1,
   все m=0, server=-1; q становится 1. Сначала завершить publish и доставить tick,
   чтобы scheduler вошёл в CollectKPI.
3. В том же t=5 взять номинальные PHY inputs: SINR=2, остальные классы 0,
   miss=0/scenario=0; new_sample, measure_tick, channel/sensing/aggregate reports.
   Доставить PHY KPI через Map→Mac…Return: freshness=FRESH, mapped resource=FREE.
4. После committed notifications scheduler из SelectMode выбирает gP6=JOINT.
   Оставить его в ApplySchedule; команда ещё не отправлена. До t=10 выполнять
   пустые p/m resets. SDN CollectReports bound 5 допускает сам t=10, APP admission
   age=9 укладывается в 15, fault envelope до 13 и service environment до 40.
5. В t=10 SharedLoad выбирает arrival=0/server=0: guard видит q=1 и JOINT,
   update даёт q=0/grant=true, ещё до последующих notices.

Это проверяемая цель для replay, а не полный сериализованный trace из 50 процессов.
Перечисление совместимых локальных шагов и deadlines **не заменяет** машинную
проверку всей композиции. Тем не менее оно показывает, почему отсутствие ACK,
admission или разрешения SDN нельзя объявить установленной причиной таймаута.
Самая ранняя возможная service-эпоха — **t=10**: в t=5 guard ещё видит исходную q=0.
Время здесь абстрактное, не секунды физической сети.

## 4. Что уже запускали и что действительно сохранено

[history.json](history.json) содержит 32 выполненные N=1 записи: 7 из #68, одну
из #70, 24 из #76; это scientific attempts **вместе с** compile/load записями.
В каждой сохранены исходный index/array position и hash записи, точная команда,
source commit, model/query/generator hashes, native hardware, limits, raw log/
monitor/memory/trace пути и hashes. Исходные artifacts не переписаны.

Все пять service attempts используют model/query hashes из §1 и фактически
записанную версию `UPPAAL 5.0.0 (rev. 714BA9DB36F49691), June 2023`.
В каждом **status=timeout, verdict=null, trace отсутствует**, stderr пуст;
process reaped. Состояния не напечатаны даже в raw stdout.

| run_id | Поиск / seed | Предел / wall, s | CPU, s | Native peak, bytes |
|---|---|---:|---:|---:|
| `diagnostic-001-n1-u0-service` | DFS / 68 | 30 / 32.072326 | 31.265625 | 178761728 |
| `service-002-n1-u0-service` | random DFS / 20260929 | 30 / 32.148250 | 26.671875 | 248950784 |
| `uav-p4-76-campaign-002-004-r1-n1-u0-service` | DFS / 68 | 60 / 62.118797 | 59.562500 | 242065408 |
| `uav-p4-76-campaign-002-043-r2-n1-u0-service` | DFS / 68 | 60 / 62.141054 | 48.687500 | 176615424 |
| `uav-p4-76-campaign-002-082-r3-n1-u0-service` | DFS / 68 | 60 / 62.073956 | 55.281250 | 212090880 |

Общий memory stop 2 GiB sampled, во всех пяти случаях не достигнут; wall включает
termination. #68: Windows 10 build19045, Intel i5-8300H, source
`2548ec82a8fa98b3e152641fbc7a5eda30e4e07c`; #70: Windows11 build26200, Ryzen5 1400,
source `ecf08b52dadce0d5413307775f6b1d36cd13fabb`; #76: тот же тип Ryzen host,
source `877fa69a29e1732db2b4047eebdd99591b185c77`. Exploration=0, representation=1,
`-S1/-n0` сохранены; #70 также отличается отсутствием `-q`.
Эти timings не объединяются в однородную выборку и не характеризуют throughput.

Машинные результаты для других N=1 queries (не service):

| Точный run_id #68 | status / verdict | Формула | Query SHA256 |
|---|---|---|---|
| `diagnostic-001-n1-joint-backlog` | success / satisfied | `E<> u0_mac_queue_q > 0` | `706bd493fef18a2de31be212156825af913ef21adde7d15cda47dc1bc1825afe` |
| `diagnostic-001-n1-u0-queue-full` | success / satisfied | `E<> u0_mac_queue_q == u0_mac_queue_K && !u0_mac_queue_overflow_seen` | `3818bec4871dc7de0d63514ca87ad26065f0abecee33e8cb6f45d999ddd09e55` |
| `diagnostic-001-n1-u0-queue-safety` | success / violated | `A[] !u0_mac_queue_overflow_seen` | `48989eef927665697ce2687c5eccfcd99da2a9e46b97640003421fd620ca3291` |

Для всех трёх model_hash и exact tool_version приведены выше; полные provenance
и explicit stdout verdicts доступны по этим run_id в history.json. Эти результаты
исключают отсутствие arrivals и глобальный запрет всех поздних эпох: q=4/5 требует
нескольких shared ticks. Они не устанавливают service-compatible mode.

15 сохранённых N=1 trace files из #68/#76 после распаковки представляют всего
три побайтно одинаковых trace contents: backlog (27 discrete states), queue full
(711), overflow (829). Extractor использует **сохранённый compile layout**,
сверяет 255 discrete variable indices/domains/initial values и число 50-component
location vectors. Во всех увиденных состояниях grant=0, last_server=-1, mode
только IDLE/CONSTRAINED; комбинации q>0 с COMM/JOINT нет. Это чтение сохранённых
трасс, не timed replay, не доказательство отсутствия других трасс.

Сохранённый compiler output содержит 3559 edges, из них **2592** — развёртка
одного SharedLoad staging select: `2×3×4×3×4×3×3`. Это конкретный источник
ветвления. Причинную связь с service timeout измеренные данные не устанавливают:
нет service-search state counts или профиля очереди поиска.

Два setup сбоя не смешиваются с service attempts: #70 service-001 завершился
monitor_error на version-only probe с нулём memory samples; #76 campaign-001
остановился на `Pinned input changed: manifests/collaboration-v2.yaml` до
verifier. Его 24 N=1 not_started rows не входят в 32 выполненные записи.

**Найденный пробел metadata:** #76 runner пишет `states_explored=not_available`
безусловно, хотя в raw stdout 15 N=1 записей есть число состояний (3 load и
12 scientific). Для scientific это 26 explored/20838 stored (backlog),
748/91667 (queue-full), 866/123488 (обе queue-safety формулы). Источник и точное
значение отражены отдельно в `history.json.metadata_gaps`. Старые records и
runner не исправлялись. Для service states действительно отсутствуют.

## 5. Конкурирующие объяснения

| Гипотеза | Основания и различающая проверка | Статус |
|---|---|---|
| Service существует, поиск не успевает | Пять censored searches; 2592 staging branches; ручной кандидат. Новый BFS с промежуточными D1/D2 и полезным D3 проверит короткий путь при том же полном XML. | Правдоподобна, **не доказана**. CPU/timeouts не устанавливают state explosion как точную причину. |
| Query/observer не соответствует ожидаемому событию | Grant допускается после overflow и до ACK; нет APP/SLA correlation. D3 уточняет абстрактное обслуживание до overflow. | **Установлено различие смыслов**, но это не объяснение недостижимости самого grant. Ошибка observer как причина timeout не установлена. |
| Guards/синхронизация блокируют переход | Нужны одновременно backlog, COMM/JOINT и shared epoch. Публикацию можно пропустить, fallback может выбрать CONSTRAINED. D1 проверяет CollectKPI→SelectMode, D2 — pre-service guard с дополнительным ограничением q≤K. | Обязательная блокировка **не найдена**; полностью исключать скрытую композиционную блокировку нельзя. |
| Обязательный вход отсутствует | Источник arrivals и успешные backlog/full runs есть. PHY input/report/KPI edges есть; ручной порядок совместим локально. | Отсутствие arrivals **исключено**. Отсутствие нужного KPI ordering на всех трассах пока не исключено машинно. Admission/ACK не обязательные условия grant. |
| Overflow/другой режим мешает | q=5 поглощает updates; старые trace modes только IDLE/CONSTRAINED. D2 ограничивает q≤K и mode; D3 проверяет полезный outcome. | Ветви overflow/fallback подтверждены, их неизбежность до любого service **не установлена**. |
| Starvation исключает E<> | Сервер может всегда выбирать -1, notifications могут теряться. | Логически неверный вывод: отсутствие all-trace гарантии не опровергает existential reachability. |
| Прежние service-запуски на самом деле OOM/ошибка | Raw stderr пуст, status timeout, native peaks значительно ниже 2 GiB, child reaped. | Для пяти сохранённых попыток это объяснение **не поддерживается**; они остановлены по времени. |

Вариант (a) не заявляется: machine witness service отсутствует. Вариант (b) не
заявляется: конкретный обязательный blocking mechanism не установлен. Вариант
(c) — завершённый диагностический результат в разрешённом статическом бюджете:
новых научных запусков 0, пять старых service attempts разобраны, наиболее
информативная следующая проверка конкретизирована.

## 6. Следующий эксперимент и границы исправлений

[PROTOCOL.md](PROTOCOL.md) и [protocol.json](protocol.json) содержат три новые
формулы на неизменной полной модели: D1 SelectMode, D2 healthy service-ready
Sample_1, D3 immediate grant без overflow. По одному BFS-запуску, 30 s/query,
2 GiB sampled stop, минимум 3 GiB свободной RAM перед каждым запуском, общий
wall cap 300 s с metadata/controls/cleanup. Это **предложение, не разрешение**.
Команды, hashes, настоящий доступный Windows10/Intel host и stop rules заданы.
Положительный verdict не требуется для приёмки этого диагностического отчёта.
Успешный отрицательный D2 исключит D3, но **не исходный grant через q=5**: q≤K
является дополнительным ограничением диагностического вопроса.

Если требуемый смысл — реальная доставка, отдельно предложить P2 Issue для
контракта packet identity/arrival/departure, корреляции с command/ACK/admission
и observer до/после overflow. Это изменит семантику модели/generator, hashes,
потребует нового baseline и решения Gate 1; старые результаты сохраняются в
прежнем scope. По этому Issue такие изменения не сделаны. Если достаточно
абстрактного queue service, уточнить название исходного query как service-choice
и использовать отдельную формулу useful-departure, явно сохраняя различие claims.
Пробел state-count metadata передан в Issue #78 как замечание для владельца P4.

## 7. Воспроизведение и handoff

Без UPPAAL и без изменения исходных evidence:

```sh
python3 -B evidence/scalability/n1-service-diagnosis-78/audit.py
python3 -B evidence/scalability/n1-service-diagnosis-78/inspect_model.py \
  --check evidence/scalability/n1-service-diagnosis-78/model-inventory.json
python3 -B evidence/scalability/n1-service-diagnosis-78/inspect_history.py \
  --check evidence/scalability/n1-service-diagnosis-78/history.json
```

`checks/validation.json` сохраняет точные команды/exit codes/raw logs: **209 unit
tests**, coordination, family baseline/history hash audit, MCP и CLI smoke checks
прошли. Использовано отдельное `.venv`, Python3.12/MCP1.30.0. После этих тестов
production code не менялся; добавленные extraction scripts проверены на исходных
artifacts. `checks/package-audit.json` фиксирует pins, query structure, scope и
hash index. Статические проверки не называются model checking.

Работа изолирована в `/tmp/uppaal-n1-diagnosis-78`; исходный dirty checkout с
промтами сохранён. Sandbox exec не запускался из-за bubblewrap bind-mount
`/mnt/wslg/distro`; разрешённые команды выполнены вне него. SSH fetch завершился
host-key error, публичные Git refs получены через HTTPS. Ни один scientific
verifier process не запускался, version не подставлялась. Raw failure запуска
sandbox сохранён в описании окружения, не выдан за ошибку модели.

Checkpoint bundles хранятся вне `/tmp` в
`/mnt/c/Users/musta/Desktop/pySources/mcp_uppaal/evidence/scalability/n1-service-diagnosis-78/handoff/`.
Финальный remote HEAD, scope, clean state, bundle и PR перечислены в GitHub
handoff Issue #78. Следующий шаг — независимое review отчёта; отдельно — решение
пользователя о предложенном эксперименте. Автор не принимает результат, не
сливает PR и не закрывает R03/R04/C06.
