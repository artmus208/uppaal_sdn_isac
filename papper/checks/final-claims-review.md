# Agent scientific claims review of the integration manuscript

This is an **agent review**, not external peer review, an independent human approval, or scientific gate acceptance. Reviewed on 2026-10-03. No manuscript edit, new verifier execution or replay was performed.

Reviewed file: `levels_tex/samplepaper.tex`, SHA256 `93838ad8013b7dc7f06ae4e31f94e82a65f7817334bc6f9e9df4c4ccbd26e335`. Line references address that snapshot. Basis: `checks/evidence-review.md`, preserved machine results, exact S XML, the existing rejection-scenario package, and the other agents' literature/protocol source reviews. Reviewer response is not included in this pass.

## Findings

### F1 — P2: Anchor the one-unit transport bound at the transmission attempt

**Manuscript:** line94, `Delivery or loss after dispatch`; line139, `After dispatch, transport may deliver ... or lose the token within one abstract time unit`.

This wording puts the clock origin at queue dispatch. In S, dispatch sets `c82_dispatched=true` separately. `C82_ResultJob` remains in `Queued`; that location has no invariant/urgent/committed annotation. Only edge6, `Queued -> Transmitting`, sets `c82_attempted=true, c82_tx_age=0`. The one-unit invariant is on `Transmitting`. The model therefore does not supply a one-unit dispatch-to-delivery bound from this clock. It supplies the transport-stage bound measured from the actual attempt, subject to termination/cancellation behavior and the stated progress limitations.

**Evidence:** `evidence/instantiation/uav-service-completion-candidate/model.xml`: dispatch assignment at line906; Queued at7979; Transmitting invariant at7983; attempt/reset at8027; delivery/loss guards at8032/8038. The replay itself distinguishes dispatch state96 from attempt state99.

**Minimal fix:** table: `Delivery/loss stage after transmission attempt`. Prose: `After dispatch, the job starts a transmission attempt and resets its transport clock. Delivery or loss then has a one-unit transport-stage bound; the clock does not bound dispatch-to-attempt waiting.` Preserve cancellation and the absence of a universal completion guarantee.

### F2 — P2: Label the two APP placeholders in the composition description

**Manuscript:** line51 assigns the four APP processes the roles `Request, SLA, criticality, aggregate service impact`; line59 calls them actual instances without explaining which behavior is absent.

The count four is correct, but `u0_app_A_CRIT` and `u0_app_A_SVC_AGG` each have one Idle location and **zero transitions**. Readers can currently infer implemented criticality/aggregate processes from the table. Criticality values used by request/SLA logic do not make these two templates implemented. The accepted P1/P2 scope explicitly excludes claims of their missing behavior.

**Evidence:** S XML lines4343-4356; `evidence/governance/20260910-p1-p2-review/final-20260923/README.md`, lines46 and80; `checks/evidence-review.md`, 51-process composition section.

**Minimal fix:** retain four in the count, but say `Request and SLA; two retained criticality/aggregate placeholders without transitions` either in the row or immediately after it.

### F3 — P2: Identify the violated leads-to predicate as end-of-wait, not ACK delivery

**Manuscript:** line188, `An unconditional ACK leads-to query was violated`.

The saved violated formula is `mac_obs_ack_active --> !mac_obs_ack_active`. It concerns eventual completion of the observed ACK wait; either a matching ACK **or** ScheduleFailure/timeout can end that wait. Calling it an ACK leads-to query without the actual formula risks a materially different reading: that an unconditional successful-ACK-delivery property was tested. This distinction is central to why the adjacent three-unit argument requires time divergence.

**Evidence:** `p3-20260923-003-14-ack-unconditional-completion`, status success, verdict violated, query SHA256 `3f406107b55e4e196c2416c16e0573e3b362e2ff0396ab3ac696b183e252d249`, historical H model. Exact formula and trace reference are in `evidence/verification/p3-20260926-core-acceptance/accepted-runs.json`.

**Minimal fix:** `The unconditional end-of-wait query mac_obs_ack_active --> !mac_obs_ack_active was violated; ending the wait includes ACK or timeout.` No new query claim is needed.

### F4 — P3: Avoid implying a measured reachable-state increase

**Manuscript:** line251, `The added result job ... enlarges the state space`.

S adds state and a process, but also changes guards, event synchronization and admissible behavior. No explored-state count or state-space inclusion argument establishes a larger **reachable** state space relative to F/H. The present phrase may be read as that stronger result. The paragraph only needs the defensible implementation fact.

**Minimal fix:** `The result job adds state and verification obligations that historical results do not discharge.` This is a precision improvement, not a request for a new experiment.

## Checked and supported

- H/F/S identities and separation are correct. Process counts51 and50/99/148/197 are correct; no transfer of historical verdicts to S is claimed.
- H queue counterexample q5/K4, five arrivals without service, four control ACKs without dequeue,19.439s and182.918MiB match the retained record. Queue-full17.223s is correct. Time-divergent three-unit MAC argument is properly separated from a direct full-model verdict.
- P4 totals90,18 completed (12 satisfied/six violated),72 timeouts, all30 service timeouts, per-N rows, median/range values,231.23MiB and0.618s maximum sampling gap match saved results. Censoring and the limits of scalability conclusions are stated.
- S's eleven timeout/null outcomes,600s thresholds and6607.4778455s aggregate deviation are preserved accurately. The manuscript does not mistake merged artifacts for established properties.
- Successful S trace milestones4/62/84/85/96/99/100,100 transitions/101 states, global15, request14 and sample[4,5) are correct. The phrase `Acquisition occurred in (10,11]` at line242 would be more precise as `Measurement completed in (10,11]`; this is the sample event, not the full five-unit acquisition interval.
- The rejection scenario's63 transitions, model F/N1, four-unit request-to-rejection and zero-unit violation-to-report agree with `evidence/scenarios/r07-uav-n1-20261002/scenario-for-paper.md` and `SEMANTICS.md`.
- The qualitative Glonina comparison is consistent with the dissertation/verified literature review. Parameter bounds are correctly distinguished from process-count cutoffs. The bibliography key ending2021 deliberately retains a2020 dissertation year with a2021 defense note; this is not a date error.
- The six-query protocol is correctly identified as unexecuted. For maximum clarity, line192 could explicitly say Q1-Q5 use the prospective Hnom restriction and Q6 uses original S, matching `checks/protocol-review.md`.
- The paper properly limits243 quality-tuple regressions to software/static consistency, preserves abstract time, and does not claim physical calibration, an implemented simulator coupling, or universal S success.

The main numerical evidence is consistent. F1-F3 need small wording corrections; F4 is a conservative precision improvement. This review adds no scientific acceptance decision and does not close the outstanding property obligations.

## Follow-up: corrected manuscript, figure glosses and reviewer response

This continuation is also an agent source/evidence check, not external review or native model checking. No GUI or verifier was used. The only file changed by this reviewer is this review record.

Snapshots inspected:

- `levels_tex/samplepaper.tex`: SHA256 `7a2f5edf8d54d7aee48dc22a91fee46d02bb78880493c55c352d83face57a971`.
- `sources/make_figures.py`: SHA256 `e1de22dce8bbd357f369eda7cc47c186bd67c8199bec678490a9f317c78d1179`.
- `reviewer-response.md`: SHA256 `1530226e3bc72f31bc133937d4c2d5bfed24a14c9418744c0c194c4181da2c6b`.
- `build/samplepaper.aux`: SHA256 `7dfe0774b4c3781047ef75eea0657f31b37ba43d51a2731eb729ba7791b873d8`.
- Figure source model reread: exact SHA256 `b8ab50e112b71491f8242789cc7906497baf8440c473d7a5a4d5214840187e02`.

### Resolution of the first review

F1 resolved in manuscript: the one-unit stage is now anchored to the actual transmission attempt, and dispatch-to-attempt waiting is explicitly distinguished. F2 resolved: the composition table identifies placeholders and the text expressly says criticality/aggregate templates have zero transitions. F3 resolved in manuscript: the violated leads-to predicate is described as ending active ACK waiting by ACK or timeout. F4 resolved: the text now says the result job adds state and does not infer a numerical increase in reachable states. These resolutions do not imply that the corresponding old wording in the reviewer response has also been changed.

### Figure index/catalogue checks

The script's `specs` object was read by Python AST parsing without executing the renderer. All 32 selected zero-based indices exist in their exact templates: PHY6/28, MAC9/17, SDN6/13 and APP11/27 selected/total transitions. For every figure, selected plus omitted indices form the complete transition index set with no duplicates or gaps. Every source/target and full transition-label record in `figures/transition-catalogue.json` matches the exact XML. Thus the remaining issues concern explanatory glosses, not index extraction or fabricated transitions.

| ID | Priority | Current gloss | Exact XML semantics and required correction |
|---|---|---|---|
| G1 | P2 | PHY T27: `inactive job retires at 5` | Guard is only `!c82_active`; it has no age-equality guard and can release the measurement location before5. Use `inactive job retires`. |
| G2 | P2 | APP T14: `invalid receipt; age < 40` | Guard checks active status and invalid identity/causal or quality predicate. It has no `<40` guard; the Accepted invariant permits service age40. This edge also should not stand for the separately omitted stale-receipt branch. Use `invalid identity / quality`. |
| G3 | P2 | PHY T3: `acceptable sensing class` | Guard is `env_scenario==SCENARIO_NORMAL && c_sense<=D_sense`. The assignment computes `highest_priority_SQ()` and does not itself prove stored sample acceptability. Use `normal-scenario report`; actual job-result quality is checked at later edges. |
| G4 | P3 | MAC T1: `fresh PHY report` | The synchronization is `phy_kpi_report?`; there is no KPI_FRESH guard on this edge. The inherited source comment says fresh, but this is not an independently established freshness predicate. Use `PHY report received`. |
| G5 | P3 | APP T1: `construct request` | `build_uav_service_request()` is called on T0. T1 tests `gAdmissionRequest()` and sets ADM_PENDING/reset, entering RequestReady. Use `request admissible / ready`. |

The remaining selected glosses agree with the corresponding events/guards at their stated explanatory level. Valid-receipt APP T12/T13 correctly distinguish service age<40 versus=40; both retain the full matching/freshness predicate in the catalogue. PHY T25/T26 correctly use acquisition age5; cancellation/inactive release must remain distinct as in G1. SDN ordered predicates correctly negate earlier choices. MAC command ACK/timeout is kept separate from result delivery.

### Reviewer-response consistency

- **R2.2 still needs the F3 correction:** its sentence `An unconditional ACK leads-to property has a saved negative result` retains the ambiguous old wording. Mirror the corrected manuscript description: active ACK waiting eventually terminates by ACK or timeout. The actual formula is `mac_obs_ack_active --> !mac_obs_ack_active`.
- **R1.4 small terminology correction:** `A request is stale at sample age exactly five` should be `The sample is stale at sample age exactly five`. Request age and sample age are different clocks throughout the model.
- Numeric claims in R1.2/R1.4/R2.1/R2.2/R3.2/R3.3/R3.4 match the manuscript and preserved evidence:100/101-state successful replay,63-transition rejection, request14/sample[4,5), F process counts50/99/148/197,90 attempts with12 satisfied/six violated/72 timeouts,30 service timeouts, medians2.792/15.335/43.503,231.23MiB,243 quality tuples, and11 S timeouts with6607.4778455s aggregate.
- R1.1/R1.5/R1.6/R3.1/R3.2/R3.4/R3.7 keep calibration, external coupling, SMC, cutoff and soundness boundaries explicit. No new unsupported scientific success claim was found in those responses. R3.7 is explicitly partial, not an assertion that all omitted automaton behavior has been explained in prose.
- Presentation items are still honestly marked pending in the inspected response. This semantic/index check does not certify their final PDF/DOCX print layout. Once the integration owner completes actual artifact inspection, those labels should be updated against that evidence, without calling agent checks external peer review or author approval.

### Reference/numbering cross-check

All TeX `ref`/`eqref` targets occur in `build/samplepaper.aux`; all9 cited bibliography keys have `bibcite` entries. The response's guide and subsequent Section/Table/Figure/Equation references agree with the current source and AUX numbering:

| Element | Actual number | AUX page |
|---|---:|---:|
| Composition / configurations | Section2; Tables1/2 | 2;3/3 |
| Validation / parameters / PHY | Section3; Table3; Figure1 | 3;4;5 |
| Control / MAC / SDN | Section4; Figures2/3 | 5;6/7 |
| Completion / success / APP | Section5; Eq3; Figure4 | 7;8;9 |
| Verification / structural obligations / evidence | Section6; Eqs4/5/6; Table4 | 10;10/10/10;11 |
| Scalability | Section7; Table5 | 11;12 |
| Scenarios | Section8; Table6 | 12;13 |
| Discussion / conclusion | Sections9/10 | 13/14 |

Eq1 is the composition, Eq2 the unlabelled abstraction map and Eq7 the unlabelled bounded-response notation; the latter two were checked from their position in the equation sequence, since they have no AUX label. The AUX reports15 pages. This verifies numbering, not visual quality or absence of layout defects.

Remaining source actions at this snapshot: G1-G3 semantic gloss corrections, G4-G5 precision corrections, and the two response sentences above. No change to scientific models, queries or results is called for.

## Closure of prior findings

Targeted recheck on 2026-10-03 confirmed **G1-G5 resolved** in `sources/make_figures.py` and in the text extracted from regenerated PHY/MAC/APP figure PDFs: `inactive job retires`, `invalid identity / quality`, `normal-scenario report`, `PHY report received`, and `request admissible / ready`. APP T0 now explicitly identifies request construction. Both reviewer-response findings are also resolved: R1.4 says the **sample** is stale and names the transport clock's actual origin; R2.2 gives the exact end-of-wait formula and distinguishes ACK/timeout termination from successful ACK delivery.

Closure snapshots: figure script SHA256 `02678e3f122dbf7ed954609f8337c4126ff033271279944bff592fa17e577226`; reviewer response `985aa5aa2ad258269e1854047c48fab474746d9d065b1cd2a71e46e33ecbfe29`; transition catalogue `2dc4e004e57af4042bef83db3425966ef5d6c671cc3a4c8d250b84adfb699d7d`; manuscript `43d6bcbd782b1ffe46fd9f1f76e79032c075462d8ad409e04a2e119915cf5c3e`.

Together with the earlier F1-F4 resolutions, **all concrete findings raised in this agent review are closed**. This targeted closure did not repeat the scientific audit, model runs or presentation checks. It is not external peer review, scientific acceptance or a new universal-property result; the manuscript's stated scientific limitations remain unchanged.
