# I02: quantitative extensions with explicit semantics

Issue: [#95](https://github.com/artmus208/uppaal_sdn_isac/issues/95). Owner: `vadimnbkg`.
Base: `read@f0fcd770e3e6b93f99868b9116e4f0929f60d0fa`.
Checked: 4 October 2026, Europe/Moscow. Status: proposed for independent review.

This P6 supplement supplies the method distinctions missing from the short future-work
paragraph in the published submission source. It reuses the existing SMC reference
and adds two references; it does not repeat the earlier literature audit. I02 asks
for a perspective, not an implementation or a new experiment.

## Method and claim map

The rows describe different questions. Cost annotations, probabilistic semantics,
and the analysis algorithm are separate choices; they can be combined when the
chosen formalism supports the combination. Here, “PTA” means **probabilistic**
timed automaton, never priced or parametric timed automaton.

| Claim ID | Method and supported statement | Assumptions and limits | Primary support |
|---|---|---|---|
| I02-SYM | Ordinary symbolic checking: `A[] p` covers every reachable state; `E<> p` asks whether a state can be reached. | The supplied nondeterministic model defines the choices. A witness is not a frequency estimate. A failed or unfinished run establishes no verdict. | [UPPAAL symbolic semantics](https://docs.uppaal.org/language-reference/query-semantics/symb_queries/), “Invariantly”, “Possibly”; project evidence rules. |
| I02-COST | Linearly priced timed automata attach running costs to locations and one-off costs to edges; minimum-cost reachability concerns the infimum over paths reaching the target. | The cited construction uses a passive cost variable. An inexpensive successful path alone says nothing about all environmental choices or expected expenditure. | [Behrmann et al., 2001](https://link.springer.com/chapter/10.1007/3-540-45351-2_15), abstract; [author report](https://www.brics.dk/RS/01/3/BRICS-RS-01-3.pdf), §2. |
| I02-PROB | Probabilistic timed automata retain nondeterministic choices alongside discrete probabilities. Minimum/maximum reachability probabilities range over the stated adversaries; expected reachability costs are another objective. | The digital-clocks result has a closed, diagonal-free syntax and a time-divergence condition. It is not a translation theorem for arbitrary UPPAAL XML. | [Kwiatkowska et al., 2006](https://link.springer.com/article/10.1007/s10703-006-0005-2); [author manuscript](https://www.prismmodelchecker.org/papers/fmsd06.pdf), §§2.2, 3–5, especially Definition 8 and Theorem 24. |
| I02-SMC | SMC samples a stochastic interpretation and produces probability intervals or statistical hypothesis-test decisions. | The 2015 tutorial studies fully stochastic controllers/environments, while discussing extensions for nondeterminism. Its results do not quantify over every unresolved scheduler. Report the bound, sampling/stopping procedure and error parameters. | [David et al., 2015](https://vbn.aau.dk/en/publications/uppaal-smc-tutorial/); [tutorial](https://uppaal.org/texts/uppaal-smc-tutorial.pdf), §§1–3. |
| I02-ENGINE | Current tool restrictions must be checked separately from a paper's formalism. | PRISM digital clocks rejects strict/diagonal clock constraints. UPPAAL SMC requires non-blocking inputs, input determinism, defined delay distributions and absence of time locks/Zeno behavior. These are obligations, not results of this review. | [PRISM language manual](https://www.prismmodelchecker.org/manual/ThePRISMLanguage/Real-timeModels), engine restrictions; [UPPAAL semantics](https://docs.uppaal.org/language-reference/system-description/semantics/), “SMC Limitations”. |

Support locators, publication metadata and access dates are in [sources.json](sources.json).
Source descriptions above are paraphrases; the application choices below are our
inferences from those sources and the pinned local inputs.

## Consequences for this model

The inspected input is
[`uav-service-completion-candidate/model.xml`](../../instantiation/uav-service-completion-candidate/model.xml),
SHA256 `b8ab50e112b71491f8242789cc7906497baf8440c473d7a5a4d5214840187e02`,
as stored at the base commit. This is static inspection only. It neither consumes
nor modifies the ongoing #89 campaign.

1. **Do not invent probabilities from choices.** `C82_ResultJob` has delivery and
   loss edges out of `Transmitting`, with the same local clock/active guard (XML
   lines 8029–8040); delivery also requires a receiver. Nothing in these two
   alternatives specifies a measured loss rate. Assigning each a weight of one
   would introduce a new stochastic assumption, not recover an existing one.

2. **Preserve the requested outcome and clock origin.** A prospective success
   measure should start at actual request emission (`c82_emit_request`, lines
   862–870), retain request/sample identity and quality, and count actual APP
   receipt. Admission, rejection, failure and cancellation are not successful
   delivery. A probability conditional on admission differs from a probability
   per sent request. Define the trial and how no-send runs are handled before
   choosing a formula. A global-time horizon must not silently replace time
   elapsed since sending.

3. **Preserve strict freshness.** APP delivery guards include
   `c82_sample_age < 5` (for example line 4154). They fail the cited digital-clocks
   syntax restriction as written. Replacing `< 5` with `<= 5` admits a stale
   boundary point; replacing it with `<= 4` discards valid dense-time ages such as
   4.5. A different engine or a justified, property-specific encoding is needed.
   This is an applicability obstacle, not a claim that all PTA methods are
   unsuitable.

4. **Audit synchronization before SMC.** The model declares ordinary handshake
   channels `c82_sense_start`, `c82_measurement` and `c82_result_delivery` (lines
   859–860). For each prospective sender, establish receiver availability and
   uniqueness under the selected stochastic semantics. The current documentation
   permits a non-blocking handshake; the tutorial's broadcast presentation is
   therefore not a blanket present-day ban on handshakes. A global conversion to
   broadcast would change behavior and needs its own model decision.

5. **Separate optimization from reliability.** A least-cost successful execution
   is an optimistic planning question. For a resilient controller facing
   uncontrolled failures, define which choices the controller owns and the
   adversary/policy class before selecting a method. For an expected cost, specify
   whether failed requests count and how nontermination is treated. Cost per sent
   request, cost conditional on success, and cost until termination are different
   measurements. The qualitative `Pi_PHY` policy score is not a calibrated energy
   integral (see `src/uppaal_mcp/phy/defaults.py`, `limitations`, lines 360–363).

My recommendation is to retain the current symbolic obligations and describe
SMC as a later, separately validated experiment on one declared service policy.
First obtain arrival, failure and delay data, including correlations; then define
the stochastic model, stopping rules and request-centred observation. Study a
probabilistic model with scheduler bounds when policy uncertainty is the question.
Introduce a cost model only when its rates, units and objective are justified.
This recommendation does not authorize any run or modify any gate.

## Integration instructions

- [proposed-text.tex](proposed-text.tex) is an English **non-standalone snippet**
  for P9a/P9b, not an edit to the manuscript. Replace the paragraph beginning
  “Statistical model checking is a plausible quantitative extension.” in the
  published `papper/paper-source/levels_tex/samplepaper.tex` (line 256 at the
  base), or its successor in the integration branch. Rebuild and check pagination
  there. Do not insert a second competing future-work paragraph.
- Merge only the two entries from [references.bib](references.bib) into the
  integration bibliography. Keep the existing `uppaal_smc_2015` entry. The root
  `levels_tex/samplepaper.tex` and the packaged manuscript differ at this base;
  select the current P9 revision explicitly instead of patching a stale copy.
- Suggested reviewer-response text: “The future-work discussion now distinguishes
  cost-optimal reachability, probabilistic analysis with explicit scheduling
  assumptions, and statistical estimation. It identifies the additional inputs
  and semantic checks needed for this ISAC model. These are research directions;
  no probabilistic or cost result is claimed.” Use this only after actual insertion.

The first added reference follows Springer's title **Priced Time Automata**;
the author report says **Priced Timed Automata**. Both refer to the same cited
work. The second entry is the 2006 journal paper, not the 2003 conference version.
The existing SMC reference remains dated 2015 despite the reformatted PDF's later
date. Original publication metadata is separate from this review's access date.

No SMC experiment, probabilistic model translation, energy calibration, new
verification verdict or independent acceptance is delivered here. Checks and
reproduction commands are in [HANDOFF.md](HANDOFF.md).
