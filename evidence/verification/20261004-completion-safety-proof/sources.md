# Sources and claim map

Accessed 2026-10-04. The semantic references below are primary UPPAAL
documentation, consulted directly. No dissertation or secondary literature
is needed for this separate P3 result.

| Source | Exact section / use |
|---|---|
| [UPPAAL system semantics](https://docs.uppaal.org/language-reference/system-description/semantics/) | Initial states, Delay Transitions, Binary Synchronisations: guard/update order and the induction step. |
| [UPPAAL symbolic query semantics](https://docs.uppaal.org/language-reference/query-semantics/symb_queries/) | Invariantly and State Properties: reachable-state meaning of A[] and observation after a complete action. |
| [Gate 1 A/B](https://github.com/artmus208/uppaal_sdn_isac/issues/84#issuecomment-5946722646) | Exact model/query input acceptance, single-request assumptions and abstract age boundaries. |
| [Selection C](https://github.com/artmus208/uppaal_sdn_isac/issues/84#issuecomment-5947256320) | Authoritative P3 selection at merge 46bf268c66d6ec2c106ae4ce8e8d5f893315ad91. |
| [Issue #108](https://github.com/artmus208/uppaal_sdn_isac/issues/108) | New assignment, roles, base and sole write scope. |

The proof and the conclusions about this XML are our argument, rather than
claims quoted from the documentation. No web page is treated as evidence
of a model-checking verdict.

| Proposed claim | Evidence and boundary |
|---|---|
| Completed implies all 26 frozen conditions | proof.md Theorem 1; check.py; certificate.json; premises.json. Mathematical argument, pending independent review. |
| The receipt record survives future actions/delays | Strengthened invariant inactive plus closed 29-site writer classification in the same artifacts. |
| Successful completion has an ordered causal history | proof.md Theorem 2 and sealed event graphs/helper bodies. Human argument with static binding, not a proof-assistant derivation. |
| Ages were <5 / <=40 at receipt | Unique reset events plus entry guards; does not bound clocks forever after completion. |
| At least one successful history was previously produced | historical-evidence.json: saved replay-001, 100 accepted transitions; audit_history.py reads the preserved raw archive without rerunning UPPAAL. |
| Previous universal search did not finish | Exact #87 result/raw stdout references and hashes in historical-evidence.json/history-pins.json: timeout/null preserved. |
| Premise checker detects listed broken assumptions | tests.py and checks-final/scoped-tests.stderr.txt. Software tests, not changed-model UPPAAL counterexamples. |
| English material ready for integration review | article-snippet.md. Manuscript unchanged; Integrator chooses wording after acceptance. |

All repository inputs are consumed at operational base
f0fcd770e3e6b93f99868b9116e4f0929f60d0fa or later commits of this branch that add
only this evidence package. Exact model/query/manifest byte hashes are in
certificate.json; historical raw-file and archive-entry hashes are in
historical-evidence.json. The external documentation URLs are semantic
references, not immutable experimental artifacts.
