# P1 — Validation method and parameter provenance

Issue: [#15](https://github.com/artmus208/uppaal_sdn_isac/issues/15).
Owner: artmus208. Atomic IDs: V01–V05. Independent acceptance: pending.
Input: `read` commit `f2f714a26d6b9d9f538ef1a16b53c3e060768a11`.
Baseline: `reviewer-r1-candidate`, not frozen; manifest SHA256
`89b8d6f520546c873649643b3cf90fd80f58e4458a443832369e3d1d28bf719a`.
Write scope: `evidence/validation/20260907-p1/**`.

This deliverable provides the parameter inventory and a validation specification.
It does **not** establish empirical adequacy of the four-layer model. There is no
accepted integrated model, calibrated deployment profile, imported network trace
or model-checking result in this package. P2 and independent review must resolve
the decisions below before Gate 1 can freeze inputs.

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
number in prose. Class mappings without numeric definitions are included below
as unresolved calibration obligations. Symbolic estimator parameters are covered
in the tables below; they are not invented UPPAAL constants. The scanner is not a
general TeX parser or an empirical validator.

## Demonstrated findings

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

## Timing calibration

The following method applies to **each** of the 43 rows of `parameter-table.md`.
Its current value, profile alternatives and source locations are in that table
and JSON. No current value is relabelled as a standard-derived physical bound.

For each row, register: trigger event, terminal event, clock reset, measured
endpoints, physical unit, included waiting/transport/processing, service budget,
operating envelope, measurement source/uncertainty and chosen rounding. Correlate
events by transaction/session ID; an unrelated acknowledgement cannot terminate
the interval. Separate response guarantees from environment timing assumptions.

| Layer and parameters | Measurements/requirement and calibration procedure |
|---|---|
| PHY `D_meas`, `D_sig`, `D_sense` | Timestamp measurement request→classification, configuration command→applied signal configuration, sensing trigger→classified result. Include estimator window/compute delay and declared load. Obtain bounded envelopes or declare statistical coverage explicitly. |
| PHY `D_BM` | Recovery command→restored/failed/handover outcome. Measure sweep, detection, processing and control transport at declared beam count and blockage regime; choose a recovery requirement including explicit failure outcome. |
| PHY `D_child`, `D_net`, `D_report` | Child report creation→aggregate receipt; network send→controller delivery; aggregate trigger→KPI publication. Specify queuing, loss, reorder, retransmission assumptions and separate them from CPU time. |
| PHY `T_meas`, `J_meas`, `T_report`, `tau_SSB`, `J_SSB` | Configured sampling/report/sweep schedule plus observed inter-event spacing and jitter; record numerology and timer resolution. Declare whether jitter is one-sided or symmetric. These seven non-profile constants (including D_child/D_net) stay fixed across built-in profiles. |
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

Pin one positive scale Δ, in seconds per model time unit. UPPAAL clocks remain
dense-time; integer constants do not imply discrete time steps. Convert an
environment interval [L,U] outward to [floor(L/Δ),ceil(U/Δ)] when constructing an
over-approximation. A hard physical requirement D should instead use a model bound
no larger than floor(D/Δ); rounding it upward could permit late physical behavior.
If a required bound rounds to zero or the intervals conflict, refine Δ and the
abstraction. Timing approximation error must be included in the composition budget.

A measured maximum or percentile is not a universal upper bound. For a stochastic
envelope record percentile, confidence, sample size and unobserved tails; make the
ordinary TA claim conditional on that envelope. Reproducing one successful trace
does not justify an all-executions deadline claim. The failure/timeout path must
remain represented when an assumed bound is exceeded.

A sourced magnitude example is 5QI 82's 10 ms packet budget (S2). It is a useful
communication-budget reference for a compatible discrete-automation QoS flow,
not authority for setting every `D_*` to 10 ms or for a universal sensing SLA.
No physical Δ is selected here. Sources and applicability are in [sources.md](sources.md).

## Threshold calibration and finite domains

For each ordered quality domain record adjacent boundaries, unit, estimation
window, configuration, uncertainty interval and unsafe direction. Fit on calibration
runs; evaluate on separate runs/scenarios. At equality use the declared worse
adjacent class after P2 resolves the current conflict. Where uncertainty crosses
several classes, the chosen abstraction must cover all resulting behaviors; simply
choosing a worse label does not prove transition over-approximation. Hysteresis,
debounce and missing-value handling are explicit model decisions, not post hoc fixes.

### PHY classes

| Domains | Inputs, units and method |
|---|---|
| SINRClass, BLERClass, CQIClass | Pin linear ratio vs dB, waveform, MCS/CQI table, bandwidth, channel/receiver/HARQ configuration. Use measured or link-level SINR–BLER curves and the chosen service target; S1/S3/S4 justify this procedure. Calibrate OUTAGE/LOW/OK/HIGH separately. GOOD/WEAK/OUTAGE in the reviewer comment is conceptual vocabulary, not the current enum spelling. |
| IClass, PowerClass, DopplerClass, DelaySpreadClass | Calibrated powers/interference (W or dBm), Doppler (Hz), RMS delay spread (s), receiver sensitivity and waveform tolerance. Sweep each against decoding/detection performance under joint interference/mobility conditions; derive limits from allowable service loss. |
| DRTClass, PilotDensityClass, PayloadSenseClass, PRSClass | Pin waveform and estimator capability, pilot/PRS density and resource pattern, payload availability. Enumerated capability decisions need supported-configuration tests; density thresholds require quality-vs-resource measurements. An unsupported estimator is FAILED/BAD according to an explicit mapping. |
| BeamErrorClass, BlockageClass, MisClass, BMOverheadClass, BeamClass | Angular error (rad or degrees), blockage ground truth/confidence, misalignment frequency/probability and observation window, occupied beam-management time fraction. Calibrate against tracking/lock failure and usable throughput; distinguish measured quality from beam-controller protocol states. Specify suspected/confirmed evidence and failure recovery transitions. |
| PdClass, RfaClass | Ground-truth target-present/absent trials at fixed range, RCS, clutter, receiver and decision window. Pd = detections/target-present trials; choose either false alarms/target-absent opportunities (probability) or false alarms/time/area (rate). Calibrate the joint ROC operating point to service limits, with uncertainty, never from Pd alone. |
| AccClass, CRBClass | Range/velocity/angle errors (m, m/s, rad), independent ground truth and confidence/quantile targets. Estimate empirical errors; treat CRB as a model-dependent lower bound, not an achieved error guarantee. Pin estimator bias/model conditions and units of variance versus standard deviation. |
| AoSClass | Timestamp of represented sample, receipt, processing and current decision, clock synchronization error and service age tolerance in s. Define FRESH→STALE→EXPIRED separately and validate delayed/reordered/lost reports. The current demo has only one cutoff AoS_max=10. |
| CapClass, CoverageClass, ResourceShareClass | Target count meeting quality requirements over a fixed area and time window; coverage fraction/area with declared denominator; sensing resource fraction. Sweep target density, positions and resource load while retaining Pd/accuracy/freshness constraints. Pin LIMITED/FAILED/STARVED boundaries from required service and margins. |
| ChannelClass, SignalClass, SensingState, PHYState | Derived finite policy states, not standalone physical scalar thresholds. Trace back to lower-level class predicates and priority rules in defaults/generator; test conflicting inputs, complete domain coverage and recovery. Do not fit an arbitrary scalar to reproduce the code's own output. |

### MAC classes

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
current MAC profile; measurements and the capacity definition are still required.

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
age and consecutive update timestamps (s). FalseAlarmClass, MissedDetectionClass
and PdClass use labeled trials/exposure and service-specific statistical limits.
QualityClass is shared by multiple quality variables: bind each variable to its
metric and unit before using OK/LIMITED/FAILED. SLAClass derives from the conjunction
of service requirements and criticality; AdmissionClass and DegradedReason record
decisions/causes. Validate degraded acceptance against the selected service rules,
including safety-critical requests. A shared enum does not imply shared thresholds.

## Symbolic estimator parameters and unresolved numerical inputs

These definitions are in the PHY TeX, whose exact hash is in `inventory.json`.
They extend the executable timing inventory; most have no numeric model value.

| Parameters (source lines) | Unit/input and calibration or definition |
|---|---|
| SINR_out, SINR_min, SINR_high (180–187); BLER_max (786) | SINR unit unresolved; BLER probability per transport block. PHY radio-calibration method above; demo thresholds 0/10/25 have no empirical provenance. |
| Pd_min, Rfa_max/Rfa^max (730–754) | Probability versus false-alarm rate must be resolved. Service detection/false-alarm requirement plus labeled ROC calibration; demo Pd cutoffs 0.5/0.9 and Rfa 0.05/0.2 are illustrative. |
| l_a, v_a, q, q_v (738–754) | Allowed range/velocity error and required coverage probabilities. Obtain from service tolerance and independent error distribution; no current numerical values. |
| T_0, A, N*(Q_s,T_0), C_s^min (746–754, 791) | Observation duration (s), area (m²), feasible simultaneous target count and required density (targets/m²); capacity sweep under fixed Q_s. Do not substitute bits/s. |
| T_s, u_s (758) | Sensing time and fraction of observation window, 0<u_s≤1. Derive from actual schedule and required sensing quality, then validate contention. |
| AoS_max (790); AoS_BS, AoS_CTRL timestamps (762–768) | Freshness requirement/age in declared time units; demo AoS_max=10 is uncalibrated. Distinguish receipt age from information age. |
| epsilon_max, p_mis^max, Omega_BM^max (795) | Angular tolerance, misalignment limit with a denominator/window, beam-overhead fraction. Beam calibration method above; no fixed numeric thresholds. |
| N_SSB, N_PRS, T_SSB, T_PRS, T_ctrl, T_report, T_frame (499) | Counts and durations in the beam-overhead estimator. Pin frame/schedule and count overlapping resources consistently; a symbolic T_report here is not automatically the TA report-period constant. |
| N_ru, p_n, S_thres (733–735) | CFAR reference-cell count, estimated noise power and decision threshold. Pin detector/noise/clutter assumptions and measure ROC. The formula alone does not calibrate Rfa or guarantee its operating point. |
| D_cmd (573) | Symbolic beam-command delivery bound, not a generated declaration. P2 must bind it to a named interface deadline or explicitly remove the assumption. Use send→matching receive measurements. |
| w_i (798–801) | Dimensionless nonnegative external score weights summing to one. Document optimizer preference/normalization and sensitivity; not base-TA clocks, probabilities or verified optimality. |
| P_t, P_r, S_c, S_s, N_0, N_s, I_c, I_c→s, I_self, I_mutual, L_p; B, f_c, Δf (142–160) | Powers/noise density, path loss and frequencies: record SI/log unit conversions, link budget, equipment/propagation model and calibration reference. These feed the radio estimator, not TA guards. |
| sigma_tau, f_D, epsilon_b, p_mis, Omega_BM, Pd, Rfa, Acc_r, Acc_v, CRB_R/v/theta, C_s, A_cov (155–157) | Measured/estimated quantities, not freely selected thresholds. Use the corresponding PHY family method, recording uncertainty, measurement window and ground truth. |
| MCS, W, rho_p, kappa_DRT, psi_cs, psi_ps, theta_b, G_b, n_B (158) | Categorical/ratio/gain/angle/count configuration inputs; pin waveform, coding, pilot pattern, beamwidth/gain/count and definitions of estimator-specific indicators. Validate each supported configuration; no universal scalar thresholds are supplied. |
| tau_SSB, T_SSB, T_PRS, N_RE^PRS, delta_PRS, S_t, S_f, T_s, gamma_det (159) | Timing, resource counts/pattern/spacing and detector settings. Pin resource-grid units and receiver implementation; measure quality over that configuration. tau_SSB also has an illustrative generated clock constant; no physical conversion is established. |

## V01 — Adequacy of automata and composition

1. Define the operating envelope independently of the automata: deployment,
   traffic, mobility, radio/estimator configuration, topology, resource counts,
   service requirements, losses/failures and uncertainty. Record which cases are
   excluded and how assumption violations are exposed.
2. For each automaton map each observable location/edge to a real protocol or
   estimator event. Identify hidden actions, timer starts/resets, payload ownership,
   decision priorities and allowed delays. Use interface/transition tables from
   P2; a table derived solely from the generated XML is not independent validation.
3. Define a relation R between concrete states (including uncertainty) and finite
   states. Check initial-state coverage, predicate preservation, concrete delay
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
5. Compare held-out concrete traces against the abstraction and inspect mismatches.
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

Proposed workflow, not executed: external simulation/measurements → immutable raw
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

The normalized exchange consists of JSONL events and a manifest. Required event
fields: `run_id`, `scenario_id`, `event_id`, `sequence`, `entity_id`, `flow_id`,
`transaction_id`, `event_kind`, `t_observed_s`, `t_sample_s` when available,
`metric`, `value`, `unit`, uncertainty bounds, `config_id`, `raw_reference`.
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

Calibration procedure: choose scenarios and acceptance criteria before fitting;
split by independent run/scenario rather than adjacent rows; fit thresholds on
calibration data; freeze them; run boundary/failure cases and held-out scenarios.
Use independent ground truth for detection/quality instead of classifying model
outputs against themselves. Report sample/exposure counts, false alarms, misses,
unsafe class assignments, latency/age distributions, conformance mismatches and
confidence intervals with their estimation assumptions. Declare acceptable unsafe
error rate/confidence, deadline coverage and test-envelope coverage before the run;
P1 does not invent a scientifically justified universal pass percentage.

Until deployment data are available, P2 may propose an explicitly abstract case
study with declared time units/assumptions for reviewer acceptance. It must not be
described as physically calibrated or empirically validated. Approval of that
claim scope belongs to the independent reviewer/integrator.

## Validation claims and handoff

| ID | Delivered | Still required for stronger claim/acceptance |
|---|---|---|
| V01 | State/transition/composition adequacy methodology and failure taxonomy | P2 integrated interfaces; independent relation/coverage review and any claimed empirical evidence |
| V02 | All finite domains, demo numeric boundaries, equality observations, family calibration methods | Chosen deployment thresholds, STALE/missing-data mapping and consistent boundary semantics |
| V03 | All 43 timing parameters with source values, endpoint/calibration method and bounded applicability of a standard example | Physical Δ or explicitly abstract profile, measured/assumed bounds and composition budget decision |
| V04 | Simulator/export/estimator/conformance protocol with reproducibility requirements | Implemented adapter and executed data comparison before claiming demonstrated integration |
| V05 | Source hashes/locations, symbolic inputs, distinction between policy/illustrative/normative/calibrated values | Independent review of inventory and acceptance of parameter decisions; no unexplained calibrated value claimed |

P2 handoff decisions: resolve equality semantics; complete or explicitly restrict
the mapper; define missing/invalid inputs; resolve SINR/Rfa units; choose freshness
semantics; bind D_cmd; distinguish static labels from measured capacities; align
cross-layer admission/ack timing and freeze a parameter set with instance vector.
The reviewer must decide whether an abstract case-study scope suffices or physical
calibration is required. This report does not mark V01–V05 closed, P1 accepted or
Gate 1 passed, and does not unblock P3/P4.
