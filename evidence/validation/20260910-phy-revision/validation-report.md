# P1 — Validation method, PHY semantics and parameter provenance

## Revision scope — 2026-09-10

This is the author's revised local copy of the P1 report. It clarifies PHY
definitions, formulas, parameter roles and the hardware-independent scope of the
article. The repository's historical evidence, TeX, model and generator are not
changed. This revision supplies no new model-checking or empirical result and
does not constitute independent acceptance.

The original is preserved as [validation-report.before-phy-revision-20260910.md](validation-report.before-phy-revision-20260910.md),
SHA256 `23d62e29254786ddb7e3091584da5df4f6a79946fb69f293e03cbb74dafd637c`.
Current user-authorized target: `D:/ПЗ психология/validation-report.md`.
Definitions adopted below are a consistent interpretation for this report and
proposed source-alignment decisions; they do not assert that matching changes
have already been made in the executable model or the manuscript.

### Original P1 provenance

Issue: [#15](https://github.com/artmus208/uppaal_sdn_isac/issues/15).
Owner of the original P1 deliverable: artmus208. Atomic IDs: V01–V05.
Independent acceptance was pending in that report.
Input: `read` commit `f2f714a26d6b9d9f538ef1a16b53c3e060768a11`.
Baseline: `reviewer-r1-candidate`, not frozen; manifest SHA256
`89b8d6f520546c873649643b3cf90fd80f58e4458a443832369e3d1d28bf719a`.
Original Issue write scope: `evidence/validation/20260907-p1/**`.

The original P1 package provides a parameter inventory and a validation
specification. A later P2 integrated candidate exists, but its existence is not
scientific acceptance. Historical observations and later implementation decisions
are distinguished below rather than treating every original observation as an
unresolved defect of the current candidate.

## Scope of the article and levels of parameter justification

The current research object is temporal cross-layer control under explicit finite
inputs. A UAV signature dataset, selected apparatus and a calibrated physical
estimator are not prerequisites for studying this abstract control model.
Its profile values are scenario assumptions, not measured device capabilities.
The meaning of probability, rate, error, variance, age and occupancy must still
be defined before interpreting the resulting classes.

1. **Abstract study, required now:** specify parameter roles, domains, event
   endpoints, clock resets, relative timing, class predicates, loss/missing-data
   rules and provenance. Explain why each illustrative configuration was chosen
   and what behaviors it includes. A finite parameter sweep supports only those
   configurations; it is not a proof for every hardware realization or all
   parameter values.
2. **Physical instantiation, conditional on the claim:** select hardware,
   waveform, estimator and service requirements; bind physical units and obtain
   analytical, simulation or measurement evidence appropriate to the claim.
   Claims of empirical accuracy require empirical evidence. The calibration
   routes below describe this later stage, not an unconditional obligation to
   obtain unavailable UAV measurements for the abstract study.

Separate **requirements** (what a service needs), **environment assumptions**
(admitted inputs and delays), **configuration choices** (what is set),
**estimates** (what is inferred) and **policy states** (what is decided).
A configured requirement is not a measured guarantee; an enum code is not a
physical quantity. Configuration-independent definitions can be fixed now while
their deployment-specific numerical values remain symbolic.

## Evidence and coverage

`inventory.py` records exact SHA256 hashes of 26 input files, the three built-in
profiles per generated layer, 43 distinct layer-qualified timing constants, 59
finite domains, every parsed literal constant occurrence, bounded integer
declarations and clock guards/invariants. `parameter-table.md` is its readable
projection; `inventory.json` preserves values by surface and source line references.
Source references are line numbers in the pinned commit, not in the historical
dirty candidate. Generated XML hashes refer to in-memory generation with default
options for each profile; generation is not verification.

Declared source surfaces: the four layer TeX formalizations and four model XMLs
listed in the inventory, plus `alpha.py`, `defaults.py`, `generator.py`, `ir.py`
and `property_pack.py` for PHY/MAC/SDN. The numeric constant scanner distinguishes
timing names from enum encodings; the latter were inspected as finite codes, not
capacities. No numerical queue-capacity or retry-count bound is defined in these
candidate models. Queue/resource/overflow states abstract those quantities away.
The bounded policy counters count enabled rules, not network packets or retries.

Coverage is of those surfaces and the three named profiles. It is not a claim
about every historical XML, benchmark, custom JSON profile, generator mode or
number in prose. Class mappings without numeric definitions require explicit
abstract predicates
or external-input semantics now, and physical threshold justification when a
physical instantiation is claimed. Symbolic estimator parameters are discussed
in the tables below; explanatory symbols added in this revision do not change
the historical inventory counts. None is asserted to be a new generated UPPAAL
constant. The scanner is not a general TeX parser or an empirical validator.

## Historical P1 findings at the pinned input

The following observations are preserved from the original audit; they were not
re-executed during this revision. The disposition immediately below qualifies
their relevance to later P2 work. In particular, absence of a physical time scale
is a limit on physical interpretation, not by itself a defect of the abstract
model. References to what P2 “must” resolve in this historical list describe the
original handoff, not an assertion that no later decision exists.

1. The profiles label their provenance `built-in`. None pins a physical time unit,
   measurement dataset or calibrated radio configuration. Default/conservative/
   stress values are engineering illustrations. Smaller deadlines are not by
   themselves a proof of more conservative behavior: they also change enabled
   transitions and admissible environment behavior.
2. All eight numerical boundaries of `phy.alpha.classify_sample` assign equality
   to the better adjacent class, despite returning `boundary_policy=worse_class`.
   The table records executable below/equal/above probes, not a proposed fix.
   PHY TeX lines 180–187 uses similar inequalities, while lines 230–241 demand
   worse-class treatment. P2 must resolve the semantic conflict in both artifacts.
3. The demo mapper produces only FRESH/EXPIRED for AoS and NONE/CONFIRMED for
   blockage. STALE and SUSPECTED exist in the domain but have no preimage through
   this mapper. Most PHY classes are not computed by it. Profile selection changes
   the output label, not these hardcoded numerical thresholds.
4. Omitted demo measurements yield nominal defaults (SINR=20, Pd=0.99, Rfa=0.01,
   age=0, blockage=false). Missing telemetry cannot use this path as evidence of
   good service. The function explicitly identifies itself as a smoke/demo mapper.
5. PHY TeX lines 142–146 defines SINR as a linear power ratio; the demo mapper
   does not declare units for 0/10/25. Do not assume dB from familiar magnitudes.
   Rfa likewise needs a decision between probability per decision and rate per
   exposure interval; 0.05/0.2 are not interchangeable across those definitions.
6. PHY freshness resets at report delivery (TeX lines 762–768). Time since receipt
   and age of the information carried by that report differ. A delayed old report
   can reset a receipt timer without supplying a fresh sensing estimate. P2 must
   name the intended metric and preserve the sample timestamp if true data age is
   intended. P1 does not silently change the existing definition.
7. The historical candidate audit has 9 mismatching file hashes out of 20 and a
   mismatching generator aggregate. Each stored PHY/MAC/SDN XML also differs in
   byte hash from current default in-memory generation. A hash difference alone
   does not identify a semantic defect. Both surfaces are inventoried; P2/Gate 1
   must select and regenerate the canonical configuration rather than assuming
   a stored smoke XML is a frozen output of the current generator.

### Subsequent P2 disposition

At `read@4480f1087b93f48541a925590ae82ca86fa4b808`, the
[P2 specification decisions](https://github.com/artmus208/uppaal_sdn_isac/blob/4480f1087b93f48541a925590ae82ca86fa4b808/evidence/instantiation/20260907-p2-scope/decisions.md)
exclude the raw demo mapper from the finite input envelope, retain STALE and
SUSPECTED, and choose source age. The
[P2 implementation decisions](https://github.com/artmus208/uppaal_sdn_isac/blob/4480f1087b93f48541a925590ae82ca86fa4b808/evidence/instantiation/20260908-p2-integrated/decisions.md)
describe explicit validity, removal of manufactured good sensing KPI at request
creation, source-age clocks, expiry and `D_cmd=1` abstract unit. These are
implementation decisions, not physical calibration or acceptance of V01–V05.

Classes are selected by an abstract environment, not a working physical
estimator. The candidate has an aggregate single-BS/single-UAV/link/controller/
service interpretation. Delivery uses simplified latest mailboxes and loss/
overwrite rules. New sampling invalidates older transport and temporarily marks
older delivered PHY data missing; shared SDN freshness follows the PHY source.
This is not a general multi-source information-age implementation.

[PR #24](https://github.com/artmus208/uppaal_sdn_isac/pull/24), head
`601de5344a0f856a75470192629790efe027b0f3`, was open/unmerged when inspected on
2026-09-10. It proposes correction of the eight raw-mapper equalities; its
reported checks were not reproduced by this report revision. Do not attribute
those bytes to the pinned `read` input or infer that other semantics were fixed.

## Timing calibration

This section applies to all **43 historical layer-qualified timing rows** in the
[parameter table](https://github.com/artmus208/uppaal_sdn_isac/blob/4480f1087b93f48541a925590ae82ca86fa4b808/evidence/validation/20260907-p1/parameter-table.md).
No value is relabelled as a standard-derived physical bound.

For the abstract study, register each trigger, terminal event, clock reset,
included waiting/transport/processing, abstract unit, requirement/assumption role,
admissible domain and value-selection rationale. Correlate events by transaction
or session; an unrelated acknowledgement cannot terminate an interval. Add
physical endpoints, units and measurement uncertainty only at physical binding.

The PHY subset contains **12** constants:

| PHY constant | Historical default / conservative / stress | Abstract role to identify at its use site |
|---|---|---|
| `D_meas` | 5 / 4 / 2 | Channel measurement/classification response deadline |
| `D_sig` | 5 / 4 / 2 | Signal reconfiguration response deadline |
| `D_sense` | 5 / 4 / 2 | Sensing-quality computation/report response deadline |
| `D_report` | 5 / 4 / 2 | Aggregate PHY report response deadline |
| `D_BM` | 5 / 4 / 2 | Beam recovery deadline, including an explicit unsuccessful outcome |
| `D_child` | 5, fixed | Assumed child-report delivery bound |
| `D_net` | 5, fixed | Assumed network-delivery bound |
| `T_meas` | 5, fixed | Nominal measurement timing parameter; not an automatic exact period |
| `J_meas` | 1, fixed | Measurement timing tolerance; its one-sided/symmetric use must be specified |
| `T_report` | 5, fixed | Nominal report timing parameter |
| `tau_SSB` | 4, fixed | SSB/search timing parameter; distinguish it from burst duration `T_SSB` |
| `J_SSB` | 1, fixed | SSB/search timing tolerance |

All these values are abstract time units. “Conservative” is a profile name, not
a proved inclusion relation between its behaviors and those of another profile.
For a selected executable profile, require positive timing budgets/periods and
nonnegative jitter in the supported integer domain; define any intentional zero
budget separately. A symmetric jitter interval must not admit negative spacing.
The later P2 `D_cmd=1`, transport and sampling choices, and age boundaries 5/10
must be recorded in the selected integrated parameter set; they are not new rows
silently added to the historical 43-constant inventory.

Check the actual guards, invariants, enabled synchronizations and resets together.
An upper-bound guard alone does not force an event to occur by that bound.
Periodicity also requires the intended lower bound/reset/progress behavior.
Repeated triggers must not silently reset the oldest outstanding deadline unless
the declared coalescing policy permits that interpretation. Distinct child,
transport, processing and report budgets may overlap; add them only for genuinely
sequential stages with compatible endpoints. A delivery ACK is not automatically
successful sensing, beam recovery or satisfaction of the application SLA.

In the following table, event meanings apply now. Requirements to measure or
instrument apparatus apply to the **physical-instantiation** route. In the
abstract study declare corresponding assumptions and assess their composition.

| Layer and parameters | Event meaning; physical calibration route when applicable |
|---|---|
| PHY `D_meas`, `D_sig`, `D_sense` | Timestamp measurement request→classification, configuration command→applied signal configuration, sensing trigger→classified result. Include estimator window/compute delay and declared load. Obtain bounded envelopes or declare statistical coverage explicitly. |
| PHY `D_BM` | Recovery command→restored/failed/handover outcome. Measure sweep, detection, processing and control transport at declared beam count and blockage regime; choose a recovery requirement including explicit failure outcome. |
| PHY `D_child`, `D_net`, `D_report` | Child report creation→aggregate receipt; network send→controller delivery; aggregate trigger→KPI publication. Specify queuing, loss, reorder, retransmission assumptions and separate them from CPU time. |
| PHY `T_meas`, `J_meas`, `T_report`, `tau_SSB`, `J_SSB` | Configured sampling/report/sweep schedule plus observed inter-event spacing and jitter; record numerology and timer resolution. Declare whether jitter is one-sided or symmetric. These five schedule/jitter constants and D_child/D_net are the seven constants fixed across the built-in profiles. A guard c≤T+J alone does not establish a period or a guaranteed event. |
| MAC `D_collect`, `D_sched`, `D_phy_ack` | KPI collection, scheduling decision and matching PHY command acknowledgement. Pin scheduler period, active flows, contention, compute/transport bounds; check which stages share/reset the same clock before adding budgets. |
| MAC `D_queue_crit`, `D_buf_report` | Critical queue→drain/reject/report and overflow→report. Use queue size, arrival envelope and service curve or simulated queue trace at declared traffic/resources; overflow itself is a class, not a numeric buffer capacity. |
| MAC `D_mac_report`, `D_phy_report` | Report build→publication and acceptable upstream report spacing/age. Distinguish report creation age from receipt spacing and include lost-report handling. |
| SDN `D_mon`, `D_decision` | Telemetry collection and policy evaluation under declared controller load; pin tick schedule, input completeness and computation envelope. |
| SDN `D_rule_install`, `D_rule_ack`, `D_ctrl_ack` | Rule miss→installation outcome, rule acknowledgement, command acknowledgement. Instrument controller and switches, match rule/version/transaction, include RTT and device installation time. Preserve the profile constraint D_rule_ack ≤ D_rule_install and examine equality/timeouts in P2. |
| SDN `D_recovery`, `D_rollback` | Failure detection→recovery outcome and rollback interval. Budget their sum only when stages are sequential with the observer's exact start/reset events. Include topology size/failover policy and unsuccessful recovery. |
| SDN `D_admission`, APP `D_admission` | One cross-layer admission request→accept/degrade/reject, same request ID. Match endpoints and compatible bounds; equal default number 15 does not prove that the two contracts compose. |
| SDN `D_sec_ack` | Optional security extension acknowledgement; calibrate only if A_SEC is selected. Presence of the declaration in the base model does not demonstrate its use. |
| APP `D_req`, `D_event`, `D_update`, `D_safety` | Demand→request, sensed event→required application outcome, update cadence, violation→safety response. Obtain the service contract first, then allocate sensing/network/controller/application portions without counting overlapping stages twice. |
| APP `D_fresh`, `D_sensing_fresh` | Maximum useful information age at the named consumer; derive from an application dynamics/error tolerance or a named SLA. These are not generic network delay budgets. |
| APP `D_sla_warn`, `D_sla_violation`, `D_fresh_report`, `D_update_report`, `D_fa_report`, `D_miss_report`, `D_detect_warn`, `D_detect_violation` | Timestamp each named warning/violation condition→its matching report or outcome. Calibrate event detection/window delay separately from subsequent reporting, using criticality-specific service requirements. |

Use one common model-time unit. Its physical scale may remain unassigned until
hardware/service binding. UPPAAL clocks remain dense-time; integer constants do
not imply discrete time steps. A later physical instantiation pins Δ>0 seconds
per model-time unit, so `t_physical = Δ * t_model`.

For an over-approximation, map a physical environment interval [L,U] outward to
[floor(L/Δ),ceil(U/Δ)]. A hard physical requirement D instead needs a model bound
no larger than floor(D/Δ); rounding it upward could permit late physical behavior.
If a necessary bound rounds to zero or intervals conflict, refine Δ or the
abstraction. Include approximation error in any end-to-end budget. Common scaling
of a fixed model preserves its dimensionless timing ratios; selecting new
hardware does not necessarily preserve those ratios or the model assumptions.

A measured maximum or percentile is not a universal bound. A statistical envelope
must record its coverage, confidence, sample count and unobserved tails; a claim
under that envelope remains conditional. If exceeding a bound is included in the
fault envelope, represent it explicitly. If invariants exclude it, state that the
result does not cover it rather than claiming an existing failure path handles it.

5QI 82's 10 ms packet budget (historical source S2) is an example for a compatible
communication QoS flow with specified endpoints, not every `D_*`, a controller
response bound or a complete sensing SLA. No physical Δ is selected here.
[Pinned P1 sources and applicability](https://github.com/artmus208/uppaal_sdn_isac/blob/4480f1087b93f48541a925590ae82ca86fa4b808/evidence/validation/20260907-p1/sources.md).

## PHY definitions and formulas adopted in this revision

These definitions make the report internally consistent. They interpret or
qualify the formulas in the pinned PHY TeX; they do not assert that a physical
estimator, dataset or new UPPAAL variable has been supplied. Symbols with new
subscripts below clarify the mathematics and are not additional inventory rows.

### Signal quality, powers and configuration

Use **linear** power ratios in the physical formulas:

\[
\gamma_c=\frac{S_c}{I_c+N_0B},\qquad
\gamma_s=\frac{S_s}{I_{c\to s}+I_{self}+I_{mutual}+N_s}.
\]

All powers in each ratio refer to the same receiver reference point, bandwidth
and declared averaging interval. Powers are nonnegative; denominators must be
positive. With `N_0` in W/Hz and `B` in Hz, `N_0 B` is W. It assumes the relevant
noise spectral density is adequately constant over the band; otherwise integrate
the density over the receiver's effective bandwidth. Include receiver noise
effects in the chosen equivalent noise definition rather than counting them twice.
Likewise, communication leakage, self-interference and mutual sensing interference
must be defined without overlapping contributions. Treat powers as additive under
the declared uncorrelated/averaged interference model; a coherent signal model
requires the corresponding cross terms or an effective aggregate definition.

The source names `SINR_c` and `SINR_s` denote these linear quantities. A separate
representation is `gamma_dB = 10 log10(gamma)` for gamma>0. Do not add dBm powers
or mix a dB threshold with a linear ratio. Linear gamma is never negative; the
historical demo cutoff 0 would make OUTAGE unreachable below that cutoff for
valid nonnegative linear input. Therefore the demo 0/10/25 cannot be adopted
silently as a physical profile. Symbolic physical thresholds need no numerical
choice now; a nonempty low-SINR outage region requires an appropriate positive
boundary. Missing input is not the numerical value zero or a good nominal value.

`P_t` is a transmitted-power/configuration or monitored quantity; `P_r` is
received power, which is not necessarily the useful component `S_c` or `S_s`.
`L_p` must specify linear loss or dB loss. `B`, `f_c` and `Delta f` are usually
configuration/context values, even though the original vector lists them among
measurements. A vector position does not make a quantity independently measured
or freely variable. Signal/noise powers, SINR, BLER, CQI, detection and resource
classes have dependencies determined by the selected physical configuration;
the abstract environment must state which dependencies it retains or relaxes.

### Detection, false alarms and estimator outputs

For one declared decision opportunity, let H0 mean no target and H1 mean a target
is present, and let `Z > gamma_det` be the chosen detection rule:

\[
P_d=\Pr(Z>\gamma_{det}\mid H_1),\qquad
P_{fa}=\Pr(Z>\gamma_{det}\mid H_0).
\]

Both lie in [0,1]. Empirical estimates, when observations exist, are

\[
\widehat P_d=\frac{N_{det}}{N_{present}},\qquad
\widehat P_{fa}=\frac{N_{false}}{N_{absent}},
\quad N_{present}>0,\ N_{absent}>0.
\]

An empty denominator gives an unavailable estimate, not 0 or 1. P1 already
defines target-present trials correctly, and PHY TeX already describes statistical
KPI as estimates; the hats and explicit denominators remove notational ambiguity.
Define the opportunity (cell, scan or target decision), observation window and
ground-truth/association rule. An individual detection event is not `PdClass=OK`.
For the same binary decision experiment, missed-detection probability is 1-P_d;
do not impose that identity across different windows or class definitions.

In this revision, historical `Rfa`/`Rfa_max` in CFAR and its probability-based
quality predicates mean `P_fa`/`P_fa,max`. Keep `RfaClass` as the existing interface
name; a future schema migration is a separate change. A false-alarm **intensity**,
such as `lambda_fa = E[N_false(T)]/T` in s^-1, needs a different symbol, exposure
and thresholds. An area-normalized intensity needs its own area/time denominator.
There is no universal conversion without the opportunity process. For M identical
opportunities in duration T, expected count is M*P_fa and mean intensity is
M*P_fa/T; probability of at least one alarm additionally depends on dependence
between opportunities. Do not substitute either count or intensity into CFAR.

`P_d(P_fa)` is shorthand for a detector operating curve at fixed signal,
background, processing and target assumptions, not a complete physical law.
Changing a threshold trades detection against false alarms. The model may use
abstract classes without measuring this curve, but no actual detection quality
is inferred from that choice. [Detection definitions](https://www.mathworks.com/help/radar/ug/receiver-operating-characteristic-roc-curves-part-2-monte-carlo.html).

### CA-CFAR: a conditional external-estimator example

Write the source formula with explicit meanings:

\[
\widehat p_n=\frac{1}{N_{ru}}\sum_{j=1}^{N_{ru}}X_j,\qquad
S_{thres}=N_{ru}\bigl(P_{fa,design}^{-1/N_{ru}}-1\bigr)\widehat p_n.
\]

Here `N_ru` is a positive integer number of training cells, `X_j` are power
samples, `p_n` is their **mean**, and 0<P_fa,design<1 is a target probability per
cell under test. `S_thres` and `X_j` have the same units. The usual coefficient
assumes homogeneous independent exponential noise-power samples (from complex
Gaussian noise after square-law detection), with the noise-only test cell
independent of the training cells and no additional pulse integration. Guard
cells exclude target leakage. Correlated/nonhomogeneous clutter, contaminated
training cells or other accumulation rules require a corresponding detector
model/coefficient. A design probability is not an observed guarantee.

This formula is an optional external-estimator illustration, not part of the
finite automata and not a required implementation task for the abstract article.
[CA-CFAR definition and coefficient](https://www.mathworks.com/help/radar/ug/constant-false-alarm-rate-cfar-detection.html).

### Accuracy requirements and Cramer–Rao bounds

Define nonnegative errors `e_r = abs(r_hat-r)` and `e_v = abs(v_hat-v)`. Adopt
`Delta r=e_r`, `Delta v=e_v` when interpreting the source requirements:

\[
\Pr(e_r\le l_a\mid\mathcal D)\ge q,\qquad
\Pr(e_v\le v_a\mid\mathcal D)\ge q_v,
\]

where l_a>0 is in m, v_a>0 in m/s, 0<q,q_v<=1, and D is the declared successful
detection/valid-association event. Report detection failures separately. A
claim about overall successful service also needs the probability of D and any
joint error requirement; two marginal inequalities do not prove the same joint
probability. If another unconditional error convention is intended, define its
handling of misses explicitly. This conditional convention is a report-level
clarification, not a claim that the original source specified it.

For a consistent scalar input to the source penalty, `Acc_r` and `Acc_v` may be
defined as the q and q_v quantiles of these absolute errors under D. This is the
convention adopted here for interpreting those penalties. Mean error, RMSE,
standard deviation and a quantile are not interchangeable; another estimator
must declare a different mapping. At q=1 an unbounded distribution may have an
infinite quantile, so no finite tolerance is guaranteed. No error data are
asserted to exist in the candidate.

For an unbiased estimator and a regular identifiable statistical model with
nonsingular Fisher information J, the vector bound is

\[
\operatorname{Cov}(\widehat{\boldsymbol\vartheta})
\succeq J(\boldsymbol\vartheta)^{-1}.
\]

CRB_R, CRB_v and CRB_theta denote the corresponding diagonal lower bounds on
variance, with units m², (m/s)² and rad². Their square roots have the associated
error units. Bias, singular information or nonregular models require an
appropriate different bound. A small lower bound does not establish that a
particular estimator achieves a small error or a required tail probability.
`CRBClass` and `AccClass` therefore describe different information. The vector
listed in the original TeX is a list of bounds, not a formula computing them.
When comparing a bound with conditional accuracy, ensure both refer to the same
observation/selection model; conditioning on successful detection can change
that statistical model.
[Conditions and interpretation of the bound](https://ocw.mit.edu/courses/14-381-statistical-method-in-economics-fall-2018/15224973dfc1c2b4287804c8712681f7_MIT14_381F18_lec6.pdf).

### Capacity and coverage

Retain the original P1 meaning of **simultaneous** target count:

\[
C_s(Q_s,T_0;\mathcal C)=\frac{N^*(Q_s,T_0;\mathcal C)}{A},\qquad A>0.
\]

The explicit context C fixes region, target population/geometry assumptions,
radio/estimator configuration, resource budget and scheduling policy. N* is the
largest studied simultaneous target count for which **every target** meets the
declared quality requirements over the fixed observation window under that
context. If an average or a service percentile across targets is desired instead,
it is a different, explicitly specified capacity definition. Existence of a
finite attained maximum is not supplied by the fraction itself.

The source `Q_s=(l_a,v_a,Pd_min,Rfa_max,q,q_v,T_0)` contains detection and accuracy
requirements; this revision interprets `Rfa_max` as P_fa,max. It does not silently
claim that Q_s already contains freshness or update-rate constraints. Include
those explicitly if a service-capacity claim requires them. Statistical
probabilities over trials are not empirical frequencies of a supplied dataset.

C_s is in targets/m², not bit/s or targets/s. Specify the 2D region/altitude
interpretation for airborne targets; a volume-based definition would use a
volume and different units. `A_cov` must identify covered area (m²); if the
reported KPI is a fraction, use `a_cov=A_cov/A` with a stated coverage predicate.
Neither a single-UAV abstraction nor an externally selected `CapClass` computes
physical multi-target capacity. The formula defines the metric to which a future
estimator could map; it is not a capacity result.

### Resource share, beam management and scores

`u_s=T_s/T_0` is a **time fraction** when T_s is the duration of the union of
sensing-active intervals in T_0. Allow u_s=0 for inactive/no allocation; the
source 0<u_s<=1 applies only to the active-sensing condition. Shared ISAC symbols
can serve both functions, so `u_comm=1-u_s` is not generally implied. Frequency,
power and compute shares need their own resource definitions.

For the source expression

\[
\Omega_{BM}=\min\left(1,
\frac{N_{SSB}T_{SSB}+N_{PRS}T_{PRS}+T_{ctrl}+T_{report}^{dur}}
{T_{frame}}\right),
\]

all terms must describe the same resource and accounting frame, T_frame>0.
`T_report^dur` distinguishes report airtime from the TA report-period constant
named T_report; it clarifies notation without creating a generated variable.
Summation gives occupied time only for nonoverlapping exclusive intervals.
Otherwise use their union or a consistently defined time-frequency resource
measure. End-to-end waiting latency cannot automatically count as radio airtime.
If the numerator is demanded rather than occupied resource, preserve its ratio
above 1 as overload and define the clipped quantity separately as a saturated
score. Clipping must not be used to claim feasibility of an overloaded schedule.

Define beam error epsilon_b as an absolute angular error/norm. For this report,
p_mis is a probability or opportunity-normalized fraction of misalignment at a
declared tracking decision, not a count per second. Use
0<=p_mis,warn<p_mis,max<=1 with a documented equality policy. A temporal duty
fraction of misalignment is a different metric unless equivalence is justified.
Protocol states such as SEARCH or LOCKED are not interchangeable with this
statistical quantity.

The source penalties have two general forms:

\[
\Pi_{shortfall}(x,b)=\max(0,(b-x)/b),\qquad
\Pi_{excess}(x,b)=\max(0,(x-b)/b),\quad b>0.
\]

Shortfall is used for linear SINR, P_d and C_s; excess for BLER, P_fa, the selected
error quantiles, age and nonnegative beam metrics. Every comparison uses one
consistent unit/convention. If a service requires a zero bound, this normalized
formula is undefined and needs a separately declared indicator/scale.
For nonnegative x a shortfall is at most 1; an excess can exceed 1, and the sums
inside Pi_Acc and Pi_BM can also exceed 1. Thus
`Pi_PHY = sum(w_i Pi_i)`, w_i>=0, sum(w_i)=1, need not lie in [0,1].
Missing/invalid input is not a zero penalty. A score is an external preference
measure, not a probability, a proof of optimality or a substitute for hard
service constraints. No numerical score weights or optimized policy are supplied
by this report.

### Information age and freshness

For a consumer with a usable delivered report, define

\[
AoS(t)=t-u(t),
\]

where u(t) is the source timestamp of its freshest usable delivered estimate,
not that report's arrival time. At arrival the age includes estimation/transport
delay and need not be zero. A delayed older report must not replace a newer
source timestamp. No delivered usable report means explicit missing/invalid
state, not an assumed fresh estimate. Distinguish poor quality from old age.
If an estimate summarizes a sensing window, declare which instant the estimate
represents; estimator completion is not automatically that instant. Physical
binding also accounts for synchronization error.
[Source-age interpretation](https://arxiv.org/abs/1601.02284).

The later integrated P2 classifier uses FRESH for age<5, STALE for
5<=age<10, EXPIRED for age>=10, plus report validity. These are abstract policy
boundaries, not a measured UAV freshness tolerance. Their worse-side equality
is distinct from a response deadline that explicitly permits response at c=D.
P2's overwrite/missing rules are the limited implementation described above;
the general definition here does not assert that every multi-source scenario
is implemented.

## Threshold calibration and finite domains

For an ordered scalar domain, record its metric, increasing/decreasing quality
direction, adjacent symbolic boundaries, equality rule and validity condition.
For a policy/categorical domain, define predicates and priorities rather than
inventing scalar thresholds. Abstract finite inputs may be specified without a
raw-metric classifier. Keep all intended classes, including STALE and SUSPECTED,
reachable under the declared environment; list excluded combinations and reasons.

Use the declared worse-side equality as an abstraction policy, not as a physical
law. For increasing quality and boundaries b1<b2<b3 it can mean OUTAGE for x<=b1,
LOW for b1<x<=b2, OK for b2<x<=b3 and HIGH for x>b3. Physical service inequalities
and any intentionally stricter class policy must be distinguished. Historical
demo behavior and the PR correction have the version-specific status above.

If an uncertainty set crosses classes, define the set of admissible abstract
behaviors or justify an ordered abstraction that covers them. A worse label
alone does not prove transition coverage or safety preservation. Confidence
intervals are not certain bounds. Explicitly handle missing, NaN/infinite and
out-of-domain values (for example a probability outside [0,1]); never replace
them with nominal success. Hysteresis/debounce requires explicit memory/timing
semantics if used. For physical fitting, separate calibration from evaluation
by independent runs/scenarios; this is conditional future work, not a performed
experiment.

### PHY classes

The following table covers all 28 PHY domains in the historical inventory.
The middle column is sufficient to define the abstract interface. The last
column identifies the additional evidence needed for a physical interpretation.

| Domains | Abstract meaning and consistency required now | Physical mapping when claimed |
|---|---|---|
| SINRClass, BLERClass, CQIClass | Distinct classes of linear signal-to-interference-plus-noise ratio, block error probability and configured quality indicator. No universal identity between them. | Declare receiver/waveform, MCS/CQI table, bandwidth, HARQ and observation stage; use the associated SINR–BLER relation (S1/S3/S4). Preserve correlation assumptions and distinguish channel estimates from actual decoding outcomes. |
| IClass, PowerClass, DopplerClass, DelaySpreadClass | Specify interference and useful-power reference points, magnitude of Doppler if direction is irrelevant, and nonnegative RMS delay spread. High transmitted power is not universally better sensing because leakage/interference can change. | Powers in W or explicitly converted dBm, Doppler in Hz, RMS delay spread in s. Assess against waveform/receiver tolerances and mobility/interference assumptions; do not identify signed Doppler with its magnitude silently. |
| DRTClass, PilotDensityClass, PayloadSenseClass, PRSClass | Supported estimator/configuration capabilities and resource-pattern sufficiency; categorical choices need a declared interpretation, not a fabricated scalar. | Define DRT/configuration indicators, pilot/PRS denominator and grid, payload availability and receiver support. Validate each selected configuration; no universal threshold is supplied. |
| BeamErrorClass, BlockageClass, MisClass, BMOverheadClass, BeamClass | Separate angular error, suspected/confirmed obstruction, misalignment probability, occupied/saturated resource indicator and protocol state. Retain SUSPECTED and define competing-alarm priority. | Declare angle units, observation opportunities, blockage evidence, beam geometry and resource accounting. Evaluate tracking/recovery under the chosen configuration; low power alone does not identify blockage causally. |
| PdClass, RfaClass | Classes of P_d and probability-per-opportunity P_fa; detection events and probability classes differ. Missing evidence remains invalid. | Labeled target-present/absent trials at fixed context/window or a specified analytical detector model; evaluate the joint operating point and uncertainty. An intensity requires a separate metric/mapping. |
| AccClass, CRBClass | Absolute-error quantile requirements and model-dependent variance lower bounds, respectively. A good CRB class does not establish achieved error. | Specify detection/association conditioning, q/q_v, ground truth, error distribution and estimator assumptions. Keep variance, square root and quantile units distinct. |
| AoSClass | Source age plus explicit validity; define FRESH/STALE/EXPIRED and late/old/missing-report behavior. The P2 5/10 policy is abstract. | Specify source/consumer timestamps, represented measurement instant, synchronization uncertainty and service tolerance; assess delivery and loss effects. |
| CapClass, CoverageClass, ResourceShareClass | Respectively simultaneous-target capacity category, region coverage and allocated-resource sufficiency. No enum value is a count, density or packet capacity. | Fix region, window, per-target quality, schedule and denominator; distinguish covered area from coverage fraction and time share from exclusive resource share. |
| ChannelClass, SignalClass, SensingState, PHYState | Derived policy states; specify lower-level predicates, priorities, completeness and recovery. State names are not independent physical measurements. | Relate source predicates to a supported estimator/configuration. A classification fitted only to reproduce the model's own outputs is not independent validation. |

### MAC classes

The following physical quantities define a possible future mapping. The current
abstract model may select their classes directly; it does not thereby contain a
packet-level queue or a measured service curve.

QueueClass: packet/byte queue occupancy and residence time under an arrival/service
envelope; derive warning/critical/draining partitions with an explicit buffer size.
BufferClass: occupancy relative to capacity and actual overflow events. DelayClass:
scheduling age relative to the allocated service deadline and a declared warning
margin. DropClass: drop counts/exposure or loss fraction in a pinned window.
ResourceClass: available PRBs/slots/airtime versus requested resources, with
RES_EXHAUSTED tied to infeasibility rather than an arbitrary enum value.
KPIFreshnessClass: source data age and missing-report timeout, using the freshness
method above. CommDemand/SensingDemand: service-request quantities and criticality
mapped by a documented admission policy. ScheduleMode/MacReason: derived policy
choice and diagnostic cause; validate totality/priority and cause preservation.
No numeric occupancy, retry limit or loss-rate threshold is specified in the
current MAC profile. Explicit abstract class semantics are required now; queue
capacity/arrival/service data are required for a physical queue-capacity claim.

### SDN classes

TelemetryClass uses data age, completeness and missing-report timeout. RiskClass
uses an explicit ordered rule combining constituent alarms; LOW/MED/HIGH/CRIT
must be auditable against those rules, not an unexplained risk score. SliceClass
requires requested versus available resources and admitted service obligations.
PolicyClass, RuleClass, RecoveryClass, ServiceImpact and SdnReason describe protocol
or policy outcomes: use command/ack/timeout/recovery logs and the transition table,
not physical threshold fitting. Check simultaneous alarms, stale/missing inputs,
policy fallback and preservation of rejection reasons across APP interfaces.

### Application classes

ServiceClass, CriticalityClass, DemandClass and RequirementClass are service/policy
inputs; register the exact service contract and translate RELAXED/NORMAL/STRICT
into explicit limits. DetectionFreshnessClass and UpdatePeriodClass use sample
age and consecutive update timestamps (common abstract units, or s after binding). FalseAlarmClass, MissedDetectionClass
and PdClass use declared statistical meanings and service-specific limits; a
physical instantiation additionally needs corresponding trials/exposure or an
appropriate analytical model. Retain the same probability/rate distinction as PHY.
QualityClass is shared by multiple quality variables: bind each variable to its
metric and unit before using OK/LIMITED/FAILED. SLAClass derives from the conjunction
of service requirements and criticality; AdmissionClass and DegradedReason record
decisions/causes. Validate degraded acceptance against the selected service rules,
including safety-critical requests. In the P2 candidate, preserved request fields
do not demonstrate enforcement of every strict requirement; Crit/Agg placeholders
and unimplemented application reconfiguration limit claims. A shared enum does
not imply shared thresholds or demonstrated full SLA behavior.

## Symbolic estimator parameters and unresolved numerical inputs

The source line numbers below refer to the pinned PHY TeX, whose SHA256 is
`b121fb122e68edbc92b2b2f3dd4e86d954fce0c56760d97dcecc77270ea125df`.
These are source symbols, not an assertion that all are executable inputs.
Definitions below follow this revision's conventions. Most numerical values
remain deliberately unassigned for the abstract article. Requirements,
configuration and estimated values must not be conflated merely because the
source puts them in one input vector.

| Parameters (source lines) | Role, domain and binding decision |
|---|---|
| SINR_out, SINR_min, SINR_high (180–188); BLER_max (786) | Ordered thresholds on linear SINR and a probability-per-transport-block requirement. Physical values require a configured link model. Historical demo 0/10/25 is not adopted as a physical profile. Positive denominator required for the SINR penalty. |
| Pd_min, Rfa_max/Rfa^max (730–754) | Detection and false-alarm **probability** requirements for defined opportunities; interpret Rfa_max as P_fa,max here. Physical values stay symbolic; zero bounds need a different penalty normalization. Distinguish configured P_fa,design from measured P_fa. |
| l_a, v_a, q, q_v (738–754) | Positive absolute-error tolerances and coverage probabilities in (0,1]; requirements, not achieved errors. Define conditioning and whether marginal or joint accuracy is needed. Acc_r/Acc_v use the declared quantile convention. |
| T_0, A, N*(Q_s,T_0), C_s^min (746–754, 791) | Observation window, fixed region area, simultaneous feasible target count and required target density. The all-target rule and context C are explicit in this revision. N* is derived, not an arbitrary tuning constant. No numeric capacity is computed here. |
| T_s, u_s (758) | Allocated sensing duration and its fraction of T_0>0. Active sensing uses 0<u_s<=1; inactive/no resource permits 0. Shared sensing/communication time is not necessarily exclusive. |
| AoS_max (790); AoS_BS, AoS_CTRL timestamps (762–768) | Consumer source-age requirement and age estimates/clocks, in common units. Receipt time is distinct. P2's 5/10 age policy and validity are separate from the old demo's single cutoff 10. |
| epsilon_max, p_mis^warn, p_mis^max, Omega_BM^max (490–499, 795) | Positive angular tolerance, ordered probability-per-tracking-opportunity limits and a resource-fraction limit. p_mis^warn appears in the source classification and is included here explicitly. Actual values remain unassigned. |
| N_SSB, N_PRS, T_SSB, T_PRS, T_ctrl, T_report, T_frame (499) | Nonnegative event counts/durations and a positive accounting frame. Specify repeated-event count and nonoverlap/union rule. T_report in this estimator is a report duration, not automatically the TA period with the same name. |
| N_ru, p_n, S_thres (733–735) | Positive training-cell count; mean reference-cell noise power; derived CA-CFAR threshold. Apply the explicit conditional formula above; intensity is not a valid replacement for P_fa,design. |
| N_det, N (731); gamma_det (159) | Successful detections, target-present opportunity count and detector threshold/configuration. Use N_present>0 and P̂_d for the fraction; missing trials do not produce an estimate. Define the statistic and threshold units. These source symbols were not separate numerical TA constants. |
| D_cmd (573) | Source symbolic command-delivery assumption, bound to 1 abstract unit in later P2. Distinguish delivery from completion/success; a physical interpretation requires matching send/receive endpoints. |
| w_i (798–801) | Nonnegative external preference weights summing to one; chosen configuration, not empirical probabilities. Specify normalization, sensitivity and hard constraints separately. No verified optimizer or score in [0,1] is implied. |
| P_t, P_r, S_c, S_s, N_0, N_s, I_c, I_c→s, I_self, I_mutual, L_p; B, f_c, Delta f (142–160) | Powers/PSD/loss and bandwidth/frequencies with explicit receiver references and SI/log conventions. B/f_c/Delta f and usually P_t are configuration or monitored settings; other powers may be estimated/derived. Do not vary all independently while claiming one physical link. |
| sigma_tau, f_D, epsilon_b, p_mis, Omega_BM, Pd, Rfa, Acc_r, Acc_v, CRB_R/v/theta, C_s, A_cov (155–157) | Nonnegative RMS spread, signed or magnitude Doppler as specified, angular error, misalignment probability, occupancy indicator, statistical estimates/bounds, capacity and covered area. Their units, conditioning and aggregation are given above. These are not all freely chosen physical thresholds. |
| MCS, W, rho_p, kappa_DRT, psi_cs, psi_ps, theta_b, G_b, n_B (158) | Coding/waveform and supported configuration indicators; pilot fraction, beam angle/gain/count as explicitly defined by the estimator. Declare each indicator domain and dependencies; names alone do not supply a universal quantitative definition. |
| tau_SSB, T_SSB, T_PRS, N_RE^PRS, delta_PRS, S_t, S_f, T_s, gamma_det (159) | Schedules/durations, resource-element counts, temporal/frequency grid patterns and detector configuration. Pin numerology/grid and distinguish time from frequency spacing. Repeated symbols refer to the same declared quantity only when definitions match; tau_SSB's generated clock value does not establish a physical conversion. |

For reproducible abstract runs, retain the selected executable parameter set,
instance vector, source/model/query hashes and the explanation of each varied
parameter. Symbolic physical placeholders are documented as unbound rather than
filled with fabricated measurements. If a declaration is unused, identify that
fact in the implementation review; declaration alone is not an enforced contract.

## V01 — Adequacy of automata and composition

For an abstract article, steps 1, 2 and 4 assess the declared event/interface model.
Steps involving physical traces or a concrete simulation relation are required
when the corresponding physical correspondence claim is made, not merely because
a symbolic PHY quantity appears in the specification.

1. Define the operating envelope independently of the generated automata: abstract
   topology/instances, allowed events, traffic and mobility classes, supported
   configurations, resource categories, service requirements, losses/failures
   and uncertainty. Record which cases are
   excluded and how assumption violations are exposed.
2. For each automaton map each observable location/edge to a specified protocol
   or estimator-interface event; substantiate its physical meaning if claimed.
   Identify hidden actions, timer starts/resets, payload ownership,
   decision priorities and allowed delays. Use interface/transition tables from
   P2; a table derived solely from the generated XML is not independent validation.
3. For a claim transferring properties to a concrete system, define a relation R
   between its concrete states (including uncertainty) and finite states.
   Check initial-state coverage, predicate preservation, concrete delay
   coverage and matching of every relevant concrete transition, possibly through
   explicitly justified internal abstract steps. For composition check shared
   variables, channel kinds, identifiers, simultaneous events and scheduling.
   Worse-class labeling alone establishes none of these obligations.
4. Exercise boundary equalities, timeout/ack coincidences, stale/dropped/reordered
   reports, conflicting alarms, resource exhaustion, recovery/rollback and repeated
   overlapping requests. Test individual automata and complete cross-layer event
   chains. Confirm that each component's assumptions are supplied by other
   components/environment without circular reasoning. Closed layer stubs are not
   evidence for the integrated system.
5. When claiming empirical correspondence, compare held-out concrete traces
   against the abstraction and inspect mismatches.
   Classify unsafe under-abstraction, harmless extra abstract behavior, wrong
   interface/reset, invalid trace and out-of-envelope cases. Report counts and
   denominators by scenario; retain counterexamples. Resolve violations before
   making the corresponding adequacy claim.
6. A mathematical simulation/over-approximation argument can justify transfer of
   the specified safety predicates only under its assumptions. Finite trace tests
   supply empirical evidence for sampled conditions. They do not prove the
   relation universally, liveness/fairness or probabilistic service reliability.
   P3 subsequently checks named queries on the separately frozen model.

## V04 — External data exchange and validation experiment

The following physical-data workflow is proposed, not executed. It is an
extension route; the abstract study can instead use declared finite event
scenarios, which are not measured traces. No automatic closure of V04 follows
from choosing that abstract scope.

Proposed physical workflow: external simulation/measurements → immutable raw
trace → calibrated estimator → timestamped finite events → P2 environment adapter
and trace-conformance check → mismatch report. Reverse replay of a P3 counterexample
uses the same configuration and reports whether it is realizable, spurious or
unresolved. A new abstraction after a mismatch requires new hashes and reruns.

For ns-3, instrument source generation, transmit/receive/drop, scheduler decisions
and link-quality observations at their native trace sources; retain node/device/
flow IDs and simulator times. S4 documents the LTE abstraction only: select and
pin a suitable radio module and add a separately validated sensing estimator.
For OMNeT++, register the required signals, record timestamped vectors and run
attributes (S5), and export event order alongside metrics. Scalar summaries cannot
replace the event stream. Pin the radio/network framework as well as OMNeT++.

The proposed **physical-time** exchange consists of JSONL events and a manifest.
Required event
fields: `run_id`, `scenario_id`, `event_id`, `sequence`, `entity_id`, `flow_id`,
`transaction_id`, `event_kind`, `t_observed_s`, `t_sample_s` when available,
`metric`, `value`, `unit`, uncertainty bounds when available, `config_id`,
`raw_reference`. Absent uncertainty information is null plus a reason, not zero
uncertainty. Fields ending in `_s` contain seconds only after physical time has
been bound; an abstract trace must use explicitly named model-time fields with
`time_basis=model_unit`, not silently put abstract values into `_s`. This is a
report-level exchange proposal, not an implemented adapter or schema migration.
Derived events additionally carry `class_name`, `class_value`, `alpha_version`
and `parameter_set_hash`. Missing values are explicit null plus reason, never
nominal defaults. Reject nonfinite numeric values and inconsistent units.
Enforce monotone observation time per ordered source, preserve simultaneous events,
and keep original sample timestamps across delivery and reordering.

The run manifest records simulator/module version and commit, scenario/config
hashes, seeds, topology/instance vector, radio/traffic/service settings, estimator
version, parameter/adapter hashes, time scale, host/environment, command and raw
stdout/stderr/data hashes. This is a proposed contract; no production adapter or
real JSONL dataset is supplied by P1.

If physical calibration/evaluation is undertaken, choose scenarios and acceptance
criteria before fitting; split by independent run/scenario rather than adjacent
rows; fit thresholds on
calibration data; freeze them; run boundary/failure cases and held-out scenarios.
Use independent ground truth for detection/quality instead of classifying model
outputs against themselves. Report sample/exposure counts, false alarms, misses,
unsafe class assignments, latency/age distributions, conformance mismatches and
confidence intervals with their estimation assumptions. Declare acceptable unsafe
error rate/confidence, deadline coverage and test-envelope coverage before the run;
P1 does not invent a scientifically justified universal pass percentage.

The author may propose an explicitly abstract case study with declared model
units and assumptions; this can be a deliberate research scope even before
hardware selection, rather than a claim of physical calibration awaiting data.
It must not be described as physically calibrated or empirically validated. Approval of that
claim scope belongs to the independent reviewer/integrator.

## Validation claims and handoff

This table distinguishes the historical P1 package, clarifications made in this
local revision and evidence still needed for acceptance or stronger claims.

| ID | Available description/evidence | Remaining decision or evidence |
|---|---|---|
| V01 | P1 adequacy methodology; later P2 interface/implementation descriptions; explicit abstract/physical claim distinction here | Review event meanings, composition, environment coverage and implementation limits. A physical transfer claim additionally requires a justified concrete relation or appropriately limited empirical evidence. |
| V02 | Historical finite-domain inventory and demo observations; explicit physical meanings/equality/validity rules here; P2 finite-input decisions | Accept or revise the chosen abstract predicates and domain restrictions. Review the separately proposed raw-mapper correction. Numerical deployment thresholds are required only for deployment-specific mapping claims. |
| V03 | Historical 43-constant table, explicit 12-constant PHY subset and abstract-unit method; later P2 timing choices identified separately | Select and review the complete integrated parameter set and timing composition. Physical Δ is needed for physical deadlines, not for model-unit claims. No profile name proves conservativeness. |
| V04 | Proposed simulator/export/estimator/conformance workflow, with explicit physical vs model-time fields | Review the scope of the proposed interface; implemented adapter and executed data comparison are needed before claiming demonstrated integration. Synthetic finite scenarios are not empirical validation. |
| V05 | Original source inventory plus explicit parameter roles and source-symbol clarifications | Independently review provenance and choices. Preserve historical hashes; any repository revision must create its own updated evidence instead of reusing old hashes as if they covered changed text. |

For P1/P2 review, consider the conventions now stated explicitly: linear SINR;
P_fa as a probability per opportunity; conditional CA-CFAR with mean training
power; probability estimates with valid denominators; absolute-error/quantile
semantics; variance-bound interpretation of CRB; simultaneous per-target capacity;
consistent resource and score accounting; abstract clock units and source age.
These are corrections to this report's descriptions, not assertions that the
TeX/generator or scientific gate has already adopted each convention.

The existing P2 source-age, missing-data and D_cmd decisions must be reviewed with
their implementation limits rather than requested again as if absent. Full APP
behavior, numeric packet/retry bounds, physically constrained input combinations
and multi-source telemetry remain limited or unimplemented where the P2 evidence
says so. Review the exact selected artifacts and align source notation through
the responsible workstreams. Only P9a/P9b changes the unified manuscript.

This revision does not mark V01–V05 closed, P1/P2 accepted or Gate 1 passed. No P3/P4
run is started. Scientific acceptance of the abstract scope and any stronger
physical claims remains an independent decision.

## Revision summary

- Made hardware-independent parameter justification explicit throughout, with
  physical calibration conditional on deployment/empirical claims.
- Preserved historical observations while adding the later P2 disposition and
  the dated, unmerged status of the raw-mapper correction.
- Defined PHY probabilities, dimensions, estimator assumptions, absolute errors,
  CRB, capacity, resource shares, penalties and information age consistently.
- Added all 12 historical PHY clock values and clarified their abstract roles;
  included source symbols such as p_mis^warn and N_det/N without changing the
  historical inventory count or inventing calibrated values.
- Retained all original finite-domain families and timing groups; clarified
  abstract versus physical interpretation in the cross-layer parameter sections.
- Retained the proposed external-data methodology and made model-time/second
  fields, missing uncertainty and the limits of each claim explicit.

The accompanying revision record and patch document the actual file change.
Document checks confirm source/parameter coverage and text consistency only;
they are not model checking, physical validation or independent acceptance.
