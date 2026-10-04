# Proposed article text and R04 response

For independent review and P9 integration. These paragraphs have **not** been
inserted into the manuscript. Citation keys are supplied in `references.bib`;
the integrator should deduplicate them against the manuscript bibliography.
All new mathematical claims depend on acceptance of `PROOF.md` and its premise
audit. Existing native verification tables must retain their original statuses.

## Article: scalable verification discussion

Glonina's analysis of modular computing systems distinguishes verification of
component contracts from a proof that their composition yields correct and
deterministic observable timed diagrams [Glonina2020DissertationR04, pp. 63–64,
79–86]. This distinction enables configuration analysis using representative
executions once the required component and composition arguments have been
established; the associated tool separates UPPAAL component verification from
execution of generated configuration models [Glonina2020ToolR04, pp. 21–25].
These results do not imply a general cutoff on the number of interacting UAVs.
For example, Proposition 6 bounds array sizes by the number of relevant index
variables and selection functions under class-specific restrictions, whereas
Proposition 7 concerns synchronization sequences within one array-processing
iteration. Its observer corollary requires sizes 1, 2 and 3, together with the
specified structural and timing conditions [Glonina2020DissertationR04,
pp. 165–191]. Our unrolled UAV family, persistent queue state and ordered shared
environment have not been shown to satisfy those conditions. We therefore retain
the accepted finite domain N=1,2,3,4 rather than inferring unbounded-network
verification from the finite experiments.

## Article: worked property-specific reduction

For one structural safety property, a direct projection is sufficient. Let
`g_i` denote the recorded service grant for UAV i and `l` the most recently
selected server index. Initially `l=-1` and all grants are false. In the frozen
family, the only writer selects `j in {-1,...,N-1}` and assigns `l=j` and
`g_i=(j=i)` for every i on one internal transition; every other transition and
delay preserves these variables. Induction therefore establishes
`g_i <-> (l=i)` in every reachable state, implying
`sum_i 1[g_i] = 1[l != -1] <= 1`. The relevant observation consists of N+1
reachable states, and a forward simulation from the full composition justifies
transfer of this safety predicate. The evidence package checks the exact
model/query hashes, initialization, unique writer, unchanged selector, complete
update, process instantiation and absence of other references to the protected
variables for each accepted N.

This is a mathematical invariant argument supported by static checks and finite
abstract enumeration. It is separate from the twelve native `shared-capacity`
attempts, all of which retain their timeout status and lack a property verdict.
The grants record service opportunities, not acknowledgements or useful packet
departures. The projection does not establish concrete service reachability,
fairness, queue safety, SLA satisfaction or the cost of exploring the complete
timed state space. In particular, an existential witness in the overapproximation
need not be realizable by the full model.

## Reviewer response: R04

Thank you for pointing us to Glonina's dissertation. We studied the component
verification method, its composition/determinism argument and the parameter
reductions in Appendix B. The accompanying comparison identifies the exact
hypotheses that matter for our model. In particular, the array-size results are
conditional results for specified component/observer classes; they are not a
general rule that verification of a two-UAV instance implies correctness for
arbitrarily many UAVs. We distinguish Proposition 7's one-iteration result from
its observer corollary, which uses sizes 1, 2 and 3 under additional conditions.

We also provide a worked reduction for the recorded shared-service capacity.
The full model projects onto the grants and selected server. A single internal
writer preserves their exact correspondence, yielding an inductive bound of
one recorded grant. The package includes the full-to-abstract simulation
argument, source/model claim map, hash-pinned premise checks, adversarial
mutation tests and reproducible abstract graphs for N=1,2,3,4. It explicitly
separates this mathematical argument from the native timeout results and leaves
service nonvacuity and network liveness unresolved.

**Use after review:** replace the last paragraph's references with the accepted
manuscript section and supplementary-artifact identifier. Do not state that a
revision has been submitted or that R04 has been accepted until the integrator
records those actions.

## Claim-to-evidence map

| Proposed claim | Evidence | Kind and limit |
|---|---|---|
| Glonina separates component obligations, composition/determinism and configuration execution | `GLONINA.md` sections 1–2; D1 pp. 63–64, 79–86; D2 pp. 21–25 | Primary-source analysis, not an ISAC theorem |
| No imported cutoff has been established for our UAV family | `GLONINA.md` sections 2–3, with concrete XML selectors | Applicability assessment; does not prove that no future reduction exists |
| Grants correspond exactly to the recorded server in each accepted instance | `PROOF.md` sections 2–4; `generated/certificate.json` | Mathematical argument plus static premise audit; independent review pending |
| The observation graph has N+1 reachable states | `PROOF.md` section 5; generated graphs in the certificate | Abstract enumeration; not UPPAAL explored-state counts |
| All twelve historical shared-capacity attempts are timeouts | `generated/historical-runs.json` and its pinned original records | Historical native evidence; verdicts remain null |
| The proof does not establish concrete service witnesses | One-way simulation and spurious zero-time abstract action in `PROOF.md` | Preservation-direction argument; no fabricated concrete trace |

## Integration exclusions

Do not replace a native result cell by “satisfied,” report a measured speedup,
describe the result as physical channel capacity, remove the nonvacuity caveat,
or extend the accepted generator domain. Do not label this elementary invariant
as a novel general parameterized-verification algorithm. Its value is the
explicitly checked argument for a specific property of the full frozen model.
