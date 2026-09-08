# P2 decisions and remaining obligations

Issue #17. All choices below are proposals; independent acceptance is pending.
P1 is used as a source of findings, not as an accepted calibration result.

| P1 input / composition question | Decision for this specification | Required implementation or review |
|---|---|---|
| Boundary equality contradicts declared worse_class | Numeric demo classifier is not a source for the finite-class test envelope. Proposed age mapping has explicit worse-side equality at 5 and 10. | A future raw-metric adapter must implement the reviewed equality rule for every threshold and reconcile the TeX; phy/alpha.py and TeX are outside this Issue and outside the current P2 source write list. |
| Missing STALE / SUSPECTED values | Finite input domain retains STALE and SUSPECTED; they are not declared unreachable just because demo classify_sample omits them. | Implement complete finite input selection and review physically realizable combinations. |
| Empty/invalid inputs | No valid report until sampled; missing remains explicit. | External adapter rejects nonfinite/missing raw fields without turning them into nominal values. |
| SINR units | No raw SINR conversion in this abstract case. | A physical profile must pin linear ratio or dB and radio configuration before choosing thresholds. |
| Rfa rate versus probability | Abstract Rfa class only; it is not a false-alarm rate measurement. | Pin exposure denominator, unit and observation window before calibration. |
| Receipt age versus information age | Use source age including bridge delay, warn at 5 and expire at 10 abstract units. | Introduce validity/age storage and explicit expiry; remove success-producing receipt reset assumptions. |
| Unbound D_cmd | Introduce D_cmd=1 abstract unit for selected command delivery. | Bind a real bridge clock; no assertion that this equals physical beam-control latency. |
| Capacity/queue labels | One finite aggregate queue and one link; no packet-count capacity. | A capacity/scalability study requires explicit entity dimensions and resource-sharing model. |
| Admission/ACK timings | Preserve source constants as separate namespaced clocks; bridge bound=1. | Resolve missing APP timeout, pre-send MAC ACK clock reset and typed SDN ACKs; review total budget. |
| Canonical parameter set | Candidate values are fully identified in inventory/vector but not frozen. | P1/P2 review and P0 supersession decision required; no manifests edited here. |
| No integrated model | Declare retained source components and eight missing boundary templates. | Separate P2 implementation Issue with source/test scope, then review actual XML/queries. |
| APP Crit/Agg placeholders | Retain and label zero-transition placeholders; exclude claims of their full behavior. | Reviewer decides whether implementing them is necessary for the article's intended scope. |
| Counter/observer behavior | Event identity and timeout visibility must survive adaptation. | Bound or replace APP sequence counters; inspect passive observer coverage, timing and noninterference. |
| SDN location versus policy value | Preserve source observation, flag for review. | A_POLICY's edge guards and select_sdn_policy priority chain are not identical; A_RISK guards can overlap. Review agreement between location names and assigned finite values before making determinism claims. |

## Handoff boundaries

This Issue owns the specification package for R01/R02/R05/R06. Subsequent P2
implementation must reference it and retain one primary owner per reviewer ID;
do not duplicate ownership by independently claiming closure in another process.
Manuscript changes remain P9a/P9b-only. Any manifest change needs the separate
governance decision defined by the repository. No P3 or P4 runs are started here.

Reviewer acceptance can accept this **specification deliverable** while still
requiring the integrated_model, interface_contract and instance_vector to be
implemented and accepted for overall P2/Gate 1. A merged PR alone does not close
scientific requirements or constitute baseline freeze.
