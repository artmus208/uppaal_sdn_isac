# Response to Reviewers

Manuscript ID: 18100004273  
Revised title: *A Hierarchical Timed-Automata Model for SDN-Managed Resource Orchestration in 6G ISAC Networks*  
Prepared: 3 October 2026

This response accompanies a substantial revision. The manuscript now separates three configurations: the historical 50-process model H, the finite family F with 50–197 processes, and the current 51-process request-correlated model S. Results are attributed to their exact configuration. The revision reports counterexamples, completed verdicts, unsuccessful searches and replay evidence separately. It does not claim universal service success or physical validation where these have not been established.

The status labels below distinguish completed revisions from unresolved scientific work. The 15-page TeX PDF was built without overfull boxes or undefined references, and all 15 pages were visually inspected. The DOCX was generated from the same TeX revision, checked structurally and rendered through LibreOffice; all 16 rendered pages were inspected after correcting conversion defects. These technical checks do not replace the authors' final scientific review and approval.

## Guide to the Revised Manuscript

| Location | Content |
|---|---|
| Section 1 | Introduction, contribution and network-protocol related work |
| Section 2; Tables 1–2 | Executable composition, process counts and distinct model identities |
| Section 3; Table 3; Figure 1 | Physical abstraction, parameter provenance, validation boundaries and PHY fragment |
| Section 4; Figures 2–3 | MAC scheduling, SDN/RIC policy and interface semantics |
| Section 5; Figure 4; Eq. (3) | Request-correlated result completion, clock ownership and terminal outcomes |
| Section 6; Table 4; Eqs. (4)–(7) | Properties, historical results, current timeouts and open obligations |
| Section 7; Table 5 | Finite-family scalability measurements and comparison with Glonina |
| Section 8; Table 6 | Successful service replay and a separate rejection scenario |
| Sections 9–10 | Simulator workflow, statistical extensions, reproducibility and limits |

Equation numbering above follows the present source: Eq. (1) composition, Eq. (2) abstraction map, Eq. (3) success predicate, Eqs. (4)–(6) structural obligations, Eq. (7) intended bounded-response notation.

## Reviewer 1

The reviewer identified the four-layer architecture and public model artifacts as strengths. The revised manuscript retains this structure and adds explicit configuration and evidence boundaries.

### R1.1. Justify the PHY discretization thresholds through radio or system-level analysis

**Status: partially addressed; physical calibration remains open.**

Section 3 now separates a finite abstraction from a calibrated radio model. Equation (2) identifies the quality dimensions, while Table 3 gives the case-study constants and their units. The text states that these are abstract engineering choices rather than measurements from a radio installation. It also removes an unsupported implication that categorization automatically preserves safety.

The validation discussion identifies threshold-equality checks, finite-domain checks and a strict completion oracle, and proposes comparison against independent external traces. No SINR-to-class calibration, detection-probability validation, concrete-to-abstract preservation proof or coupled simulator dataset has been obtained. The revision therefore makes the assumptions and missing evidence explicit; it does not claim that empirical justification of the thresholds has been completed. Sections 9–10 retain this limitation.

### R1.2. Add concrete service scenarios from PHY states to SLA formulas

**Status: addressed as traced examples; universal service guarantees remain open.**

Section 8 now presents two scenarios. Table 6 follows the current S model from request emission through matching admission, measurement, queue insertion, MAC service, transport and application receipt. The successful execution has 100 transitions and a replay of 101 states. At receipt the request age is 14 abstract units and sample age lies in [4,5), satisfying the strict freshness and relative-deadline conditions explained in Section 5 and Eq. (3).

A separate 63-transition rejection trace belongs to F at N=1. It relates PHY degradation, shared telemetry, MAC/SDN reactions, application rejection and an SLA report. Its request-to-rejection interval is four abstract units. Table 2 and Section 8 identify the different model configurations. Neither trace is treated as a universal model-checking verdict or evidence that every request succeeds.

### R1.3. Make the UPPAAL diagrams readable and enlarge important fragments

**Status: addressed after render review.**

The revised source uses selected vector fragments instead of embedding whole GUI screenshots: Figure 1 shows PHY sensing, Figure 2 the MAC scheduler, Figure 3 SDN/RIC policy and Figure 4 application outcomes. The captions identify the exact template, omitted transitions and the source catalogue. This makes the intended scope of each diagram explicit rather than presenting a simplified fragment as the full model.

All four figures were inspected in the 15-page TeX PDF and the 16-page LibreOffice rendering of the DOCX. The fragments are readable at the manuscript's print size and contain no GUI debris. Selected transition glosses and the complete transition catalogue were checked against the exact XML; omitted transitions remain explicitly identified. A separate native APP export, `app-native-full.eps.gz`, is retained in the source package as a supplementary full view.

### R1.4. Give typical deadline magnitudes or ranges

**Status: addressed for the abstract case study; physical magnitudes remain open.**

Table 3 now gives numerical values: acquisition duration 5, service epoch 5, transport-stage bound 1 measured from the actual transmission attempt, relative service deadline 40, and freshness boundaries 5 and 10. Section 5 explains the start event, reset ownership and boundary behavior. The sample is stale at sample age exactly five; at service age exactly 40, receipt and timeout may both be enabled. The transport clock does not bound dispatch-to-attempt waiting.

All time values remain abstract. Section 3 explains how a calibrated unit would translate them to seconds, without choosing an unsupported conversion. No typical millisecond range for a real network is claimed.

### R1.5. Explain the workflow with ns-3 or OMNeT++

**Status: methodological explanation added; coupling experiment remains open.**

Sections 3 and 9 now describe a concrete proposed workflow: obtain timestamped radio/packet observations, map quality and event information into finite categories and timing ranges, inspect symbolic behaviors, and replay informative scenarios in a conventional simulator. The exchanged information includes units, request/sample identities, timestamps, thresholds and outcomes. The official ns-3 and OMNeT++ manuals are cited for their simulation capabilities.

The manuscript explicitly distinguishes this workflow from an implemented adapter or an empirical validation campaign. Neither has been completed for the reported model.

### R1.6. Discuss priced/probabilistic models and statistical model checking

**Status: addressed as future work.**

Section 9 cites the UPPAAL SMC tutorial and identifies deadline-success probability and accumulated energy/resource cost as useful quantitative targets. It explains that arrival, failure, loss and service-time distributions, together with statistical error/confidence parameters, would have to be justified. Current nondeterministic alternatives are not assigned probabilities retrospectively. The text distinguishes statistical estimates from universal exhaustive verification and reports no SMC experiment.

### R1.7. Improve language, merged words and overly long sentences

**Status: addressed after source and render review.**

The introduction and interface discussion have been rewritten, and the completion terminology is used consistently across Sections 1, 4–6 and 8–10. Admission, command ACK, queue service, transmission and successful receipt have distinct meanings. The abstract no longer contains a formatting claim. All pages of the TeX PDF and the LibreOffice-rendered DOCX were reviewed. Identified interval-notation, caption, bibliography and equation-conversion defects were corrected and rechecked. The authors' final review remains separate from this technical proofreading.

## Reviewer 2

### R2.1. Replace a modeling-only presentation with actual verification evidence and counterexamples

**Status: reporting gap addressed; scientific outcomes are mixed.**

Section 6 and Table 4 now report actual outcomes rather than only proposed properties. Historical H contains a queue-safety counterexample: five arrivals without service reach occupancy five at capacity four; command ACKs do not dequeue work. A separate queue-full reachability query on H completed successfully. Section 7 and Table 5 report 90 attempts on F: 12 satisfied verdicts, six violated verdicts and 72 timeouts.

For current S, Section 8 reports a successful execution and engine replay. Section 6 also reports all eleven exhaustive attempts: each reached its 600-second limit with a null verdict. The 6607.4778455-second aggregate exceeded the declared 6600-second budget after a supplemental guard failure; this deviation is disclosed and is not counted as extra evidence. Table 2 prevents transferring historical results to S.

### R2.2. Check structural correctness and at least one bounded-response property on the actual XML

**Status: partially addressed; the requested current-model guarantees remain open.**

The structural formulas originally discussed as Eqs. (10)–(12) are now explicitly stated as Eqs. (4)–(6) in Section 6. The historical queue-safety property is violated. A historical MAC response argument gives an ACK-or-timeout bound of three abstract units under time-divergent executions, but it is not a successful full-model universal application query. The unconditional end-of-wait formula `mac_obs_ack_active --> !mac_obs_ack_active` has a saved violated verdict. It concerns eventual termination of active ACK waiting by ACK or timeout; it is not a successful-ACK-delivery formula.

No completed exhaustive verdict for deadlock freedom, queue/recovery bounds or universal bounded successful response is reported for S. Its eleven-query campaign timed out and also has stated coverage gaps. The successful replay is only existential execution evidence. A later six-query protocol was prepared, but its slots were not executed because the selected runner checkpoint cannot represent the current runner identity truthfully. Thus the requested universal current-model result has not been produced, and the revised abstract, Sections 6 and 9, and conclusion state that limitation directly.

### R2.3. Replace the dense figures with cropped or enlarged fragments

**Status: addressed after render review.**

Figures 1–4 now show selected PHY, MAC, SDN/RIC and APP fragments with explicit omission notes. Their print readability and placement were checked in both rendered formats, and the selected transition descriptions were checked against the XML. The response to R1.3 describes these completed checks and the separate native APP export.

### R2.4. Remove the abstract's “Springer LNCS-formatted” wording and use the correct venue format

**Status: wording and format corrected; render checks completed.**

The abstract's self-description of formatting has been removed. The current [MoNeTec-2026 author instructions](https://monetec.ru/authors) specify Springer CCIS for accepted and presented English papers and direct authors to Springer proceedings templates. We therefore retain the Springer proceedings format for this camera-ready revision. The [Springer template instructions](https://link.springer.com/series/558/information-for-authors-and-editors) explicitly cover CCIS. The contemporary conference instructions, rather than the old wording in the abstract, determine this choice.

The TeX PDF is 15 pages and has no overfull-box or undefined-reference warnings; all pages were visually reviewed. The DOCX from the same source contains six editable tables, four figures, 42 Office Math nodes including seven displayed equations, and nine reference entries. All 16 pages of its LibreOffice rendering were inspected. Microsoft Word may paginate differently; no native Word UI inspection is claimed.

## Reviewer 3

The introductory concerns about model validity, instance counts, verification resources and missing protocol references are addressed individually below. The revised manuscript consistently separates implementation validation, physical adequacy and temporal verification.

### R3.1. Add existing timed-automata models of network protocols to the introduction

**Status: addressed in the text.**

Section 1 now discusses Fehnker et al.'s UPPAAL analysis of AODV as a concrete wireless-network example, in addition to the foundational timed-automata and UPPAAL references. The comparison concerns finite-topology exploration and diagnostic counterexamples; it does not claim that AODV results prove this ISAC model correct. The citation identifies the TACAS 2012 publication, not the later arXiv upload date.

### R3.2. Explain validation as fidelity to modeled behavior, distinct from checking requirements

**Status: substantially clarified; physical adequacy remains open.**

Section 3 expressly distinguishes validation from verification. It describes parameter/domain inventories, threshold equality cases, interface mappings and regression checks against a separately expressed strict completion oracle. The S checks include 243 quality tuples, identity correlation, grants without receipt, cancellation, freshness boundaries and clock-reset ownership. These assess internal implementation consistency rather than measured radio fidelity.

The same section proposes trace-based comparison with an external model, including boundary and missing-report cases. No physical calibration dataset, completed simulator coupling or general abstraction-soundness proof is claimed. The remaining adequacy obligation is stated in Sections 9–10. This response therefore does not characterize software tests as empirical validation of an operational 6G network.

### R3.3. Present actual verification attempts, computational resources and state-explosion limits

**Status: addressed as an empirical report; current structural/universal results remain inconclusive.**

Sections 6–7 and Tables 4–5 give the results and resource limits. F was tested at N=1,2,3,4, with 50,99,148,197 processes and three attempts per model/query cell. The host used an AMD Ryzen 5 1400, eight logical processors, approximately 15.93 GiB physical RAM and Windows 11; UPPAAL was version 5.0.0, revision 714BA9DB36F49691. Search limits were 60 seconds with a sampled 2048 MiB memory stop.

Joint-backlog reachability completed at N=1,2,3 with median observed times 2.792,15.335,43.503 seconds and timed out at N=4. All 30 service-reachability attempts timed out. The largest sampled target-process memory observation was 231.23 MiB; it is not the memory required to finish an incomplete query. Timeouts are censored observations, not false formulas or completed observations at the limit. Section 6 separately reports the eleven 600-second S attempts and their budget deviation. These measurements make the practical limits visible without deriving an asymptotic scaling law.

### R3.4. Explain multiple instances and compare scalable verification with Glonina's work

**Status: instance description and comparison added; arbitrary-N theorem remains open.**

Section 2 and Table 1 now enumerate S: 20 core processes, 22 observers, eight environment/adapter processes and one result job, totaling 51. It models one UAV, one request and one result token. Table 2 distinguishes F, which has 49N+1 processes and a shared service arbiter, from S, which was tested only at N=1. The manuscript does not describe this finite case study as a network with an arbitrary number of base stations or devices.

Section 7 now compares the methodology with Glonina's dissertation and the published component-correctness work. That route establishes correctness and deterministic behavior under component/composition conditions; parameter reductions require explicit clock, comparison and reset restrictions. The dissertation also demonstrates that a locally valid reduction can fail after composition. Our loss choices, optional service, queues and shared arbiter have not been proved to satisfy the required premises. The finite N≤4 experiment supplies no cutoff or unbounded-instance verification theorem. Applying such a theorem remains research work rather than a completed revision claim.

### R3.5. Place figures close to their corresponding sections

**Status: addressed after render review.**

Figure 1 is placed in Section 3 with the PHY explanation; Figures 2–3 in Section 4 with MAC and SDN/RIC; Figure 4 in Section 5 with APP completion. Section-level float barriers keep these groups together. Page-by-page inspection confirmed the figures on PDF pages 5, 6, 7 and 9, respectively, within the corresponding sections. Their placement was also checked in the DOCX rendering.

### R3.6. Remove GUI debris, including a window corner and mouse cursor

**Status: addressed after render review.**

The manuscript screenshots were replaced by vector automaton fragments and associated source catalogues. Inspection of the final PDF and DOCX rendering confirmed the absence of the window corner, mouse cursor and other GUI debris. The supplementary native APP export is retained separately and does not replace the readable selected fragment in the manuscript.

### R3.7. Explain one automaton and the abstraction that limits its states and transitions

**Status: partially addressed in the text; no state-space preservation theorem claimed.**

Section 4 and Figure 2 explain the MAC control cycle: collecting PHY information, finite policy selection, applying a schedule, waiting for a command ACK, fallback and failure reporting. The queue is described separately, with K+1 retained as an observable overflow state. Section 5 and Figure 4 give a more detailed application example: request creation/emission, admission, result matching and distinct terminal states; Eq. (3) defines the strict success condition. Stored sample quality and separately owned clocks prevent later telemetry or a control ACK from being mistaken for request completion.

Sections 3–5 explain why categorical quality and bounded token/identity domains give a finite control abstraction. They do not assert that input combinations equal reachable states, that selected diagram edges cover every behavior, or that this abstraction preserves every concrete network property. A complete transition-by-transition explanation and soundness proof remain beyond the evidence reported here; figure captions explicitly identify omitted branches.

## Remaining Scientific Items and Author Review

The revised paper reports an executable case study and measured verification limits. Physical calibration, complete current-model structural checking, universal bounded successful response and verification for arbitrary instance counts remain open. These are retained as limitations rather than reported as resolved reviewer requests. The PDF and DOCX render checks have been completed; scientific approval and submission remain the authors' responsibility. The manuscript now includes an AI-assistance disclosure in its credits.

The accompanying technical checks are agent checks against archived evidence. They are not external peer review, scientific gate acceptance or author approval.
