# Title: 18100004273 A Hierarchical Timed-Automata Evaluation Model for Resource Orchestration and Resilience in SDN-Enabled Computation-Centric 6G ISAC Networks 

Comments and Suggestions for Authors

## Review 1

### 6. Comments and Suggestions for Authors (will be shown to authors)

#### Strengths:

- Clear hierarchical architecture: PHY, MAC/resource scheduling, SDN/RIC control, and application/SLA layers are represented as synchronized timed automata with explicit contracts and deadlines.
- The availability of a public UPPAAL XML model repository and screenshots increases reproducibility and practical usefulness.

#### Methodological clarifications:
- Provide more justification for discretization thresholds used for PHY quality classes (e.g., GOOD/WEAK/OUTAGE, FRESH/STALE) based on external radio or system-level analysis.
- Add one or two concrete service scenarios (e.g., UAV detection, industrial telemetry) traced from PHY states to SLA formulas to illustrate end-to-end use of the model.

#### Presentation and figures:

- Ensure that UPPAAL screenshots have readable state names, channels, and guards; consider enlarging key templates.
- In tables describing channels and deadlines, consider indicating typical deadline magnitudes or ranges to connect formal notation with intuitive network delays.

#### Discussion and limitations:

- Expand the discussion of how this UPPAAL model is expected to interact with conventional simulators (e.g., NS-3, Omnet++) in a typical design workflow.
- Briefly outline which statistical extensions (priced/probabilistic timed automata, statistical model checking) the authors consider most promising for future work.

#### Language:

- Perform a language and formatting pass to remove merged words, shorten very long sentences, and improve readability, especially in the introduction and cross-layer semantics sections.

## Review 2

### 6. Comments and Suggestions for Authors

The four-layer (PHY/MAC/SDN-RIC/Application) timed-automata decomposition is a clearly conceived architecture, and Section 8 lists a sensible set of verification properties (deadlock freedom, bounded response, cross-layer consistency). However, the manuscript stops at the modeling stage: the paper explicitly frames itself as "intended for" UPPAAL verification rather than reporting it, and no reachability results, model-checking output, or counterexamples are actually shown - the properties are proposed, not evaluated. I'd recommend the authors run and report at least the structural-correctness checks (Eqs. 10-12) and one bounded-response property on the actual XML models, since this is what would turn a modeling proposal into a verification result. The included UPPAAL screenshots (Figs. 1-4) are also too dense/small to read at any typical print size and should be replaced with cropped, zoomed views of the relevant automaton fragments. Please reformat for the target venue - the abstract currently self-describes the paper as "a unified, Springer LNCS-formatted article," which is inconsistent with an IEEE conference submission.

## Review 3

### 6. Comments and Suggestions for Authors

The paper describes a set of timed automata for modeling the 6G network resource orchestration. The authors state that the model composed of these automata is intended for verification, and provide examples of properties to be verified.

One of the main issues in modeling is the validity of the model. The paper should describe in more detail how the automata and their composition were validated for representing the actual network behavior.

A real-world network is composed of multiple instances of network agents (base stations, portable devices, UAVs, etc. The paper does not clearly describe how many instances of automata are created to model a network, and scalability discussion is missing. Only possibility of verification is stated, but no information on actual verification attempts is provided, along with the amount of necessary computational resources. The Introduction lacks references to existing timed automata models of network protocols.

#### Following improvements of the paper are recommended:

* Include references to existing timed automata models of network protocols into the Introduction.
* Describe the approaches to validation of the model, i.e. checking that it reproduces the properties of the modeled network (to not mess it with checking the model for requirements to the modeled network).
* During several months from paper submission, the authors likely tried to perform verification of the model; the results should be briefly presented, in order to confirm the actual possibility of verification and describe the necessary computational resources. Just declaring the possibility of verification is not enough, as there is a risk of state explosion.
* Possibility to model a network with multiple agents (by multiple instances of automate) should be discussed. The authors are strongly encouraged to read the Ph.D. thesis of A. Glonina (https://istina.msu.ru/dissertations/364890262/) in which a timed automata model of a complex scheduler is developed, supporting multiple instances of automata for computational tasks. In this thesis, several properties were verified for a model with an unbounded number of automata instances, and constraints on such automata were formulated that allow such scalable verification. If automata models for 6G network agents were developed under these constraints, then the model will both represent a network with many base stations, devices etc., AND be verifiable for a valuable set of properties.
* The figures should be placed closer to the corresponding sections; currently it is typical that a depiction of an automaton is in the section about another automaton.
* Screenshots of automata should be cleared of garbage, such as a corner of a window (Fig. 3), mouse cursor (Fig. 4).
* At least one automaton should be described in more detail, to uncover the logic of abstraction that allows to limit its number of states and transitions.
