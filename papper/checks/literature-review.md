# Literature and venue check for integration #92

Checked 3 October 2026 (Europe/Moscow). This is an agent technical check, not external scientific peer review. Scope: bibliography, related-work comparison, current venue/format instructions. The manuscript and root bibliography were not edited by this reviewer.

## Deliverable and selection

`../sources/verified-literature.bib` contains nine entries, including the two official simulator manuals requested by the integration editor. Cite only entries used by the final text. The compact selection addresses timed-automata foundations, UPPAAL semantics, actual network-protocol model checking, SMC, ISAC background and Glonina's reduction assumptions. Old application papers need not be retained simply because they were in the original bibliography.

The original audit was read from `C:/Users/musta/Desktop/pySources/mcp_uppaal/chat_histories/03.10.2026-audit-prism.md`, bibliography and Glonina sections. Its findings were used as leads; the primary sources and local dissertation passages below were checked separately.

## Verified entries and metadata traps

| Key | Verified publication and primary evidence | Editorial use |
|---|---|---|
| `alur_theory_1994` | Alur and Dill, *Theoretical Computer Science* 126(2), 183–235 (1994), DOI 10.1016/0304-3975(94)90010-8. [Author-hosted published paper](https://www.cis.upenn.edu/~alur/TCS94.pdf) | Foundational timed-automata semantics, not evidence about this network instance. |
| `uppaal_tutorial_2004` | Behrmann, David and Larsen, LNCS 3185, 200–236 (2004), DOI 10.1007/978-3-540-30080-9_7. [Springer chapter](https://link.springer.com/chapter/10.1007/978-3-540-30080-9_7) | Reference for UPPAAL modeling patterns. Publisher pagination prevails over the Aalborg record's 200–237. |
| `aodv_uppaal_2012` | Fehnker et al., *Automated Analysis of AODV Using UPPAAL*, TACAS 2012, LNCS 7214, 173–187, DOI 10.1007/978-3-642-28756-5_13. [Author deposit and publication reference](https://arxiv.org/abs/1512.07352) | Concrete wireless-routing model checking and diagnosis, with experiments for topologies up to five nodes. |
| `uppaal_smc_2015` | David, Larsen, Legay, Mikučionis and Poulsen, *International Journal on Software Tools for Technology Transfer* 17(4), 397–415 (2015), DOI 10.1007/s10009-014-0361-y. [Authors' institutional record](https://vbn.aau.dk/en/publications/uppaal-smc-tutorial/), [tool-hosted tutorial](https://uppaal.org/texts/uppaal-smc-tutorial.pdf) | Stochastic semantics and statistical queries; the re-typeset PDF's 2018 date is not the journal year. |
| `isac_survey_2022` | Liu, Cui, Masouros, Xu, Han, Eldar and Buzzi, *IEEE JSAC* 40(6), 1728–1767 (2022), DOI 10.1109/JSAC.2022.3156632. [IEEE](https://ieeexplore.ieee.org/document/9737357/), [author copy](https://www.weizmann.ac.il/math/yonina/sites/math.yonina/files/Integrated_Sensing_and_Communications_Toward_Dual-Functional_Wireless_Networks_for_6G_and_Beyond.pdf) | ISAC resource-sharing, sensing/communication tradeoffs and cross-layer motivation. |
| `glonina_thesis_2021` | A. B. Glonina, *Analysis of Modular Computer System Configurations for Checking Real-Time Constraints*, Candidate of Sciences dissertation, MSU. [MSU defense record](https://dissovet.msu.ru/dissertation/1719), [ISTINA record](https://istina.msu.ru/dissertations/364890262/) | The preserved `pdfs/dissertation.pdf` title page says Moscow 2020. MSU records successful defense on 23 September 2021. BibTeX uses 2020 with an explicit defense-date note, keeping the editor-requested key. Direct ISTINA access failed in this pass; the official MSU record links to it. |
| `glonina_correctness_2018` | Glonina and Balashov, *Automatic Control and Computer Sciences* 52(7), 817–827 (2018), DOI 10.3103/S0146411618070271. [Publisher](https://link.springer.com/article/10.3103/S0146411618070271) | English translation by the authors; issue year 2018, online publication 4 March 2019. Correctness and determinism under component contracts. |
| `ns3_manual` | [Official ns-3 Manual](https://www.nsnam.org/docs/manual/html/index.html), accessed 3 October 2026 | Discrete-event simulator, tracing and data collection; no adapter implementation is implied. |
| `omnetpp_manual` | [Official OMNeT++ Simulation Manual](https://doc.omnetpp.org/omnetpp/manual/), version 6.2.0, accessed 3 October 2026 | Simulation inputs, event logs and result recording; not exhaustive verification. |

Do not insert a purported 2013 AODV publication under `aodv_analysis_2013`: the two supplied identifiers do not identify one. [arXiv:1512.07312](https://arxiv.org/abs/1512.07312) is *Modelling and Analysis of AODV in UPPAAL*, explicitly identified as WRiPE 2011. [arXiv:1512.07352](https://arxiv.org/abs/1512.07352) is the TACAS 2012 paper. Both arXiv uploads occurred in December 2015. The 2012 paper suffices for a compact discussion.

## Text suitable for introduction/discussion

The following is an original synthesis, with claim boundaries chosen for this submission rather than a quotation from a source:

> ISAC shares communication and sensing resources, creating tradeoffs that extend beyond waveform design to network coordination [isac_survey_2022]. Timed automata provide a language for explicit clock constraints [alur_theory_1994], while UPPAAL supplies modeling patterns for synchronized networks of automata [uppaal_tutorial_2004]. Network-protocol analysis is an established application: Fehnker et al. used UPPAAL to diagnose undesirable AODV behavior across bounded network topologies [aodv_uppaal_2012]. Our contribution applies this approach to interactions among PHY, MAC, SDN/RIC and service control, with every reported result tied to a particular configuration. It does not establish correctness of an unbounded network family.

> Statistical model checking offers a complementary route to probabilistic performance questions [uppaal_smc_2015]. Applying it here would require justified stochastic choices for arrivals, failures and delays, explicit cost rates or updates if energy or resource cost is measured, and reported statistical error parameters. Sampling a stochastic extension would answer different questions from universal safety or bounded-response verification of the nondeterministic model. No SMC result is claimed in the present work.

The stochastic/cost paragraph is an application inference from the tutorial, not a claim that its authors analyzed this ISAC model.

For V04, cite the official manuals only for their documented simulation capabilities. A defensible proposed workflow is: collect timestamped simulator events and metrics, map them into finite categories and timing intervals, analyze the resulting TA configuration, and feed counterexamples back into simulation scenarios. The mapping must state units and approximation direction; this is a proposed workflow until actual extraction/adapter code and validation exist.

## Substantive Glonina comparison (R04)

The dissertation was read directly with `pypdf`; cited page numbers below are its printed page numbers (matching PDF indices plus one). These are not inferred from the previous audit.

| Aspect | Glonina source | Consequence for this submission |
|---|---|---|
| Problem and guarantee | Published paper: schedulability of modular real-time computer systems. Component correctness conditions imply whole-model correctness and deterministic observable behavior. | The present nondeterministic environment permits alternative arrivals, channel conditions and recovery paths. A single successful run cannot stand in for universal service completion. |
| Reduction with one ordinary clock | Dissertation p.148, Proposition 3: one non-stopping clock, `k` temporal parameters, comparisons only to those parameters and possibly zero; non-reachability for nonnegative integer parameter values up to `k` transfers to all such values. | This is a parameter-domain theorem under a clock syntax, not a cutoff theorem on process or UAV count. |
| Stopwatch reduction | p.157, Proposition 4: at most four temporal parameters and two stoppable clocks; all stopwatches compare to one shared parameter, not compared with the ordinary clock; clocks reset together; further class-L1 guard/invariant restrictions, bounded clock values and parameter-free clock-activity conditions apply. The bounded valuation set uses 22. | Neither the finite instance vector nor discrete category counts establish these assumptions. Do not claim that checking 22 values or a few UAV counts proves this model correct. |
| Composition is a separate obligation | pp.160–161 give a two-automaton counterexample: individual satisfaction of the local reduction premises need not persist under composition when clocks reset asynchronously. | Cross-layer reset and synchronization contracts must be checked in the composed model. Local template checks alone cannot establish a transfer theorem. |
| Restricted transfer cases | pp.161–162 discuss periodic model/observer pairs with a shared period and synchronized resets. pp.162–164 treat a single temporal parameter under uniform scaling. | A reduction must specify which case applies, the preserved property and a mapping to the target query. No such transfer is established by the scalability experiment alone. |

Suggested discussion text:

> Glonina and Balashov obtain efficient schedulability analysis by proving component correctness and determinism for their modular-system model [glonina_correctness_2018]. Glonina's dissertation further reduces parameter valuations under explicit restrictions on clocks, guards and resets, and shows why local reductions need not survive composition [glonina_thesis_2021, Appendix B]. Our finite UAV family is an empirical scalability study, not an instantiation of those reduction theorems. A transfer would require a property-specific argument for the composed model; no cutoff for arbitrary UAV counts is claimed.

This wording is an applicability comparison, not a claim that the thesis reduction has been implemented or independently reproved. The single English journal citation and thesis are sufficient; adding multiple duplicate Russian/English versions would pad the bibliography.

## Existing 2025/2026 entries

The compact revised selection does not need these entries. If any are retained, apply the following findings:

| Existing key | Finding and source |
|---|---|
| `aman_ai-driven_2026` | Confirmed by publisher: *Scientific Reports* **16**, article **12613** (2026), DOI **10.1038/s41598-026-42247-y**. [Publisher](https://www.nature.com/articles/s41598-026-42247-y). This supports resource-allocation background, not model-checking guarantees. |
| `liu_cooperative_2025` | Final issue metadata is **Engineering 56 (2026), 130–148**, DOI **10.1016/j.eng.2025.08.033**. [Publisher-hosted PDF](https://www.engineering.org.cn/engi/EN/PDF/10.1016/j.eng.2025.08.033). The DOI's 2025 does not determine the issue year. |
| `qaisar_role_2026` | Author deposit confirms TNSE 2026 and adds **10.1109/TNSE.2026.3666665**. [Author deposit](https://arxiv.org/abs/2510.04413). Final volume and pagination not independently established in this pass; omit unknown fields. |
| `mustafin_selective_2026` | [Official conference program](https://smartindustrycon.ru/programme2026-eng.html) confirms title and authors. The previous audit reported ITMO support for DOI/pages, but this pass did not recover that record from the supplied ITMO page. Do not describe full metadata as newly publisher-verified. No need to retain for the core TA claim. |
| `bogatyrev_combinatorial-probabilistic_2026` | DOI/pages remain unconfirmed by an accessible primary publisher source in this bounded pass. Do not rely on this incomplete entry for a central claim. |
| `hossain_ai-assisted_2023` | Previous audit flagged journal-year correction to 2024. Not independently rechecked here because the compact selection replaces this peripheral background. Do not restore the 2023 journal year without checking. |
| Other original background entries | They were not all re-audited. Their removal is a relevance decision, not an assertion that those works are nonexistent or invalid. |

## Venue, Word template and disclosure

[MoNeTec authors page](https://monetec.ru/authors), checked now, specifies Springer CCIS for accepted, presented English papers; camera-ready due **5 October 2026**; **12–15 pages**, with a few additional pages allowed; and the open-publication clearance scan for authors from the Russian Federation through uConfy. It links to Springer formatting guidance. It does not require both TeX and Word: that dual-format requirement comes from the user's task.

The [official Springer author/template page](https://link.springer.com/series/558/information-for-authors-and-editors) explicitly applies to CCIS and supplies **Microsoft Word Proceedings Template (ZIP)** and **LaTeX2e Proceedings Template (ZIP)**. Use that live page as the authoritative Word download entry point; the web tool could not fetch the Word ZIP itself, so no unverified direct ZIP URL is supplied.

[Current Springer Instructions for Authors (PDF)](https://cms-resources.apps.public.k8s.springernature.io/springer-cms/rest/v1/content/27852130/data/Instructions%20for%20Authors%20PDF) specify editable source plus corresponding PDF; Word submission must be `.docx`, not `.docm`; equations and tables must remain editable. Diagrams should use vector graphics where possible, with lettering at least 6 pt; bitmap line art requires at least 800 dpi. References should use Latin characters; translated Russian titles should be marked as Russian. The instructions also require text alternatives for non-text content, normally coordinated with chairs/typesetters. These are source-format requirements, not confirmation of the current DOCX/PDF's compliance.

Springer explicitly requires AI transparency and human accountability. [Book publishing policies](https://www.springernature.com/gp/policies/book-publishing-policies) (brief paraphrase only).

The publisher's [AI guidance](https://group.springernature.com/gp/group/ai/ai-guidance-for-researchers-editors-reviewers) says generative-AI use should be declared in the introduction or acknowledgements, distinguishes limited copy editing, and identifies tool versions, dates, prompts and contribution scope as disclosure information. This task involves substantive synthesis and manuscript assistance, so a copy-editing-only statement would be inaccurate. Keep a factual AI-use note and a pointer to the preserved prompt/evidence. Do not state that the human authors already reviewed and approved all AI-assisted material while they are absent. Their scientific accountability and final review cannot be replaced by an agent check.

Suggested factual disclosure draft, pending author review:

> OpenAI Codex was used on 3 October 2026 to assist with manuscript editing, literature checks, document preparation and consistency checks against the archived computational evidence. The task instructions and supporting check records are retained with the submission materials. AI assistance is not treated as independent scientific peer review.

Add the exact model/version only if it is recorded by the running environment; do not invent a model identifier. Before actual submission the authors must review the paper and supply any final accountability statement in their own capacity.

## Limits

This pass did not reproduce the full prior audit or every DOI lookup. It did not verify all theorem proofs, obtain a new thesis PDF from ISTINA, run UPPAAL, certify publication clearance, submit the manuscript, or confer scientific gate acceptance. The bibliography has nine unique entries and balanced braces; integration must still check which keys are cited and run the actual document build.
