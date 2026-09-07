# Формализация уровней иерархической SDN-управляемой 6G ISAC-сети

Рабочая Markdown-версия. Раздел PHY изложен по последней TeX-версии без сохранения служебного TeX-синтаксиса; далее добавлены уровни MAC / Resource Scheduling, SDN Control Plane / RAN Intelligent Controller и Application / Service Layer.

## 1. PHY-уровень

### 1.0 Аннотация

В статье формализуется физический уровень PHY (Physical Layer) для иерархической модели SDN-управляемой сети 6G ISAC, где SDN (Software-Defined Networking) используется для оркестрации ресурсов, а ISAC (Integrated Sensing and Communication) объединяет передачу данных и радиозондирование среды. Модель не является радиофизическим симулятором и не утверждает, что обычные временные автоматы вычисляют SINR, CRB, вероятность обнаружения или распределения задержек. Измеренные PHY-величины и конфигурационные параметры сначала оцениваются внешним измерительным или аналитическим слоем, затем консервативно отображаются в конечные классы функцией абстракции alpha_PHY:X_meas x X_cfg-> X_disc. Сеть PHY далее задается как композиция контрактных временных автоматов с явными часами, guards, resets, инвариантами, broadcast-уведомлениями отчетов, handshake-командами, приоритетами классификации, environment-stub автоматами и observer-автоматами для bounded deadlines. Такая постановка позволяет проверять не радиофизику как таковую, а своевременную реакцию MAC/SDN на классифицированные деградации communication и sensing KPI.

### 1.1 Назначение и границы модели

Физический уровень в 6G ISAC-сети выполняет две связанные функции: обеспечивает передачу данных и формирует информацию о физической среде. В отличие от детального моделирования формы сигнала на уровне I/Q-отсчетов, в работе используется абстрактная автоматная модель. Ее задача состоит в том, чтобы передавать вышестоящим уровням конечный набор KPI (Key Performance Indicators) и событий деградации, пригодных для model checking.

PHY-уровень не выбирает глобальную политику управления ресурсами. Выбор режима выполняется на уровнях MAC (Medium Access Control) и SDN. PHY применяет полученные конфигурации, классифицирует их последствия и формирует отчеты для контроллера. Поэтому статус модели следует понимать как *абстрактную контрактную модель PHY для верификации реакций MAC/SDN на деградации ISAC-KPI*, а не как полную радиофизическую модель 6G-канала.

Обычные timed automata проверяют дискретную логику переходов во времени: достижимость, безопасность, отсутствие тупиков, соблюдение сроков и корректность синхронизации. Они не доказывают статистическое утверждение вида ``истинная вероятность обнаружения больше 0.95''. Вместо этого проверяется условие вида: если внешний PHY-estimator классифицировал Pd как `LOW`, то автомат A_SQ обязан за заданный срок перейти в состояние `ProbabilityLimited` и породить отчет `sensing_report!`.

Литературная база в этой редакции оставлена точечно: signaling design для ISAC [1], SensCAP и cooperative sensing [2, 3], ISAC-enabled beam management [4], теория timed automata [5], семантика запросов UPPAAL [6] и пример применения формальной проверки к сетевой логике [7]. Такой набор привязан к используемым утверждениям и не подменяет формальную часть библиографическим перечислением.

### 1.2 Архитектурное положение PHY

Рассматриваемая сеть задается иерархией:


```text
Service/Application
       |
       v
SDN control plane
       |
       v
MAC/resource scheduling
       |
       v
PHY abstraction layer
       |
       v
Physical environment and external PHY estimators
```


Сервисный уровень задает SLA: задержку, пропускную способность, надежность доставки, минимальную вероятность обнаружения, допустимую вероятность ложной тревоги, точность зондирования и допустимую давность информации. SDN-контроллер выбирает глобальную политику: разбиение ресурсов между связью и зондированием, маршрутизацию, восстановление и реконфигурацию. MAC-уровень реализует расписание радиоресурсов: плотность пилотов, распределение символов полезной нагрузки, мощность, MCS (Modulation and Coding Scheme) и команды формирования луча.

PHY является нижним измерительно-оценочным слоем. Он наблюдает радиосреду через внешние оценки, классифицирует состояние сигнала, канала, луча и sensing quality, после чего формирует события для MAC/SDN. Агрегирующий автомат A_PH получает не только отчет A_SQ, но и отдельные отчеты A_CH, A_SIG и A_BM. Это устраняет архитектурную неоднозначность, при которой A_PH использовал communication degradation, но формально не имел входов от communication-компонентов.


```text
Physical environment / estimators
        |             |             |
        v             v             v
      A_CH ------>  A_SIG ------>  A_SQ
        |             |             |
        v             v             v
      channel_     signal_      sensing_
      report!      report!      report!
        \             |             /
         \            |            /
          v           v           v
                    A_PH
                     |
                     v
              MAC and SDN control

A_BM receives beam commands from MAC/SDN
and publishes beam_report! to A_PH and A_SQ.
```


Сигнальные технологии OFDM, OTFS и AFDM не задаются отдельными состояниями PHY. Они являются значениями дискретной переменной W в автомате A_SIG. Состояния A_SIG описывают режим использования сигнала: pilot-based sensing, payload-assisted sensing, reconfiguration и degraded signal mode. Это предотвращает искусственное раздувание пространства состояний.

### 1.3 Базовая модель контрактного timed automaton

Каждый компонент PHY задается как контрактный временной автомат


```text
A_i=(L_i,l_i^0,C_i,V_i,E_i,Inv_i,In_i,Out_i,Ass_i,Gar_i),
```


где L_i --- конечное множество локаций, l_i^0 --- начальная локация, C_i --- часы, V_i --- конечные переменные, E_i --- переходы, Inv_i --- инварианты локаций, In_i и Out_i --- входные и выходные каналы, Ass_i --- assumptions контракта, Gar_i --- guarantees контракта.

Переход имеет вид


```text
e=(l,g,a,r,u,l'),
```


где l,l' in L_i, g --- guard, a in In_i U Out_i U tau --- действие синхронизации или внутреннее действие, r subseteq C_i --- множество сбрасываемых часов, u --- обновление конечных переменных. Переход разрешен, если истинны guard g и инвариант целевой локации после обновления u и сбросов r.

Композиция самого PHY-уровня содержит ровно пять автоматов:


```text
A_PHY=A_CH||A_SIG||A_BM||A_SQ||A_PH.
```


Здесь нет шестого PHY-компонента: A_ENV не относится к PHY, не моделирует дополнительный сетевой слой и не принимает решений за MAC/SDN. Это служебная абстрактная среда, используемая только для закрытия модели при model checking.

Закрытая проверяемая система задается как композиция PHY-модели и environment-stub:


```text
A_SYS=A_PHY||A_ENV,
```


где


```text
A_ENV = A_ENV_CH || A_ENV_TARGET || A_ENV_MAC || A_ENV_NET.
```


A_ENV кодирует assumptions о внешних входах: периодичность измерений, появление целей, допустимые команды MAC/SDN и доставку отчетов. Handshake-команды `x!`/`x?` синхронизируются бинарно по UPPAAL-подобной семантике, broadcast-отчеты и broadcast-события рассылаются всем готовым слушателям без перехвата, а внутренние tau-переходы выполняются локально. Общие переменные записи отчетов обновляются только отправителем соответствующего отчета; остальные автоматы читают их после broadcast-уведомления.

### 1.4 Абстракция непрерывной PHY-физики

#### Измерительный слой, конфигурация и конечные классы

Непрерывные величины не вычисляются внутри timed automata. Они принадлежат внешнему слою измерений, аналитических оценок или симуляции. Для связи используются


```text
SINR_c=(S_c)/(I_c+N_0B),
```


где S_c --- полезная мощность communication-сигнала, I_c --- communication-интерференция, N_0B --- шумовая мощность в полосе B.

Для зондирования используется отдельная величина


```text
SINR_s=(S_s)/(I_c-> s+I_self+I_mutual+N_s),
```


где S_s --- полезная sensing-компонента, I_c-> s --- интерференция communication-сигнала в sensing-тракте, I_self --- собственная интерференция, I_mutual --- взаимная интерференция между sensing-узлами, N_s --- шум sensing-приемника. Чтобы не смешивать физические измерения и дискретные настройки MAC/SDN, вход estimator-слоя разделяется на измерительный вектор и конфигурационный вектор:


```text
x_PHY^meas=(P_t,P_r,S_c,S_s,N_0,N_s,I_c,I_c-> s,I_self,I_mutual,L_p,sigma_tau,f_D,

B,f_c,Delta f,epsilon_b,p_mis,Omega_BM,Pd,Rfa,Acc_r,Acc_v,

CRB_R,CRB_v,CRB_theta,C_s,AoS_BS,AoS_CTRL,A_cov),

x_PHY^cfg=(MCS,W,rho_p,kappa_DRT,psi_cs,psi_ps,theta_b,G_b,n_B,

tau_SSB,T_SSB,T_PRS,N_RE^PRS,delta_PRS,S_t,S_f,T_s,gamma_det).
```


Если часть величин не измеряется напрямую, она считается производной от измеренных параметров внешнего estimator-слоя. В любом случае конечная автоматная модель получает не вещественные значения из x_PHY^meas и не сырые настройки из x_PHY^cfg, а только конечные классы из X_disc. Поэтому guards автоматов далее задаются по class-переменным, а формулы с SINR, Pd, Rfa, CRB, epsilon_b и Omega_BM остаются на стороне estimator/score-слоя.

#### Функция дискретизации

Формальный мост между PHY-оценками, конфигурацией и timed automata задается функцией


```text
alpha_PHY:X_meas x X_cfg-> X_disc.
```


Ее результатом является набор bounded int или enum-переменных:

Множество `X_disc` содержит классы, перечисленные ниже: коммуникационные классы, sensing-классы, beam-management классы и агрегированное состояние PHY.


Для communication SINR используется, например, следующая классификация:

| Условие | Значение `SINRClass` |
| --- | --- |
| `SINR_c < SINR_out` | `OUTAGE` |
| `SINR_out <= SINR_c < SINR_min` | `LOW` |
| `SINR_min <= SINR_c < SINR_high` | `OK` |
| `SINR_c >= SINR_high` | `HIGH` |


Аналогично задаются классы:

| Переменная | Допустимые классы |
| --- | --- |
| `BLERClass` | `OK`, `HIGH`, `CRITICAL` |
| `CQIClass` | `GOOD`, `LIMITED`, `BAD` |
| `IClass` | `OK`, `HIGH`, `CRITICAL` |
| `DopplerClass` | `OK`, `HIGH` |
| `DelaySpreadClass` | `OK`, `HIGH` |
| `PowerClass` | `OK`, `LOW`, `ABSENT` |
| `DRTClass` | `OK`, `BAD` |
| `PilotDensityClass` | `OK`, `LOW`, `FAILED` |
| `PayloadSenseClass` | `OK`, `LIMITED`, `FAILED` |
| `PRSClass` | `OK`, `LIMITED`, `FAILED` |
| `BeamErrorClass` | `LOCKABLE`, `UNSTABLE`, `CRITICAL` |
| `BlockageClass` | `NONE`, `SUSPECTED`, `CONFIRMED` |
| `PdClass` | `OK`, `LOW`, `FAILED` |
| `RfaClass` | `OK`, `HIGH`, `CRITICAL` |
| `AccClass` | `OK`, `LIMITED`, `FAILED` |
| `CRBClass` | `OK`, `LOOSE`, `UNUSABLE` |
| `AoSClass` | `FRESH`, `STALE`, `EXPIRED` |
| `CapClass` | `OK`, `LIMITED`, `FAILED` |
| `CoverageClass` | `OK`, `LIMITED`, `FAILED` |
| `ResourceShareClass` | `OK`, `LIMITED`, `STARVED` |
| `MisClass` | `OK`, `WARN`, `CRITICAL` |
| `BMOverheadClass` | `OK`, `HIGH`, `EXCESSIVE` |
| `ChannelClass` | `NOMINAL`, `INTERFERENCE_LIMITED`, `MOBILITY_LIMITED`, `MULTIPATH_LIMITED`, `BLOCKAGE`, `OUTAGE` |
| `SignalClass` | `NOMINAL`, `PILOT_BASED`, `PAYLOAD_ASSISTED`, `RECONFIGURING`, `LIMITED` |
| `BeamClass` | `SEARCH`, `TRACK`, `LOCKED`, `PREDICT`, `MISALIGNED`, `RECOVERING`, `HO_ASSIST`, `FAILED` |
| `SensingState` | `SensingQoSOk`, `ProbabilityLimited`, `FalseAlarmLimited`, `AccuracyLimited`, `FreshnessLimited`, `CoverageLimited`, `CapacityLimited`, `SensingFailure` |
| `PHYState` | `PHYNormal`, `PHYCommunicationDegraded`, `PHYSensingDegraded`, `PHYJointDegraded`, `PHYRecovery`, `PHYFailure` |


Для вероятностных и статистических KPI семантика следующая: Pd, Rfa, p_mis и CRB являются оценками estimator-слоя за окно наблюдения, а не вероятностями, доказанными внутри timed automata. Automata проверяют реакцию на классы этих оценок.

#### Soundness и консервативность абстракции

Абстракция выбирается как консервативная over-approximation относительно safety-свойств. Пограничные и неопределенные случаи относятся к худшему из соседних классов:


```text
alpha_PHY(x in boundary(C_good,C_bad))=C_bad.
```


Например, при SINR_c=SINR_min и наличии неопределенности измерения Delta SINR значение классифицируется как `LOW`, если нижняя граница доверительного интервала попадает ниже порога. Более строго это задается отношением конкретизации


```text
R subseteq (X_meas x X_cfg) x X_disc,
```


где (x,d) in R означает, что дискретный класс d покрывает все допустимые estimator-значения и неопределенности для x. Утверждение о сохранении safety-свойств далее не используется как доказанная теорема автоматически: оно предполагает корректную калибровку alpha_PHY, включение пограничных случаев в худшие классы и покрытие всех concrete transitions соответствующими abstract transitions относительно проверяемых atomic propositions. Если model checker находит counterexample, он может быть либо физически реализуемым сценарием, либо артефактом грубой over-approximation; поэтому counterexample должен проверяться обратным воспроизведением на estimator-слое или симуляторе.

### 1.5 Семантика assume--guarantee контрактов

Контракт автомата A_i трактуется не как описательная таблица, а как условное обязательство:


```text
A_imodels Ass_i=> Gar_i.
```


Если assumptions выполняются, автомат обязан выполнить guarantees в указанных временных границах. Если assumption нарушается, автомат публикует соответствующее диагностическое событие из семейства `contract_violation_ch!`, `contract_violation_sig!`, `contract_violation_bm!`, `contract_violation_sq!`, `contract_violation_ph!` и переходит в диагностическую локацию `ContractViolation_i`; guarantees после этого не используются как основание для доказательства свойств композиции.

Для исполнимой UPPAAL-подобной модели обозначения Ass_i и Gar_i не являются мета-переменными. Они реализуются как конкретные boolean-предикаты над clocks, class-переменными и состояниями environment-stub автоматов. Например, `Ass_CH` означает, что `ENV_CH` публикует `measure_tick!` не реже T_meas+J_meas, а все estimator-классы принадлежат объявленным enum-диапазонам; `Gar_CH` означает, что после каждого принятого `measure_tick?` до D_meas публикуется `channel_report!` и обновляется `ChannelClass`. Аналогично `Ass_SQ`, `Gar_SQ`, `Ass_PH` и `Gar_PH` задаются как проверяемые условия, а не как свободные математические ярлыки.

Композиция корректна, если гарантии поставщика закрывают assumptions потребителя:


```text
Gar_CH=> Ass_SQ, Gar_SIG=> Ass_SQ, Gar_BM=> Ass_SQ,

Gar_CH and Gar_SIG and Gar_BM and Gar_SQ=> Ass_PH, Gar_PH=> Ass_MAC/SDN.
```


| Автомат | Assumptions | Guarantees |
| --- | --- | --- |
| A_CH | Measurements P_r,I_c,sigma_tau,f_D,SINR_c обновляются не реже T_meas; estimator возвращает конечные классы. | За D_meas после `measure_tick?` публикуется `channel_report!`; ChannelClass выбирается по приоритету prio_CH. |
| A_SIG | MAC/SDN задают допустимые W,rho_p,MCS,kappa_DRT,psi_cs,psi_ps, а estimator возвращает `PilotDensityClass`, `DRTClass` и `PayloadSenseClass`. | За D_sig после конфигурационной команды публикуется `signal_report!`; нарушение DRT или BLER переводит автомат в `SignalLimited`. |
| A_BM | Команды луча и SSB/PRS-конфигурации конечны; `beam_cmd?` доставляется за D_cmd. | `beam_report!` публикуется в каждом окне; misalignment порождает `beam_misaligned!` за D_BM; неуспешное recovery при c_rec=D_BM порождает `beam_failure!`. |
| A_SQ | На вход поступают свежие `channel_report?`, `signal_report?` и `beam_report?`. | За D_sense публикуется `sensing_report!`; SensingState выбирается по приоритету prio_SQ. |
| A_PH | Все дочерние отчеты доставляются за D_child; clocks aos_bs, aos_ctrl корректно сбрасываются. | За D_report после деградации публикуется `phy_kpi_report!`; агрегированное состояние отражает communication и sensing classes. |


### 1.6 Operational semantics

#### Часы и resets

Набор clocks делится на локальные clocks дочерних автоматов и observer clocks. Минимальный набор для проверяемой модели:


| Clock | Смысл | Reset |
| --- | --- | --- |
| c_meas | возраст последнего channel measurement | `measure_tick?`, `channel_report!` |
| c_sig | длительность применения signal configuration | `waveform_config?`, `pilot_config?`, `signal_report!` |
| c_sense | время вычисления sensing state из входных классов | `channel_report?`, `signal_report?`, `beam_report?`, `sensing_report!` |
| c_report | возраст агрегированного PHY-отчета | `phy_kpi_report!` |
| c_rec | длительность beam recovery | вход в `BeamRecover` |
| c_ssb | длительность очередного SSB/beam-search окна | вход в `BeamSearch` или команда `ssb_burst_config?` |
| aos_bs | локальная давность sensing-информации на BS | `sensing_success!` |
| aos_ctrl | давность sensing-информации у SDN-контроллера | доставка отчета контроллеру |
| c_obs | clock observer-автоматов для deadlines | вход observer в состояние ожидания |


Основные инварианты:


```text
Inv(MeasurePending): c_meas<= T_meas+J_meas,

Inv(SignalReconfiguring): c_sig<= D_sig,

Inv(SensingEvaluating): c_sense<= D_sense,

Inv(PHYKpiReporting): c_report<= D_report,

Inv(BeamRecover): c_rec<= D_BM.
```


#### Синхронизационные каналы

Каналы разделяются на бинарные handshake-команды среды и broadcast-уведомления отчетов/событий. Это важно для UPPAAL-семантики: один обычный handshake `x!` синхронизируется только с одним `x?`, тогда как отчеты A_CH, A_SIG, A_BM, A_SQ и A_PH одновременно нужны нескольким потребителям и observer-автоматам. Поэтому report/event channels объявляются как `broadcast chan`; shared report variables обновляются отправителем перед публикацией, а получатели только читают их после broadcast-уведомления.


```text
Handshake input from environment, MAC and SDN:
  chan measure_tick, pilot_config, prs_config, ssb_burst_config;
  chan waveform_config, payload_sensing_config, beam_cmd;
  chan extra_ssb_cmd, handover_assist_cmd, power_cmd;
  chan sensing_mode_cmd, recovery_cmd, new_beam_confirmed;
  chan mac_report_delivered, controller_report_delivered;

Broadcast report notifications:
  broadcast chan channel_report, signal_report, beam_report;
  broadcast chan sensing_report, phy_kpi_report;

Broadcast degradation, recovery and diagnostic events:
  broadcast chan channel_degraded, signal_degraded, beam_misaligned;
  broadcast chan beam_failure, sensing_degraded, phy_outage;
  broadcast chan degradation_event, recovery_event, mobility_alert;
  broadcast chan multipath_alert, blockage_detected, beam_locked;
  broadcast chan beam_restored, handover_hint, sensing_failure;
  broadcast chan phy_failure, sensing_success, aos_ctrl_expired;
  broadcast chan recovery_start, target_detected;
  broadcast chan contract_violation_ch, contract_violation_sig;
  broadcast chan contract_violation_bm, contract_violation_sq;
  broadcast chan contract_violation_ph;
```


В таблицах ниже суффиксы `!`/`?` сохраняют направление использования канала. Для broadcast-канала запись `channel_report!` означает публикацию уведомления, которое не блокируется отсутствием получателя; запись `channel_report?` в A_SQ, A_PH или observer означает пассивное получение того же уведомления без перехвата события у другого потребителя. Для handshake-команд, напротив, `recovery_cmd!`/`recovery_cmd?` выполняются парно между environment-stub и соответствующим автоматом. A_SQ использует broadcast-отчеты A_CH, A_SIG и A_BM, поскольку sensing quality зависит от канала, сигнальной конфигурации и качества сопровождения луча.

#### Шаблон перехода

Типовой переход report-автомата имеет одно действие синхронизации. Если нужны и событие деградации, и отчет, используются две последовательные дуги через committed/urgent report-pending локацию либо одно событие `report!`, в payload которого уже закодирован обновленный класс. В основной спецификации выбран второй вариант: degradation flags являются shared boolean/class fields внутри отчета, а отдельные события `channel_degraded!`, `sensing_degraded!` используются только там, где они показаны как отдельные переходы. Типовой переход имеет вид


```text
(l, c<= D and class=k, report!, c, last_class:=k, l').
```


Если deadline истекает без публикации отчета, observer переходит в violation. Это важно: UPPAAL-запрос p --> q является unbounded leads-to и не задает дедлайн сам по себе. Bounded response задается отдельным clock или observer-автоматом.

#### Абстрактная среда и закрытая модель

Для проверки `A[] not deadlock`, reachability и deadline-свойств модель должна быть закрыта. Поэтому внешние входы задаются не неявно, а environment-stub автоматами с недетерминированным, но ограниченным поведением. Эти автоматы не входят в PHY-модель A_PHY; они только формализуют окружение, с которым PHY взаимодействует:


```text
ENV_CH:
  TickWait -- c_env <= T_meas + J_meas / measure_tick! --> TickWait
  update: estimator classes are refreshed before measure_tick!

ENV_TARGET:
  nondeterministically updates PRSClass, BeamErrorClass,
  BlockageClass and emits target_detected! when a target is visible.

ENV_MAC:
  emits pilot_config!, waveform_config!, recovery_cmd!,
  extra_ssb_cmd! and new_beam_confirmed! under admissible configs.

ENV_NET:
  delivers mac_report_delivered! and controller_report_delivered!
  within bounded network delay D_net.
```


Если эти автоматы не включены в композицию, спецификация трактуется как open-system contract, а свойства формулируются условно: они должны выполняться только при `Ass_ENV`, то есть при соблюдении ограничений на частоту измерений, доставку команд, обновление estimator-классов и сетевые задержки.

### 1.7 Автоматы PHY

#### Автомат канала A_CH

A_CH классифицирует состояние канала по дискретным классам, а не по конкурирующим вещественным условиям. Чтобы избежать недетерминизма при одновременном выполнении нескольких условий, вводится приоритет:


```text
prio_CH: Outage>Blockage>InterferenceLimited>

MobilityLimited>MultipathLimited>ChannelNominal.
```


Функция классификации задается явно:


```text
ChannelClass=highest_priority_CH(SINRClass,PowerClass,IClass,DopplerClass,DelaySpreadClass),
```


где `OUTAGE` выбирается при SINRClass=OUTAGE, `BLOCKAGE` --- при PowerClass in {LOW,ABSENT} без более приоритетного outage, `INTERFERENCE_LIMITED` --- при IClass in {HIGH,CRITICAL} без outage/blockage, далее по DopplerClass и DelaySpreadClass. Если estimator одновременно возвращает IClass=CRITICAL, PowerClass=LOW и SINRClass=OUTAGE, выбирается `OUTAGE`; вещественные I_c и P_r в guards автомата не используются.


| Локация | Guard с учетом prio_CH | Output / update |
| --- | --- | --- |
| `ChannelNominal` | SINRClass in {OK,HIGH} и нет более приоритетных нарушений | `channel_report!`, ChannelClass:=NOMINAL |
| `InterferenceLimited` | IClass in {HIGH,CRITICAL} и нет `Outage`, `Blockage` | `channel_report!`, ChannelClass:=INTERFERENCE_LIMITED |
| `MobilityLimited` | DopplerClass=HIGH и нет более приоритетных нарушений | `channel_report!`, ChannelClass:=MOBILITY_LIMITED |
| `MultipathLimited` | DelaySpreadClass=HIGH и нет более приоритетных нарушений | `channel_report!`, ChannelClass:=MULTIPATH_LIMITED |
| `Blockage` | PowerClass in {LOW,ABSENT} и SINRClass!=OUTAGE | `channel_report!`, ChannelClass:=BLOCKAGE |
| `Outage` | SINRClass=OUTAGE | `channel_report!`, ChannelClass:=OUTAGE |


Явная схема переходов E_CH отделяет прием измерения от публикации отчета:


```text
Any -- measure_tick? / c_meas := 0 --> MeasurePending
MeasurePending -- guard: ChannelClass' == NOMINAL
  sync: channel_report!
  update: ChannelClass := NOMINAL, channel_degraded_flag := false,
          c_meas := 0 --> ChannelNominal
MeasurePending -- guard: ChannelClass' == INTERFERENCE_LIMITED
  sync: channel_report!
  update: ChannelClass := INTERFERENCE_LIMITED,
          channel_degraded_flag := true, c_meas := 0 --> InterferenceLimited
MeasurePending -- guard: ChannelClass' == MOBILITY_LIMITED
  sync: channel_report!
  update: ChannelClass := MOBILITY_LIMITED,
          channel_degraded_flag := true, c_meas := 0 --> MobilityLimited
MeasurePending -- guard: ChannelClass' == MULTIPATH_LIMITED
  sync: channel_report!
  update: ChannelClass := MULTIPATH_LIMITED,
          channel_degraded_flag := true, c_meas := 0 --> MultipathLimited
MeasurePending -- guard: ChannelClass' == BLOCKAGE
  sync: channel_report!
  update: ChannelClass := BLOCKAGE,
          channel_degraded_flag := true, c_meas := 0 --> Blockage
MeasurePending -- guard: ChannelClass' == OUTAGE
  sync: channel_report!
  update: ChannelClass := OUTAGE,
          channel_degraded_flag := true, c_meas := 0 --> Outage
```


Здесь `ChannelClass'` обозначает результат функции `highest_priority_CH` на свежих class-входах. Если требуется отдельный observable alert, он отправляется отдельной последующей broadcast-дугой из соответствующей локации, например `Outage -- phy_outage! --> Outage`; она не совмещается с `channel_report!` на одном edge.

#### Автомат сигнальной конфигурации A_SIG

Переменная waveform остается конечной переменной


```text
W in {OFDM,OTFS,AFDM,SC,OTHER}.
```


Локации A_SIG описывают не waveform, а режим эксплуатации сигнала.


| Локация | Guard / invariant | Output / transition |
| --- | --- | --- |
| `SignalNominal` | BLERClass=OK, DRTClass=OK | `signal_report!`, SignalClass:=NOMINAL; при PilotDensityClass=OK возможен переход в `PilotBasedSensing` |
| `PilotBasedSensing` | PilotDensityClass=OK; c_sig<= D_sig | `signal_report!`, SignalClass:=PILOT_BASED; при PilotDensityClass=LOW и PayloadSenseClass!=FAILED переход в `PayloadAssistedSensing` |
| `PayloadAssistedSensing` | PayloadSenseClass!=FAILED | `signal_report!`, SignalClass:=PAYLOAD_ASSISTED; при DRTClass=BAD или BLERClass!=OK переход в `SignalLimited` |
| `SignalReconfiguring` | получена `waveform_config?` или `pilot_config?`; c_sig<= D_sig | `signal_report!`, SignalClass:=RECONFIGURING, c_sig:=0 |
| `SignalLimited` | BLERClass in {HIGH,CRITICAL} или DRTClass=BAD или PayloadSenseClass=FAILED | `signal_report!`, SignalClass:=LIMITED; ожидание реконфигурации MAC/SDN |


Явная схема переходов E_SIG:


```text
Any -- waveform_config? / c_sig := 0 --> SignalReconfiguring
Any -- pilot_config? / c_sig := 0 --> SignalReconfiguring
Any -- payload_sensing_config? / c_sig := 0 --> SignalReconfiguring
SignalReconfiguring -- c_sig <= D_sig
  sync: signal_report!
  update: SignalClass := RECONFIGURING, c_sig := 0 --> SignalNominal
SignalNominal -- PilotDensityClass == OK && BLERClass == OK && DRTClass == OK
  sync: signal_report!
  update: SignalClass := PILOT_BASED, c_sig := 0 --> PilotBasedSensing
PilotBasedSensing -- PilotDensityClass == LOW && PayloadSenseClass != FAILED
  sync: signal_report!
  update: SignalClass := PAYLOAD_ASSISTED, c_sig := 0 --> PayloadAssistedSensing
Any -- BLERClass in {HIGH, CRITICAL} || DRTClass == BAD
       || PayloadSenseClass == FAILED
  sync: signal_report!
  update: SignalClass := LIMITED, signal_degraded_flag := true,
          c_sig := 0 --> SignalLimited
SignalLimited -- waveform_config? / c_sig := 0 --> SignalReconfiguring
```


Отдельное событие `signal_degraded!` при необходимости выводится отдельной broadcast-дугой из `SignalLimited`; оно не совмещается с `signal_report!` на том же переходе.

#### Автомат beam management A_BM

A_BM описывает начальный поиск направления, сопровождение цели, фиксацию узкого луча, прогноз выхода цели за границу луча, восстановление направления и помощь handover. Он не вычисляет оптимальный beamforming vector; соответствующая оптимизация остается вне timed automata. Автомат получает конечные классы MisClass, BlockageClass, PRSClass и BMOverheadClass, публикуя события для MAC/SDN.

Классификация рассогласования задается как


```text
MisClass=
OK, p_mis<= p_mis^warn,

WARN, p_mis^warn<p_mis<= p_mis^max,

CRITICAL, p_mis>p_mis^max.
```


Класс накладных расходов получается из


```text
Omega_BM=min<=ft(1,(N_SSBT_SSB+N_PRST_PRS+T_ctrl+T_report)/(T_frame)).
```


Ключевая правка касается recovery-deadline. В локации `BeamRecover` действует инвариант c_rec<= D_BM. Поэтому переход в `BeamFailed` не может иметь guard c_rec>D_BM, так как такое состояние времени недостижимо. Корректный guard задается только через clock и классы:


```text
BeamRecover\xrightarrow{c_rec=D_BM and BeamErrorClass!=LOCKABLE and BlockageClass!=CONFIRMED / beam_failure!}BeamFailed.
```


| Локация | Guard / invariant | Output / transition |
| --- | --- | --- |
| `BeamSearch` | широкое сканирование SSB; c_ssb<= tau_SSB+J_SSB | при `target_detected?` и PRSClass!=FAILED: BeamClass:=TRACK, переход в `BeamTrack` |
| `BeamTrack` | PRS-оценка положения и скорости | при BeamErrorClass=LOCKABLE: BeamClass:=LOCKED, переход в `BeamLock`; при AccClass=FAILED или BeamErrorClass=CRITICAL: BeamClass:=MISALIGNED |
| `BeamLock` | MisClass=OK | `beam_report!`, BeamClass:=LOCKED; при MisClass=WARN или BlockageClass=SUSPECTED переход в `BeamPredict` |
| `BeamPredict` | прогноз выхода цели за границу луча или блокировки | при `extra_ssb_cmd?` переход в `BeamRecover`, c_rec:=0 |
| `BeamMisalign` | MisClass=CRITICAL или BeamErrorClass=CRITICAL | `beam_misaligned!`; затем переход в `BeamRecover`, c_rec:=0, BeamClass:=RECOVERING |
| `BeamRecover` | c_rec<= D_BM | success: BeamErrorClass=LOCKABLE, `beam_restored!`, `BeamLock`; blockage: BlockageClass=CONFIRMED, `handover_hint!`, `BeamHOAssist`; timeout: c_rec=D_BM, `beam_failure!` |
| `BeamHOAssist` | требуется помощь handover | при `new_beam_confirmed?` переход в `BeamTrack` |
| `BeamFailed` | recovery не завершен в срок | ожидание `recovery_cmd?` или новой MAC/SDN-конфигурации |


Явная схема переходов E_BM использует один sync на каждой дуге:


```text
Any -- beam_cmd? / BeamClass := SEARCH, c_ssb := 0 --> BeamSearch
BeamSearch -- target_detected? / target_seen := true --> BeamSearchSeen
BeamSearchSeen -- PRSClass != FAILED
  sync: beam_report!
  update: BeamClass := TRACK --> BeamTrack
BeamTrack -- BeamErrorClass == LOCKABLE
  sync: beam_report!
  update: BeamClass := LOCKED --> BeamLock
BeamTrack -- AccClass == FAILED || BeamErrorClass == CRITICAL
  sync: beam_report!
  update: BeamClass := MISALIGNED, beam_degraded_flag := true --> BeamMisalign
BeamLock -- MisClass == OK
  sync: beam_report!
  update: BeamClass := LOCKED --> BeamLock
BeamLock -- MisClass == WARN || BlockageClass == SUSPECTED
  sync: beam_report!
  update: BeamClass := PREDICT --> BeamPredict
BeamPredict -- extra_ssb_cmd? / c_rec := 0 --> BeamRecoveryStart
BeamRecoveryStart -- recovery_start!
  update: BeamClass := RECOVERING --> BeamRecover
BeamMisalign -- beam_misaligned! --> BeamRecoveryStart
BeamRecover -- BeamErrorClass == LOCKABLE && c_rec <= D_BM
  sync: beam_restored!
  update: BeamClass := LOCKED --> BeamLock
BeamRecover -- BlockageClass == CONFIRMED && c_rec <= D_BM
  sync: handover_hint!
  update: BeamClass := HO_ASSIST --> BeamHOAssist
BeamRecover -- c_rec == D_BM && BeamErrorClass != LOCKABLE
              && BlockageClass != CONFIRMED
  sync: beam_failure!
  update: BeamClass := FAILED --> BeamFailed
BeamHOAssist -- new_beam_confirmed? / BeamClass := TRACK --> BeamTrack
BeamFailed -- recovery_cmd? / BeamClass := RECOVERING,
              c_rec := 0 --> BeamRecover
```


Периодический `beam_report!` может публиковаться из `BeamRecover`, `BeamHOAssist` и `BeamFailed` отдельными self-loop переходами с единственным sync `beam_report!`; observer recovery слушает outcome-события `beam_restored!`, `handover_hint!` и `beam_failure!`, а не перехватывает `beam_report!`.

Контракт A_BM в проверяемой форме:


```text
Assume:
  n_B is finite;
  SSB/PRS configuration is admissible;
  beam_cmd? is delivered within D_cmd.

Guarantee:
  if MisClass = CRITICAL then beam_misaligned! is emitted within D_BM;
  if BeamRecover is entered then exactly one of
      beam_restored!, handover_hint!, beam_failure!
    is emitted not later than c_rec = D_BM;
  Omega_BM and BMOverheadClass are included in every beam_report!.
```


#### Автомат качества зондирования A_SQ

A_SQ получает `channel_report?`, `signal_report?` и `beam_report?`, затем вычисляет конечное состояние sensing quality. Все guards задаются по классам, а не по вещественным Pd, Rfa, Acc_r, Acc_v, CRB или C_s.


```text
prio_SQ: SensingFailure>FreshnessLimited>AccuracyLimited>

ProbabilityLimited>FalseAlarmLimited>CapacityLimited>

CoverageLimited>SensingQoSOk.
```


| Локация | Guard по классам | Output / update |
| --- | --- | --- |
| `SensingQoSOk` | все sensing-классы равны `OK`/`FRESH` и нет более приоритетных нарушений | `sensing_report!`, SensingState:=SensingQoSOk |
| `ProbabilityLimited` | PdClass=LOW и нет более приоритетных нарушений | `sensing_report!`, SensingState:=ProbabilityLimited |
| `FalseAlarmLimited` | RfaClass=HIGH и нет более приоритетных нарушений | `sensing_report!`, SensingState:=FalseAlarmLimited |
| `AccuracyLimited` | AccClass=LIMITED или CRBClass=LOOSE | `sensing_report!`, SensingState:=AccuracyLimited |
| `FreshnessLimited` | AoSClass=STALE и нет `SensingFailure` | `sensing_report!`, SensingState:=FreshnessLimited |
| `CoverageLimited` | CoverageClass=LIMITED и нет более приоритетных нарушений | `sensing_report!`, SensingState:=CoverageLimited |
| `CapacityLimited` | CapClass=LIMITED и нет более приоритетных нарушений | `sensing_report!`, SensingState:=CapacityLimited |
| `SensingFailure` | PdClass=FAILED или RfaClass=CRITICAL или AccClass=FAILED или CRBClass=UNUSABLE или AoSClass=EXPIRED или CapClass=FAILED или CoverageClass=FAILED или BeamClass=FAILED | `sensing_report!`, SensingState:=SensingFailure |


Детерминированность классификации проверяется счетчиком enabled-guards или явной функцией:


```text
SensingState=highest_priority_SQ(PdClass,RfaClass,AccClass,CRBClass,

AoSClass,CapClass,CoverageClass,BeamClass).
```


Явная схема переходов E_SQ:


```text
Idle -- channel_report? / input_changed := true, c_sense := 0 --> SensingEvaluating
Idle -- signal_report?  / input_changed := true, c_sense := 0 --> SensingEvaluating
Idle -- beam_report?    / input_changed := true, c_sense := 0 --> SensingEvaluating
SensingEvaluating -- guard: SensingState' == SensingQoSOk
  sync: sensing_report!
  update: SensingState := SensingQoSOk,
          sensing_degraded_flag := false, c_sense := 0 --> SensingQoSOk
SensingEvaluating -- guard: SensingState' == ProbabilityLimited
  sync: sensing_report!
  update: SensingState := ProbabilityLimited,
          sensing_degraded_flag := true, c_sense := 0 --> ProbabilityLimited
SensingEvaluating -- guard: SensingState' == FalseAlarmLimited
  sync: sensing_report!
  update: SensingState := FalseAlarmLimited,
          sensing_degraded_flag := true, c_sense := 0 --> FalseAlarmLimited
SensingEvaluating -- guard: SensingState' == AccuracyLimited
  sync: sensing_report!
  update: SensingState := AccuracyLimited,
          sensing_degraded_flag := true, c_sense := 0 --> AccuracyLimited
SensingEvaluating -- guard: SensingState' == FreshnessLimited
  sync: sensing_report!
  update: SensingState := FreshnessLimited,
          sensing_degraded_flag := true, c_sense := 0 --> FreshnessLimited
SensingEvaluating -- guard: SensingState' == CoverageLimited
  sync: sensing_report!
  update: SensingState := CoverageLimited,
          sensing_degraded_flag := true, c_sense := 0 --> CoverageLimited
SensingEvaluating -- guard: SensingState' == CapacityLimited
  sync: sensing_report!
  update: SensingState := CapacityLimited,
          sensing_degraded_flag := true, c_sense := 0 --> CapacityLimited
SensingEvaluating -- guard: SensingState' == SensingFailure
  sync: sensing_report!
  update: SensingState := SensingFailure,
          sensing_failure_flag := true, c_sense := 0 --> SensingFailure
```


Здесь `SensingState'` --- результат функции `highest_priority_SQ`. Broadcast-события `sensing_degraded!` и `sensing_failure!` могут публиковаться отдельными self-loop переходами после обновления флагов; основной отчет остается единственным sync на report-edge.

#### Агрегирующий автомат A_PH

A_PH поддерживает две независимые булевы переменные:


```text
comm_ok =
  ChannelClass in {NOMINAL, INTERFERENCE_LIMITED, MOBILITY_LIMITED, MULTIPATH_LIMITED}
  and SignalClass != LIMITED
  and BeamClass not in {FAILED, MISALIGNED}

sensing_qos_ok =
  SensingState == SensingQoSOk
```


Эти переменные обновляются только после broadcast-уведомлений `channel_report?`, `signal_report?`, `beam_report?` и `sensing_report?`. Агрегированная переменная `PHYState` обновляется только A_PH, чтобы остальные автоматы читали единый источник истины.


| Локация | Guard | Output / transition |
| --- | --- | --- |
| `PHYNormal` | comm_ok and sensing_qos_ok | `phy_kpi_report!`, PHYState:=PHYNormal |
| `PHYCommunicationDegraded` | not comm_ok and sensing_qos_ok | `phy_kpi_report!`, PHYState:=PHYCommunicationDegraded |
| `PHYSensingDegraded` | comm_ok and not sensing_qos_ok | `phy_kpi_report!`, PHYState:=PHYSensingDegraded |
| `PHYJointDegraded` | not comm_ok and not sensing_qos_ok | `phy_kpi_report!`, PHYState:=PHYJointDegraded |
| `PHYKpiReporting` | истек T_report или получено событие деградации; c_report<= D_report | публикация `phy_kpi_report!`, c_report:=0 |
| `PHYRecovery` | получена `recovery_cmd?` | PHYState:=PHYRecovery; при восстановлении классов переход в `PHYNormal`; иначе deadline observer фиксирует нарушение |
| `PHYFailure` | критический отказ канала, луча или sensing-функции | `phy_failure!`, PHYState:=PHYFailure; ожидание внешней реконфигурации |


Явная схема переходов E_PH:


```text
Any -- channel_report? / child_update := true, c_report := 0 --> PHYKpiReporting
Any -- signal_report?  / child_update := true, c_report := 0 --> PHYKpiReporting
Any -- beam_report?    / child_update := true, c_report := 0 --> PHYKpiReporting
Any -- sensing_report? / child_update := true, c_report := 0 --> PHYKpiReporting
PHYKpiReporting -- comm_ok && sensing_qos_ok && c_report <= D_report
  sync: phy_kpi_report!
  update: PHYState := PHYNormal, c_report := 0 --> PHYNormal
PHYKpiReporting -- !comm_ok && sensing_qos_ok && c_report <= D_report
  sync: phy_kpi_report!
  update: PHYState := PHYCommunicationDegraded,
          degradation_flag := true, c_report := 0 --> PHYCommunicationDegraded
PHYKpiReporting -- comm_ok && !sensing_qos_ok && c_report <= D_report
  sync: phy_kpi_report!
  update: PHYState := PHYSensingDegraded,
          degradation_flag := true, c_report := 0 --> PHYSensingDegraded
PHYKpiReporting -- !comm_ok && !sensing_qos_ok && c_report <= D_report
  sync: phy_kpi_report!
  update: PHYState := PHYJointDegraded,
          degradation_flag := true, c_report := 0 --> PHYJointDegraded
Any -- recovery_cmd? / PHYState := PHYRecovery --> PHYRecovery
Any -- ChannelClass == OUTAGE || BeamClass == FAILED
       || SensingState == SensingFailure
  sync: phy_failure!
  update: PHYState := PHYFailure --> PHYFailure
```


Если нужен отдельный `degradation_event!`, он публикуется дополнительным broadcast self-loop после установки `degradation_flag`; основной KPI-отчет остается единственным sync на переходе A_PH.

### 1.8 SensCAP, capacity и freshness

SensCAP трактуется как системная метрика, включающая sensing probability, sensing accuracy и sensing capacity [2, 3]. В автоматной модели эти величины не используются как непрерывные guards напрямую; они предварительно переводятся в классы.

Sensing probability задается estimator-слоем как


```text
Pd(R_fa)=(N_det)/(N), R_fa<= R_fa^max.
```


Для CFAR-приближения порог может быть записан как


```text
S_thres=N_ru<=ft((R_fa)^-1/N_ru-1)p_n.
```


Точность зондирования задается через условия


```text
\Pr(Delta r<= l_a)>= q, \Pr(Delta v<= v_a)>= q_v,
```


а CRB сохраняется как теоретическая нижняя граница ошибки


```text
\mathbfCRB=(CRB_R,CRB_v,CRB_theta).
```


Формула sensing capacity должна явно содержать временное окно и требования качества:


```text
C_s(Q_s,T_0)=(N^*(Q_s,T_0))/(A),
```


где A --- площадь зоны зондирования, T_0 --- окно оценки, Q_s=(l_a,v_a,Pd_min,Rfa_max,q,q_v,T_0), а N^*(Q_s,T_0) --- максимальное число целей, для которого выполняются требования


```text
Pd(R_fa^max)>= Pd_min,

\Pr(Delta r<= l_a)>= q,

\Pr(Delta v<= v_a)>= q_v.
```


Доля ресурсов зондирования задается как


```text
u_s=(T_s)/(T_0), 0<u_s<= 1.
```


В timed automata используются только CapClass и ResourceShareClass, например `OK`, `LIMITED`, `FAILED`.

AoS (Age of Sensing) разделяется на локальную и контроллерную метрики:


```text
AoS_BS(t)=t-t_sense^last,

AoS_CTRL(t)=t-t_ctrl^last.
```


AoS_BS сбрасывается после `sensing_success!`, а AoS_CTRL --- после `controller_report_delivered?`. Поэтому AoS_CTRL может быть больше AoS_BS при перегрузке, изменении маршрута или задержке обработки на edge/cloud-узлах. Для SDN-контроллера именно AoS_CTRL является основной freshness-метрикой.

### 1.9 Интерфейс отчетов и PHY-компоненты штрафа

Минимальный пакет KPI публикуется как сочетание классов и опциональных оцененных численных значений. Для model checking существенны классы; численные значения могут использоваться внешним SDN-оптимизатором:


```text
{
  SINRClass, BLERClass, CQIClass, IClass, DopplerClass,
  DelaySpreadClass, PowerClass, DRTClass, PilotDensityClass,
  PayloadSenseClass, PRSClass, BeamErrorClass, BlockageClass,
  PdClass, RfaClass, AccClass, CRBClass,
  BeamClass, MisClass, BMOverheadClass,
  AoSClass, CoverageClass, CapClass, ResourceShareClass,
  ChannelClass, SignalClass, SensingState, PHYState
}
```


Если SDN-контроллеру требуется численный score, PHY может передавать нормированные компоненты нарушения контракта:


```text
Pi_SINR=max<=ft(0,(SINR_min-SINR_c)/(SINR_min)),
Pi_BLER=max<=ft(0,(BLER-BLER_max)/(BLER_max)),

Pi_Pd=max<=ft(0,(Pd_min-Pd)/(Pd_min)),
Pi_Rfa=max<=ft(0,(Rfa-Rfa_max)/(Rfa_max)),

Pi_Acc=max<=ft(0,(Acc_r-l_a)/(l_a))+max<=ft(0,(Acc_v-v_a)/(v_a)),
Pi_AoS=max<=ft(0,(AoS_CTRL-AoS_max)/(AoS_max)),

Pi_Cap=max<=ft(0,(C_s^min-C_s)/(C_s^min)).
```


Для beam management:


```text
Pi_BM=max<=ft(0,(epsilon_b-epsilon_max)/(epsilon_max))+max<=ft(0,(p_mis-p_mis^max)/(p_mis^max))+max<=ft(0,(Omega_BM-Omega_BM^max)/(Omega_BM^max)).
```


Агрегированный score


```text
Pi_PHY=sum_i w_iPi_i,
w_i>= 0,
sum_iw_i=1
```


не является частью обычного timed automaton, если используется как накопленная стоимость. Его следует трактовать либо как внешний SDN-score, вычисляемый после публикации отчета, либо как расширение модели до priced/weighted timed automata. В базовой TA-модели проверяются классы нарушений и bounded реакции, а не оптимальность Pi_PHY.

### 1.10 Верификационные свойства и observer-автоматы

В UPPAAL-подобной нотации можно задавать reachability и safety-свойства напрямую, но bounded response следует выражать observer-автоматами. Unbounded leads-to p --> q говорит только, что из p когда-нибудь следует q; он не задает срок D. В этой спецификации deadline трактуется как включительный: событие на границе c=D еще допустимо, а нарушение возникает только при c>D. Поэтому observer-локации ожидания не имеют invariant c<= D; иначе состояние c>D было бы недостижимо. Невмешательство observers обеспечивается тем, что наблюдаемые report/outcome-события объявлены как `broadcast chan`.

Базовые свойства:


```text
A[] not deadlock
E<> A_PH.PHYNormal
E<> A_PH.PHYSensingDegraded
E<> A_PH.PHYCommunicationDegraded
E<> A_PH.PHYJointDegraded
A[] (A_PH.PHYNormal imply (comm_ok && sensing_qos_ok))
```


Observer для bounded report после sensing degradation:


```text
locations: Idle, WaitReport, Violation
clock: c_obs

Idle -- sensing_degraded? / c_obs := 0 --> WaitReport
WaitReport -- phy_kpi_report? guard c_obs <= D_report --> Idle
WaitReport -- c_obs > D_report --> Violation

query: A[] not ObsSenseReport.Violation
```


Observer для freshness:


```text
Idle -- aos_ctrl_expired? / c_obs := 0 --> WaitFreshnessLimited
WaitFreshnessLimited -- sensing_report? --> Idle
  guard: c_obs <= D_sense && SensingState == FreshnessLimited
WaitFreshnessLimited -- c_obs > D_sense --> Violation

query: A[] not ObsFreshness.Violation
```


Observer для beam recovery:


```text
Idle -- recovery_start? / c_obs := 0 --> WaitBeamOutcome
WaitBeamOutcome -- beam_restored? guard c_obs <= D_BM --> Idle
WaitBeamOutcome -- handover_hint? guard c_obs <= D_BM --> Idle
WaitBeamOutcome -- beam_failure? guard c_obs <= D_BM --> Idle
WaitBeamOutcome -- c_obs > D_BM --> Violation

query: A[] not ObsBeamRecovery.Violation
```


С учетом исправленного перехода c_rec=D_BM в `BeamFailed` также допустимо проверять локальный invariant:


```text
A[] (A_BM.BeamRecover imply c_rec <= D_BM)
```


но это не заменяет проверку того, что recovery действительно завершается одним из разрешенных исходов.

Детерминированность классификаций проверяется через счетчики enabled-guards:


```text
A[] (ch_enabled_count <= 1)
A[] (sq_enabled_count <= 1)
```


или доказывается синтаксически через приоритетные функции prio_CH и prio_SQ.

Согласованность assume--guarantee контрактов проверяется как отсутствие violation при выполнении конкретных boolean-предикатов. В UPPAAL-модели эти предикаты задаются как функции над состояниями и классами, например `ass_ch()`, `gar_ch()`, `ass_sq()` и `ass_ph()`:


```text
bool ass_ch()  = ENV_CH.TimingOk && classes_in_range_ch;
bool gar_ch()  = A_CH.Reported && ChannelClass in CHANNEL_ENUM;
bool ass_sig() = ENV_MAC.ConfigAdmissible && classes_in_range_sig;
bool gar_sig() = A_SIG.Reported && SignalClass in SIGNAL_ENUM;
bool ass_bm()  = ENV_MAC.BeamCmdAdmissible && classes_in_range_bm;
bool gar_bm()  = A_BM.Reported && BeamClass in BEAM_ENUM;
bool ass_sq()  = fresh_child_reports && gar_ch() && gar_sig() && gar_bm();
bool gar_sq()  = A_SQ.Reported && SensingState in SENSING_ENUM;
bool ass_ph()  = gar_ch() && gar_sig() && gar_bm() && gar_sq();

A[] (ass_ch()  imply not A_CH.ContractViolation_CH)
A[] (ass_sig() imply not A_SIG.ContractViolation_SIG)
A[] (ass_bm()  imply not A_BM.ContractViolation_BM)
A[] (ass_sq()  imply not A_SQ.ContractViolation_SQ)
A[] (ass_ph()  imply not A_PH.ContractViolation_PH)
```


### 1.11 Ограничения применимости

Предложенная формализация намеренно отделяет physical estimation от automata logic. Estimator или радиосимулятор оценивает SINR, BLER, Pd, Rfa, CRB, p_mis и Omega_BM; timed automata получают конечные классы и проверяют своевременную реакцию. Если требуется доказывать распределения задержек, частоты отказов, среднюю стоимость или вероятность достижения состояния, модель должна быть расширена до probabilistic, stochastic или priced timed automata.

Качество результата зависит от soundness функции alpha_PHY. Пороговые значения должны выбираться из link budget, measurement confidence intervals, требований SLA или калибровочного симулятора. Грубая дискретизация может давать ложные counterexamples; слишком оптимистичная дискретизация может нарушить сохранение safety-свойств. Поэтому все границы классов в safety-критичных условиях относятся к худшему классу, а найденные counterexamples проверяются на физическую реализуемость вне model checker.

### 1.12 Заключение

PHY-уровень в SDN-управляемой ISAC-сети целесообразно задавать как композицию аппроксимированных контрактных timed automata. В строгой редакции модель содержит явную функцию alpha_PHY, конечные enum-классы для continuous и probabilistic KPI, assume--guarantee семантику, синхронизационные каналы, clocks, guards, resets, invariants, приоритеты классификации и observer-автоматы для deadlines.

Состояния автоматов отражают не детальную радиофизику, а проверяемые классы поведения: состояние канала, сигнальную конфигурацию, состояние луча, качество зондирования и агрегированное состояние PHY. Такая постановка честно ограничивает область применимости timed automata и одновременно делает модель полезной для формальной проверки SDN-управляемого поведения 6G ISAC-сети: MAC/SDN получает не произвольную таксономию PHY-состояний, а синхронизированную контрактную модель с проверяемыми сроками реакции.

## 2. Положение уровней выше PHY в общей иерархии

Ниже PHY-уровень рассматривается как нижний контрактный компонент, который сообщает дискретизированные классы состояния радиоканала, beam management (управление лучом), sensing quality (качество радиозондирования) и freshness (свежесть данных). Остальные уровни не пересчитывают физические метрики напрямую. Они работают с конечными классами, полученными от PHY и MAC, и принимают решения в пределах контрактов.

Базовая композиция уровней задается как:

```text
A_TOTAL = A_SVC || A_SDN || A_MAC || A_PHY || A_ENV.
```

A_ENV (автомат среды) не следует дублировать как четыре независимых автомата с разной логикой. Корректнее задавать один общий внешний автомат среды, разложенный на компоненты:

```text
A_ENV = A_ENV_PHY || A_ENV_MAC || A_ENV_SDN || A_ENV_SVC || A_ENV_FAULT.
```

При модульной проверке каждый уровень может использовать локальную проекцию этой среды:

```text
E_PHY = pi_PHY(A_ENV),
E_MAC = pi_MAC(A_ENV),
E_SDN = pi_SDN(A_ENV),
E_SVC = pi_SVC(A_ENV).
```

Эти проекции являются не разными “реальностями”, а разными наблюдаемыми интерфейсами одного и того же внешнего процесса. Например, blockage (блокировка радиолинии) на PHY виден как CH_BLOCKED или BM_LOST, на MAC — как падение доступного ресурса или рост очереди, на SDN/RIC — как риск реконфигурации или деградация SLA, а на service layer — как warning или violation. Если сделать независимый A_ENV для каждого уровня, можно случайно получить несогласованность: PHY считает канал восстановленным, MAC продолжает видеть перегрузку от того же события, а SDN уже запустил recovery по другой причине. Поэтому в полной композиции среда должна быть общей, а при локальной верификации — заменяться согласованной проекцией.

A_PHY (автомат физического уровня) уже задан в предыдущем разделе; A_MAC (автомат MAC/resource scheduling) отвечает за локальное планирование радиоресурсов и буферов; A_SDN (автомат SDN control plane/RIC) задает централизованную политику, правила маршрутизации, реконфигурацию и реакцию на деградации; A_SVC (автомат application/service layer) задает требования сервиса и контролирует выполнение SLA (service-level agreement, соглашение об уровне обслуживания). A_ENV моделирует внешние события: изменение канала, трафика, отказов, перегрузки, мобильности, сервисного спроса и деградации sensing (радиозондирования).

Контрактная связность уровней имеет вид:

```text
Gar_SVC  -> Ass_SDN,
Gar_SDN  -> Ass_MAC,
Gar_MAC  -> Ass_PHY,
Gar_PHY  -> Ass_MAC and Ass_SDN,
Gar_MAC  -> Ass_SDN,
Gar_SDN  -> Ass_SVC.
```

Это означает, что каждый уровень передает выше и ниже не непрерывную физическую модель, а конечный набор наблюдаемых классов, команд и подтверждений. Такой подход согласуется с целью статьи: формализовать SDN-управляемую ISAC-сеть через иерархические контрактные timed automata (временные автоматы), а не строить радиофизический симулятор. Базовая семантика времени опирается на теорию timed automata [5], а ограниченная реконфигурация может трактоваться в терминах dynamic timed automata (динамических временных автоматов) [8].

## 3. MAC / Resource Scheduling Layer

### 3.1 Назначение и границы уровня

MAC / Resource Scheduling layer (уровень доступа к среде и планирования ресурсов) связывает PHY-уровень с SDN-контроллером. Его задача состоит не в глобальной оптимизации сети, а в локальном принятии решений о выделении радиоресурсов, управлении очередями, обработке перегрузки и передаче команд на PHY. В ISAC-сети этот уровень дополнительно должен учитывать конфликт между communication (передача данных) и sensing (радиозондирование): одни и те же временно-частотные, beamforming (формирование луча) и энергетические ресурсы могут быть нужны для обеих функций. Разделение локального планирования и централизованной политики соответствует общей SDN-архитектуре с разделением data plane (уровня пересылки) и control plane (уровня управления) [9], [10].

Граница уровня задается следующим образом:

- MAC принимает от PHY дискретные отчеты о канале, луче, sensing quality и freshness.
- MAC принимает от SDN policy command (политическую команду управления), но не выбирает глобальную сетевую политику самостоятельно.
- MAC выдает PHY команды resource allocation (выделение ресурса), beam update (обновление луча), sensing boost (усиление режима радиозондирования) или constrained mode (ограниченный режим).
- MAC сообщает SDN агрегированное состояние очередей, потерь, задержек и дефицита ресурсов.

Следовательно, MAC не должен подменять SDN-контроллер. Если в модели MAC сам принимает решения о rerouting (перемаршрутизации), slice migration (переносе сетевого среза) или глобальном recovery (восстановлении), это смешивает уровни и ослабляет формализацию.

### 3.2 Дискретная абстракция MAC

Непрерывные измерения задержки, загрузки, размера очереди и пропускной способности сводятся к конечному состоянию через отображение:

```text
alpha_MAC : X_MAC_meas x X_MAC_cfg -> X_MAC_disc.
```

Здесь X_MAC_meas содержит измеряемые величины: queue length (длина очереди), buffer occupancy (заполнение буфера), packet loss (потери пакетов), scheduling delay (задержка планирования), radio resource utilization (использование радиоресурса), HARQ/NACK statistics (статистика повторных передач и отрицательных подтверждений). X_MAC_cfg содержит текущую конфигурацию: размер окна планирования, ограничения политики SDN, приоритеты сервисов, допустимую долю ресурса для sensing и communication.

Конечное множество классов можно задать так:

| Переменная | Значения | Смысл |
|---|---|---|
| QueueClass | Q_EMPTY, Q_LOW, Q_MED, Q_HIGH, Q_CRIT | Класс длины очереди |
| BufferClass | B_SAFE, B_WARN, B_OVERFLOW | Класс заполнения буфера |
| DelayClass | D_OK, D_WARN, D_DEADLINE_RISK, D_VIOLATED | Класс задержки планирования |
| DropClass | DROP_NONE, DROP_LOW, DROP_HIGH | Класс потерь пакетов |
| ResourceClass | RES_FREE, RES_BALANCED, RES_TIGHT, RES_EXHAUSTED | Класс доступности радиоресурсов |
| SensingDemand | SENS_NOMINAL, SENS_BOOST_REQ, SENS_CRITICAL | Потребность sensing |
| CommDemand | COMM_NOMINAL, COMM_HIGH, COMM_CRITICAL | Потребность передачи данных |
| ScheduleMode | SCH_IDLE, SCH_COMM, SCH_SENS, SCH_JOINT, SCH_CONSTRAINED | Режим планирования |

Эти классы не претендуют на точное описание радиофизики. Они задают наблюдаемую дискретную поверхность, на которой проверяются достижимость, дедлайны и отсутствие недопустимых состояний.

### 3.3 Композиция автоматов MAC

MAC-уровень удобно представить как параллельную композицию:

```text
A_MAC = A_SCH || A_Q || A_BUF || A_RSRC || A_MAC_AGG.
```

Здесь A_SCH (scheduler automaton, автомат планировщика) выбирает режим распределения ресурса; A_Q (queue automaton, автомат очереди) отслеживает классы очередей; A_BUF (buffer automaton, автомат буфера) отслеживает риск переполнения; A_RSRC (resource automaton, автомат ресурса) контролирует допустимость выделения ресурса между communication и sensing; A_MAC_AGG (aggregate reporter, автомат агрегированного отчета) формирует отчет для SDN.

| Автомат | Основные состояния | Ответственность |
|---|---|---|
| A_SCH | Idle, CollectKPI, SelectMode, ApplySchedule, WaitPHYAck, ScheduleFailure | Выбор и применение локального режима планирования |
| A_Q | QueueNormal, QueueWarning, QueueCritical, QueueDraining | Контроль очередей и риска нарушения задержки |
| A_BUF | BufferSafe, BufferWarning, BufferOverflow | Контроль переполнения буфера |
| A_RSRC | ResourceAvailable, ResourceTight, ResourceConflict, ResourceExhausted | Проверка совместимости sensing и communication |
| A_MAC_AGG | ReportIdle, ReportBuild, ReportSent, ReportStale | Формирование отчета для SDN |

### 3.4 Каналы взаимодействия

Интерфейс MAC задается через синхронизационные каналы и конечные переменные.

Входные каналы:

- phy_kpi_report? — отчет PHY о канале, beam quality (качестве луча), sensing quality и freshness;
- sdn_policy_cmd? — команда политики от SDN/RIC;
- service_priority? — приоритет, переданный через SDN от сервисного уровня;
- mac_tick? — событие начала окна планирования;
- phy_ack? — подтверждение применения команды на PHY.

Выходные каналы:

- mac_schedule_cmd! — команда распределения ресурса на PHY;
- beam_update_cmd! — команда обновления луча;
- sensing_boost_cmd! — команда усиления sensing;
- constrained_mode_cmd! — команда ограниченного режима;
- mac_report! — агрегированный отчет для SDN;
- resource_reject! — явный отказ при невозможности выполнить требование.

### 3.5 Контракт MAC

Контракт MAC задается парой assumption/guarantee (предположение/гарантия):

```text
C_MAC = (Ass_MAC, Gar_MAC).
```

Предположения Ass_MAC:

- PHY передает отчеты не реже заданного периода D_phy_report или явно сообщает ReportStale.
- SDN-команда принадлежит конечному допустимому множеству политик.
- Сервисный приоритет уже проверен SDN и не противоречит текущей политике допуска.
- Значения QueueClass, ResourceClass и DelayClass принадлежат конечным доменам alpha_MAC.

Гарантии Gar_MAC:

- Если QueueClass = Q_CRIT или DelayClass = D_DEADLINE_RISK, MAC обязан в течение D_sched перейти в режим SCH_COMM, SCH_JOINT, SCH_CONSTRAINED или выдать resource_reject!.
- Если SensingDemand = SENS_CRITICAL и политика SDN разрешает sensing priority (приоритет радиозондирования), MAC обязан в течение D_sched выдать sensing_boost_cmd! или constrained_mode_cmd!.
- Если ResourceClass = RES_EXHAUSTED, MAC не должен молча принимать новый ресурсный запрос; допустимы только explicit reject (явный отказ), constrained mode или запрос SDN-перепланирования.
- Если BufferClass = B_OVERFLOW, MAC обязан сформировать mac_report! с причиной overflow, а не скрывать потерю пакетов внутри PHY.
- Любая команда PHY должна получить phy_ack? до D_phy_ack или перейти в ScheduleFailure.

### 3.6 Переходы A_SCH

Схематически поведение планировщика задается так:

```text
Idle --mac_tick?--> CollectKPI
CollectKPI --fresh_kpi and policy_ok--> SelectMode
CollectKPI --stale_kpi--> ConstrainedMode
SelectMode --resource_ok--> ApplySchedule
SelectMode --resource_conflict and sensing_priority--> ApplySensingBoost
SelectMode --resource_conflict and comm_priority--> ApplyCommPriority
SelectMode --resource_exhausted--> RejectOrAskSDN
ApplySchedule --mac_schedule_cmd!--> WaitPHYAck
WaitPHYAck --phy_ack? before D_phy_ack--> Idle
WaitPHYAck --timeout--> ScheduleFailure
ScheduleFailure --mac_report!--> Idle
```

Здесь важно, что MAC не вычисляет новую глобальную сетевую конфигурацию. Он либо применяет локально допустимый режим, либо возвращает SDN отчет о невозможности выполнить контракт при текущих ограничениях.

### 3.7 Временные переменные MAC

Для проверки дедлайнов вводятся часы:

| Часы | Назначение |
|---|---|
| c_sched | Время от начала окна планирования до выбора режима |
| c_phy_ack | Время ожидания подтверждения от PHY |
| c_queue | Время пребывания в критическом классе очереди |
| c_buf | Время пребывания в состоянии переполнения буфера |
| c_report | Возраст последнего MAC-отчета для SDN |

Типовые инварианты:

```text
CollectKPI:       c_sched <= D_collect
SelectMode:       c_sched <= D_sched
WaitPHYAck:       c_phy_ack <= D_phy_ack
QueueCritical:    c_queue <= D_queue_crit
ReportBuild:      c_report <= D_mac_report
```

### 3.8 Верификационные свойства MAC

Для MAC-уровня проверяются свойства safety (безопасность состояний), bounded response (ограниченный отклик) и absence of deadlock (отсутствие тупика).

Примеры свойств:

```text
A[] not deadlock
A[] not (BufferOverflow and no mac_report_pending)
A[] (ResourceClass == RES_EXHAUSTED imply not silent_accept)
A[] (WaitPHYAck imply c_phy_ack <= D_phy_ack)
QueueCritical --> eventually_within(D_queue_crit) (QueueDraining or resource_reject or mac_report_sent)
SENS_CRITICAL --> eventually_within(D_sched) (sensing_boost_cmd or constrained_mode_cmd or resource_reject)
```

Если требуется оценить частоту потерь, среднюю задержку или вероятность переполнения, обычного timed automaton недостаточно. Для этого нужна стохастическая или priced extension (расширение с вероятностями или стоимостью). В основной статье достаточно указать, что такие метрики не выводятся из автомата напрямую, а входят как внешние классы alpha_MAC.

## 4. SDN Control Plane / RAN Intelligent Controller Layer

### 4.1 Назначение и границы уровня

SDN Control Plane / RAN Intelligent Controller (уровень SDN-управления и интеллектуального контроллера радиодоступа) является центральным уровнем принятия политики. Он получает отчеты от PHY и MAC, принимает сервисные требования от application/service layer, устанавливает правила, инициирует реконфигурацию, обрабатывает rule miss (отсутствие правила), link failure (отказ линии), node failure (отказ узла), sensing degradation (деградацию радиозондирования) и congestion (перегрузку). Такая роль согласуется с SDN-подходом для 5G/6G-сетей, где контроллер управляет политиками, срезами, маршрутами и реконфигурацией, а data plane выполняет установленные правила [9], [10].

В данной формализации RIC не является обучающимся агентом и не заменяет контрактный автомат оптимизационной процедурой. Его решения представлены конечными классами политик, выбираемыми по дискретным входным условиям и проверяемыми через timed automata.

Граница уровня:

- SDN/RIC принимает агрегированные отчеты MAC и PHY.
- SDN/RIC не управляет отдельными OFDM-symbol (символами ортогонального частотного мультиплексирования) или beam sweep (сканированием лучей) напрямую; он задает политику и ограничения для MAC/PHY.
- SDN/RIC устанавливает flow rules (правила потоков), slice constraints (ограничения сетевых срезов), recovery actions (действия восстановления) и admission decisions (решения допуска сервиса).
- SDN/RIC обязан отвечать явно: install+forward, reject/drop with reason, rollback, degraded mode или recovery failure.

### 4.2 Композиция автоматов SDN/RIC

Композиция уровня задается как:

```text
A_SDN = A_MON || A_RISK || A_POLICY || A_RULE || A_REC || A_SDN_AGG.
```

где A_MON (monitoring automaton, автомат мониторинга) контролирует свежесть телеметрии; A_RISK (risk classifier, автомат классификации риска) переводит события в класс риска; A_POLICY (policy automaton, автомат политики) выбирает допустимое действие; A_RULE (rule-table automaton, автомат таблицы правил) устанавливает или отклоняет правила; A_REC (recovery automaton, автомат восстановления) обрабатывает отказы и реконфигурации; A_SDN_AGG (aggregate automaton, агрегирующий автомат) формирует команды нижним уровням и ответы сервисному уровню.

| Автомат | Основные состояния | Ответственность |
|---|---|---|
| A_MON | MonitorIdle, CollectReports, TelemetryFresh, TelemetryStale, TelemetryMissing | Контроль свежести PHY/MAC-отчетов |
| A_RISK | RiskLow, RiskMedium, RiskHigh, RiskCritical | Классификация деградации, отказа, перегрузки |
| A_POLICY | PolicyIdle, Evaluate, NormalMode, SensingBoostMode, CommPriorityMode, ConstrainedMode, RejectByPolicy | Выбор политики управления |
| A_RULE | RuleStable, RuleMiss, RuleInstallPending, RuleInstalled, RuleAcked, RuleTimeout, RuleDropReason | Обработка rule miss и таблицы правил |
| A_REC | StableConfig, FailureDetected, StandbySwitch, ReactiveReembedding, Rollback, RecoveryFailed | Восстановление после отказов |
| A_SDN_AGG | CommandBuild, CommandSent, AwaitAck, Acked, CommandTimeout | Согласование команд и подтверждений |

### 4.3 Дискретная абстракция SDN/RIC

Отображение абстракции задается как:

```text
alpha_SDN : X_SDN_obs x X_SDN_cfg x X_SVC_req -> X_SDN_disc.
```

X_SDN_obs содержит отчеты от PHY/MAC: freshness, QueueClass, DelayClass, ResourceClass, SensingQualityClass, LinkState, RuleState. X_SDN_cfg содержит текущую сетевую конфигурацию, правила политики, допустимые recovery-пути и ограничения срезов. X_SVC_req содержит класс сервиса, критичность и SLA.

Конечные классы:

| Переменная | Значения | Смысл |
|---|---|---|
| TelemetryClass | TEL_FRESH, TEL_STALE, TEL_MISSING | Свежесть управляющей информации |
| RiskClass | RISK_LOW, RISK_MED, RISK_HIGH, RISK_CRIT | Класс риска |
| PolicyClass | POL_NORMAL, POL_SENS_BOOST, POL_COMM_PRIO, POL_CONSTRAINED, POL_REROUTE, POL_REJECT | Класс политики |
| RuleClass | RULE_OK, RULE_MISS, RULE_PENDING, RULE_ACKED, RULE_TIMEOUT, RULE_DROP | Состояние правила |
| RecoveryClass | REC_STABLE, REC_STANDBY, REC_REEMBED, REC_ROLLBACK, REC_FAILED | Состояние восстановления |
| SliceClass | SLICE_OK, SLICE_WARN, SLICE_VIOLATED | Состояние сетевого среза |

### 4.4 Контракт SDN/RIC

Контракт уровня:

```text
C_SDN = (Ass_SDN, Gar_SDN).
```

Предположения Ass_SDN:

- MAC передает mac_report! с конечным классом очередей, ресурсов и задержки.
- PHY через MAC или напрямую передает freshness и sensing-degradation classes.
- Сервисный уровень передает требование в конечной форме: service class, criticality, latency bound, reliability class.
- Набор допустимых политик и recovery-конфигураций конечен.
- Подтверждения от нижних уровней приходят через ack-каналы или истекает заданный timeout.

Гарантии Gar_SDN:

- Rule miss должен завершиться одним из исходов: rule installation + forwarding, drop/reject with explicit reason, timeout report.
- Link failure должен завершиться одним из исходов: standby switch, reactive re-embedding, rollback to stable configuration, explicit recovery failure.
- Sensing degradation должен завершиться одним из исходов: sensing boost, constrained mode, rejection by policy.
- При TEL_STALE или TEL_MISSING контроллер не должен выполнять оптимистичную реконфигурацию, зависящую от свежей телеметрии; допустимы conservative policy (консервативная политика), constrained mode или запрос повторного отчета.
- Любой service admission request (запрос допуска сервиса) должен получить service_accept! или service_reject! до D_admission.
- Любая команда нижнему уровню должна получить подтверждение до D_ctrl_ack или перейти в CommandTimeout.

### 4.5 Обработка rule miss

Rule miss является центральным сценарием для SDN-уровня, потому что он связывает data plane (уровень пересылки) и control plane (уровень управления). Формально:

```text
RuleStable --rule_miss?--> RuleMiss
RuleMiss --policy_allows_install--> RuleInstallPending
RuleInstallPending --flow_mod!--> RuleInstalled
RuleInstalled --ack? before D_rule_ack--> RuleAcked
RuleInstalled --timeout--> RuleTimeout
RuleMiss --policy_rejects--> RuleDropReason
RuleAcked --forward_cmd!--> RuleStable
RuleDropReason --drop_report!--> RuleStable
RuleTimeout --timeout_report!--> RuleStable
```

Слабое место, которое нужно явно закрыть в статье: недопустимо писать только “при rule miss контроллер устанавливает правило”. Это неполный контракт. Должны быть определены как минимум три исхода: установка и пересылка, отказ с причиной, тайм-аут установки. Иначе верификация может пропустить зависание в состоянии RuleInstallPending.

### 4.6 Обработка sensing degradation

Sensing degradation (деградация радиозондирования) приходит снизу как дискретный класс, например SENS_WARN или SENS_FAIL. SDN не вычисляет CRB (нижнюю границу Крамера–Рао), probability of detection (вероятность обнаружения) или sensing capacity (сенсорную пропускную способность). Он принимает уже классифицированное событие и выбирает политически допустимый режим:

```text
NormalMode --sensing_degradation?--> Evaluate
Evaluate --policy_allows_boost and resources_available--> SensingBoostMode
Evaluate --resources_tight--> ConstrainedMode
Evaluate --policy_denies or resources_exhausted--> RejectByPolicy
SensingBoostMode --sdn_policy_cmd!--> AwaitAck
ConstrainedMode --sdn_policy_cmd!--> AwaitAck
RejectByPolicy --service_reject! or mac_report!--> NormalMode
```

Это сохраняет разделение уровней: PHY/MAC оценивают техническое состояние, SDN выбирает допустимую политику, service layer получает результат в терминах SLA.

### 4.7 Обработка отказов и реконфигурации

Восстановление задается автоматом A_REC:

```text
StableConfig --link_failure? or node_failure?--> FailureDetected
FailureDetected --standby_available--> StandbySwitch
FailureDetected --standby_unavailable and alternative_config_exists--> ReactiveReembedding
StandbySwitch --ack? before D_rec--> StableConfig
ReactiveReembedding --ack? before D_rec--> StableConfig
StandbySwitch --timeout--> Rollback
ReactiveReembedding --timeout--> Rollback
Rollback --rollback_ack? before D_rollback--> StableConfig
Rollback --timeout--> RecoveryFailed
RecoveryFailed --failure_report!--> StableConfig or RejectByPolicy
```

Dynamic timed automata (динамические временные автоматы) здесь нужны только для ограниченной реконфигурации: включение резервного режима, замена абстрактного подузла более детальной моделью, отключение порта, изменение конечной конфигурации [8]. Не следует вводить неограниченное создание узлов или произвольную топологическую эволюцию, потому что это разрушит проверяемость модели.

### 4.8 Временные переменные SDN/RIC

| Часы | Назначение |
|---|---|
| c_mon | Возраст последней телеметрии |
| c_dec | Время выбора политики |
| c_rule | Время обработки rule miss |
| c_ctrl_ack | Время ожидания подтверждения от MAC/PHY/data plane |
| c_rec | Время восстановления после отказа |
| c_rollback | Время отката к стабильной конфигурации |
| c_admission | Время ответа на запрос сервиса |

Типовые инварианты:

```text
CollectReports:        c_mon <= D_mon
Evaluate:              c_dec <= D_decision
RuleInstallPending:    c_rule <= D_rule_install
AwaitAck:              c_ctrl_ack <= D_ctrl_ack
StandbySwitch:         c_rec <= D_recovery
ReactiveReembedding:   c_rec <= D_recovery
Rollback:              c_rollback <= D_rollback
```

### 4.9 Верификационные свойства SDN/RIC

Примеры свойств:

```text
A[] not deadlock
A[] not (RuleInstallPending and c_rule > D_rule_install)
A[] (RuleMiss imply eventually (RuleAcked or RuleDropReason or RuleTimeout))
A[] (TEL_STALE imply not optimistic_reconfig)
A[] (FailureDetected imply eventually (StableConfig or RecoveryFailed))
A[] (RecoveryFailed imply failure_report_sent)
A[] (service_request_pending imply c_admission <= D_admission)
```

Свойства “среднее число rule miss за интервал”, “вероятность успешного восстановления” или “ожидаемая цена реконфигурации” не являются свойствами обычного timed automaton. Их можно проверять только после расширения модели вероятностями, весами или внешней статистикой.

### 4.10 Optional extension: A_SEC

Безопасность не является фокусом основной модели. Поэтому A_SEC (security automaton, автомат безопасности) не включается в базовую композицию A_SDN. Его можно добавить только как расширение:

```text
A_SDN_EXT = A_SDN || A_SEC.
```

Минимальный A_SEC не моделирует криптографические протоколы. Он только переводит внешние security alerts (события безопасности) в конечные классы реакции. Такая постановка использует только общую идею SDN/NFV-based monitoring (мониторинга на основе программно-определяемых сетей и виртуализации сетевых функций) из работ по безопасности 6G [11], [12], но не переносит безопасность в центр модели:

```text
SecurityNominal --threat_alert?--> ThreatObserved
ThreatObserved --policy_allows_isolation--> IsolateSegment
ThreatObserved --policy_requires_report_only--> SecurityReport
IsolateSegment --isolate_cmd!--> AwaitIsolationAck
AwaitIsolationAck --ack? before D_sec_ack--> SecurityNominal
AwaitIsolationAck --timeout--> SecurityFailure
SecurityFailure --security_report!--> SecurityNominal
```

Такой автомат допустим как optional/extended SDN automaton, но он не должен менять центральную идею статьи. Основная линия остается: PHY, MAC, SDN/RIC и service layer формализуются как иерархия контрактных временных автоматов.

## 5. Application / Service Layer

### 5.1 Назначение и границы уровня

Application / Service Layer (прикладной или сервисный уровень) задает требования к сети, а не управляет радиоресурсом напрямую. Он формирует service request (запрос сервиса), SLA constraints (ограничения уровня обслуживания), priority/criticality (приоритет и критичность), а затем получает accept/reject/degraded-service decision (решение о принятии, отказе или деградированном обслуживании). Такое разделение соответствует SDN-подходу, где приложения задают требования через northbound interface (северный интерфейс), а контроллер преобразует их в политики и правила нижних уровней [9], [10].

Для ISAC-сценариев сервисный уровень должен различать два типа требований:

- communication requirements (требования передачи данных): задержка, надежность, пропускная способность, потери;
- sensing requirements (требования радиозондирования): период обновления, требуемая точность, допустимая свежесть данных, зона наблюдения.

Сервисный уровень не должен напрямую командовать beam management, PRS-pattern (паттерн позиционно-измерительных сигналов) или распределением физических ресурсов. Он задает контракт, а SDN/RIC и MAC решают, можно ли выполнить этот контракт при текущих ограничениях.

### 5.2 Композиция автоматов сервиса

Сервисный уровень задается композицией:

```text
A_SVC = A_REQ || A_SLA || A_CRIT || A_SVC_AGG.
```

| Автомат | Основные состояния | Ответственность |
|---|---|---|
| A_REQ | ServiceIdle, RequestBuild, RequestPending, Accepted, Rejected, Completed | Жизненный цикл запроса сервиса |
| A_SLA | SLAOk, SLAWarning, SLAViolated, SLAReported | Контроль выполнения SLA |
| A_CRIT | NonCritical, Critical, SafetyCritical | Класс критичности сервиса |
| A_SVC_AGG | DemandBuild, DemandSent, AwaitDecision, DecisionReceived | Передача требований в SDN/RIC |

### 5.3 Дискретная абстракция сервиса

Абстракция задается отображением:

```text
alpha_SVC : X_SVC_req x X_SVC_obs -> X_SVC_disc.
```

X_SVC_req содержит исходное требование приложения: latency bound (предел задержки), reliability target (целевая надежность), throughput demand (потребность в пропускной способности), sensing update period (период обновления sensing), sensing accuracy class (класс точности радиозондирования). X_SVC_obs содержит наблюдаемый результат: принято, отклонено, деградировано, SLA нарушен.

Конечные классы:

| Переменная | Значения | Смысл |
|---|---|---|
| ServiceClass | SVC_URLLC, SVC_EMBB, SVC_MMTC, SVC_ISAC_SENSING, SVC_UAV, SVC_INDUSTRIAL | Класс сервиса |
| CriticalityClass | CRIT_LOW, CRIT_MED, CRIT_HIGH, CRIT_SAFETY | Критичность |
| SLAClass | SLA_OK, SLA_WARN, SLA_VIOLATED | Выполнение SLA |
| AdmissionClass | ADM_PENDING, ADM_ACCEPTED, ADM_REJECTED, ADM_DEGRADED | Решение допуска |
| DemandClass | DEMAND_COMM, DEMAND_SENS, DEMAND_JOINT | Тип требования |

### 5.4 Контракт сервисного уровня

Контракт:

```text
C_SVC = (Ass_SVC, Gar_SVC).
```

Предположения Ass_SVC:

- SDN/RIC возвращает service_accept!, service_reject! или service_degraded! до D_admission.
- SLA-наблюдения поступают в дискретной форме SLA_OK, SLA_WARN или SLA_VIOLATED.
- Сервисный запрос задает конечный класс сервиса, критичности и требований.

Гарантии Gar_SVC:

- Сервис не формирует некорректный запрос вне допустимого множества классов.
- Если запрос принят, сервисный уровень переходит в Accepted и начинает контроль SLA.
- Если SLAClass = SLA_WARN, должен быть сформирован sla_warning_report! до D_sla_warn.
- Если SLAClass = SLA_VIOLATED, должен быть сформирован sla_violation_report! до D_sla_violation.
- Если запрос отклонен, состояние Rejected должно содержать явную причину: policy_reject, resource_unavailable, stale_telemetry, recovery_failed или deadline_impossible.

### 5.5 Переходы A_REQ и A_SLA

Жизненный цикл запроса:

```text
ServiceIdle --new_demand?--> RequestBuild
RequestBuild --service_request!--> RequestPending
RequestPending --service_accept? before D_admission--> Accepted
RequestPending --service_degraded? before D_admission--> AcceptedDegraded
RequestPending --service_reject? before D_admission--> Rejected
RequestPending --timeout--> Rejected
Accepted --service_complete?--> Completed
AcceptedDegraded --service_complete?--> Completed
Completed --> ServiceIdle
Rejected --> ServiceIdle
```

Контроль SLA:

```text
SLAOk --sla_warn?--> SLAWarning
SLAWarning --sla_warning_report!--> SLAOk or SLAViolated
SLAWarning --sla_violation?--> SLAViolated
SLAViolated --sla_violation_report!--> SLAReported
SLAReported --service_reconfigure?--> SLAOk or ServiceTerminate
```

### 5.6 Временные переменные сервиса

| Часы | Назначение |
|---|---|
| c_req | Время формирования сервисного запроса |
| c_admission | Время ожидания решения SDN/RIC |
| c_sla_warn | Время реакции на предупреждение SLA |
| c_sla_violation | Время реакции на нарушение SLA |
| c_session | Время активной сервисной сессии |
| age_sensing | Возраст последней sensing-информации для сервиса |

Инварианты:

```text
RequestPending:      c_admission <= D_admission
SLAWarning:          c_sla_warn <= D_sla_warn
SLAViolated:         c_sla_violation <= D_sla_violation
Accepted:            age_sensing <= D_sensing_fresh if DemandClass includes sensing
```

### 5.7 Верификационные свойства сервиса

Примеры свойств:

```text
A[] not deadlock
A[] (RequestPending imply c_admission <= D_admission)
A[] (RequestPending imply eventually (Accepted or AcceptedDegraded or Rejected))
A[] (SLAViolated imply eventually sla_violation_report_sent)
A[] not (Accepted and reason == resource_unavailable)
A[] (CRIT_SAFETY and SLA_VIOLATED imply eventually (service_reconfigure or service_terminate or violation_report_sent))
```

Слабое место сервисного уровня в ранней версии модели может возникнуть, если SLA задается только текстово и не переводится в конечные классы. Для timed automata необходимо явно задать конечные классы SLA, criticality и admission outcome. Иначе сервисный уровень не будет формально связан с SDN/RIC.

## 6. Межуровневые сценарии

### 6.1 Сценарий sensing degradation

Последовательность обработки деградации sensing:

```text
A_PHY detects SensingQualityClass = SENS_WARN or SENS_FAIL
A_PHY/A_MAC sends phy_kpi_report! or mac_report!
A_SDN.A_MON classifies telemetry freshness
A_SDN.A_POLICY selects POL_SENS_BOOST, POL_CONSTRAINED, or POL_REJECT
A_MAC applies sensing_boost_cmd! or constrained_mode_cmd!
A_SVC receives accepted/degraded/rejected service outcome
```

Проверяемое свойство:

```text
Sensing degradation must not remain unresolved:
A[] (sensing_degradation imply eventually (sensing_boost or constrained_mode or explicit_reject))
```

### 6.2 Сценарий rule miss

Последовательность:

```text
Data plane raises rule_miss?
A_SDN.A_RULE enters RuleMiss
A_SDN.A_POLICY evaluates admissibility
A_SDN installs rule, drops with reason, or reports timeout
A_SVC receives service impact if the flow belongs to an active service
```

Проверяемое свойство:

```text
A[] (RuleMiss imply eventually (RuleAcked or RuleDropReason or RuleTimeout))
```

### 6.3 Сценарий link failure

Последовательность:

```text
A_ENV emits link_failure?
A_SDN.A_REC enters FailureDetected
A_SDN tries StandbySwitch or ReactiveReembedding
If recovery fails, Rollback is attempted
A_SVC receives degraded/rejected/failed outcome when SLA is affected
```

Проверяемое свойство:

```text
A[] (FailureDetected imply eventually (StableConfig or RecoveryFailed))
A[] (RecoveryFailed imply failure_report_sent)
```

### 6.4 Сценарий resource conflict between communication and sensing

Последовательность:

```text
A_MAC observes ResourceClass = RES_TIGHT or RES_EXHAUSTED
A_MAC compares SensingDemand and CommDemand under SDN policy
A_MAC applies SCH_JOINT, SCH_COMM, SCH_SENS, SCH_CONSTRAINED, or rejects
A_SDN receives mac_report! if local scheduling cannot satisfy the contract
```

Проверяемое свойство:

```text
A[] not (RES_EXHAUSTED and silent_accept)
A[] (resource_conflict imply eventually (joint_schedule or constrained_mode or explicit_reject or sdn_report))
```

## 7. Общие ограничения модели

1. Обычные timed automata проверяют достижимость, дедлайны, отсутствие тупиков, согласованность переходов и bounded response. Они не дают вероятности событий, средние частоты потерь и математическое ожидание стоимости без расширений.

2. Непрерывные величины PHY/MAC должны быть заранее сведены к конечным классам через alpha_PHY и alpha_MAC. Если этого нет, модель не является конечной и ее нельзя корректно проверить стандартными средствами.

3. SDN/RIC в данной работе не является обучающимся или самооптимизирующимся агентом. Он представлен как контрактный автомат, выбирающий одну из конечных политик.

4. Безопасность в основной версии не является самостоятельным фокусом. A_SEC допустим только как optional/extended automaton для внешних alert-событий и не должен расширять работу в сторону криптографической архитектуры.

5. Dynamic timed automata следует применять ограниченно: для реконфигурации, замены абстрактного компонента детализированным, отключения порта, переключения на резерв или отката. Произвольная динамическая топология сделает модель плохо проверяемой.

## 8. Список источников

[1] Y. Li, Y. Zhang, C. Masouros, S. Pollin, and F. Liu, "Rethinking Signaling Design for ISAC: From Pilot-Based to Payload-Based Sensing," IEEE Communications Standards Magazine, in press, 2026, doi: 10.1109/mcomstd.2025.3645941.

[2] G. Liu et al., "SensCAP: A Systematic Sensing Capability Performance Metric for 6G ISAC," IEEE Internet of Things Journal, vol. 11, no. 18, pp. 29438-29454, 2024, doi: 10.1109/JIOT.2024.3430502.

[3] G. Liu et al., "Cooperative Sensing for 6G ISAC: Concept, Key Technologies, Performance Evaluation, and Field Trial," Engineering, vol. 56, pp. 130-148, 2026.

[4] Y. Huang, J. Xu, M. A. Badiu, G. Chen, J. Coon, and M.-S. Alouini, "ISAC-Enabled Low-Overhead Beam Management: Performance Analysis and Pilot Optimization," IEEE Transactions on Wireless Communications, vol. 25, pp. 10702-10715, 2026, doi: 10.1109/TWC.2026.3653956.

[5] R. Alur and D. L. Dill, "A Theory of Timed Automata," Theoretical Computer Science, vol. 126, no. 2, pp. 183-235, 1994.

[6] UPPAAL Documentation, "Query Semantics: Symbolic Queries," accessed 2026. Available: https://docs.uppaal.org/language-reference/query-semantics/symb_queries/.

[7] M. Anand and S. Vestal, "Formal Modeling and Analysis of the AFDX Frame Management Design," in Proceedings of the IEEE International Conference on Engineering of Complex Computer Systems, 2007.

[8] T. Tigane, A. Sadovykh, S. Bensalem, and M. Bozga, "Dynamic Timed Automata for Reconfigurable System Modeling," 2023.

[9] O. A. Mosudi, S. I. Popoola, A. A. Atayero, and A. A. Elngar, "SDN for 5G and Beyond: Transforming Network Architecture," 2025.

[10] Zolanvari, "SDN for 5G," 2015.

[11] A. Hirsi, M. Aljanabi, H. Karim, A. H. Ali, and S. Khan, "SDN Security in 6G: Future Technologies and Research Challenges," International Journal of Intelligent Engineering and Systems, vol. 19, no. 4, pp. 221-234, 2026.

[12] M. E. Jaadouni, A. Amnai, and Y. Fakhri, "Evolving Security for 6G: Integrating Software-Defined Networking and Network Functions Virtualization for Enhanced Protection," International Journal of Advanced Computer Science and Applications, vol. 15, no. 9, 2024.
