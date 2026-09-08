# Gate 1 decision proposal — not an acceptance record

**Recommendation: keep Gate 1 pending.** The merged integrated candidate is
reproducible, but independent scientific acceptance and a qualifying license
check are missing. This report prepares the decision; it does not make it.

Issue #21, owner artmus208. Base `origin/read` is
`bb5741b45480944630e1116fb7435effb2026655`. All report changes are confined to
`evidence/governance/20260908-gate1-readiness/**`. No scientific IDs are closed.
The directory retains the requested 20260908 name; the run name uses the local
20260909 date. Machine timestamps record UTC (2026-09-08 at capture).

## Gate requirement matrix

The [machine-readable matrix](readiness-matrix.json) gives exact artifact hashes,
commits, evidence pointers, decision references, roles and next actions. `ready`
means only that the stated artifact/check is demonstrated. It is not approval of
the scientific interpretation. All nine requirements in the active collaboration
manifest are covered, plus five explicit requirements from v1/CONTRIBUTING.

| Requirement | Status | Remaining action |
|---|---|---|
| P0 candidate exists | ready | Preserve its historical identity during supersession. |
| P1 parameter decisions accepted | blocked | Independent decision in #15 on abstract scope, units, bounds and calibration obligations. |
| P2 integrated model accepted | blocked | Independent specification/implementation decisions in #17 and #19. |
| Integrated XML present | ready | Review the exact reproduced bytes. |
| Interface contract accepted | blocked | Accept or correct the proposed contract and implemented adaptations. |
| Model/query/parameter/instance pins | blocked | Candidate pins exist; successor manifest and accepted selections do not. |
| Static validation | ready | Reproduction, integrity, reference checks and software tests demonstrated. |
| Working verifyta and license | not-demonstrated | Separately contracted minimal model-checking licensing smoke. |
| Disjoint active write scopes | ready | Recheck at freeze; snapshot includes every open Issue, conservatively. |
| Canonical manuscript source/hash | blocked | Source/PDF hashes exist; record canonical selection, build and comparison disposition. |
| Source/generator hashes and clean provenance | ready | Review explicit constructions and byte identity. |
| Query IDs and scientific coverage | blocked | Review query-to-claim mapping, observer meaning and absent numeric queue/retry bounds. |
| Tool version and audit execution parameters | ready | Saved exact commands; future P3/P4 options must be selected separately. |
| Independent Gate record | blocked | Separate accepted/rejected record with commit, time, owner and complete pins after prerequisites. |

## What was independently inspected, and what was not accepted

[GitHub snapshot](github-snapshot.json) preserves normalized Issue bodies,
comments, PR metadata, review submissions and combined discussion timelines.
PR #16, #18 and #20 are merged. #15/#17 have no Issue comments; all three PRs
have empty review and combined discussion lists. #19 comments record ownership,
diagnostics and publication, explicitly reserving scientific acceptance. The
finding is based on those decision surfaces, not on Issues merely being open.
There is no qualifying independent scientific acceptance in the inspected set.

[The #6 decision](https://github.com/artmus208/uppaal_sdn_isac/issues/6#issuecomment-5572059620)
accepts the **replacement procedure**, preserving the historical candidate until
accepted inputs are selected. It explicitly withholds scientific freeze. It
cannot supply acceptance for P1/P2 or the new integrated bytes.

Both artmus208 and carwasher authored relevant scientific inputs. This report
does not assign either as the independent accepting reviewer. The Integrator
must record a reviewer assignment satisfying separation of duties.

## Reproduction and exact provenance

New run: [gate1-readiness-001-20260909](gate1-readiness-001-20260909/checks.json).
Execution began with a clean tree at
`fa23946ac2fe52e2c157751cf9e6fe88e6179220`; its only changes from the merged base
were this report's contract snapshot, README, attributes and audit recorder.
The generated evidence was committed at
`780ba277a78d0962d980a7baf9bcd88867569dc1`.

[comparison.json](gate1-readiness-001-20260909/comparison.json) proves:

- 39 strict input files, seven integrated implementation files and the one
  operational AGENTS file equal their exact base Git blobs: 47 files total.
- Every composition metadata field except `source_commit` equals historical
  run `reviewer-scoped-005-20260908`. This includes parameter/source-parameter,
  instance, query, interface, symbol, process, adaptation and context maps.
- XML and query files are byte-identical; 50 processes partition as 20 core,
  eight boundary and 22 observers. All 81 query IDs are unique, none excluded;
  parsed process/location references and XML edge endpoints resolve.
- All 113 indexed artifacts across P1, P2 specification and the final P2 run
  match their SHA256SUMS, including the complete historical compiler output.

Historical execution commit `6f88b49a99d74dd1a5a1d96005d9838b1579c6be` is recorded
in its own evidence. Its published equivalent is
`87d1b1055e2ff320715c8792ce468f4b42775d0f`, tree
`b10e31df888520089f86a7b9eaeb5e841db05181`. The final PR #20 head
`4399fd6c25c10ef8f488bc0dca408fc191e34c5c` and merged base have the same tree
`2999195d20573e456e58b03178e7ae7910dffb7b`. Historical execution provenance is
retained; the new run never pretends to have executed at that historical SHA.

The new full suite ran once because CONTRIBUTING requires it before publication:
**147 tests, zero errors/failures/skips**, 33.421 seconds. All 13 recorded
commands returned exit 0: versions, dependency consistency/freeze, generation,
comparison, original historical audit, coordination/YAML, suite, MCP construction,
examples, whitespace and real verifyta version. The environment was an isolated
venv on WSL outside the sandbox, Python 3.12.3, MCP 1.30.0, PyYAML 6.0.3, with
process-level UTF-8/bytecode/Git newline overrides recorded in checks.json.

Actual version: **UPPAAL 5.0.0 (rev. 714BA9DB36F49691), June 2023**.
The historical real compile-only result is reused for the identical XML/query
bytes. Compilation was not repeated. Version/help/compile-only and a printed
licensee name do not establish that the engine can perform model checking now.
No property exploration or licensing smoke was executed by this task.

## Scientific decisions required before selection

Every question below has a concrete source in the pinned
[P1 report](../../validation/20260907-p1/validation-report.md),
[P2 specification decisions](../../instantiation/20260907-p2-scope/decisions.md),
[interface contract](../../instantiation/20260907-p2-scope/interface-contract.md)
or [implementation decisions](../../instantiation/20260908-p2-integrated/decisions.md).
Their exact hashes are in comparison.json and the machine matrix. These are
review obligations, not model defects newly fixed in this Issue.

| Topic | Implemented/proposed evidence | Required reviewer decision and role |
|---|---|---|
| Abstract bounds and physical units | Default layer constants; D_cmd=D_bus=1, input/MAC periods=5, demand=1, completion=40, fault window [12,13], age thresholds 5/10. No seconds-per-unit scale. | P1 reviewer: accept explicitly abstract assumptions or require calibration data/units. Review admission and ACK endpoints/budgets; equality of layer constants is not a compositional deadline proof. |
| Boundary policy and raw measurements | P1 reproduces eight better-side equalities despite worse_class metadata; finite input generation bypasses the raw demo classifier. Age equality is explicitly STALE at 5 and EXPIRED at 10. | P1/P2 reviewer: accept exclusion of the raw adapter and its conflicting TeX/demo policy from present claims, or require a separate scoped correction. SINR linear/dB, Rfa exposure denominator and missing/invalid-value handling remain unresolved for physical deployment claims. |
| APP placeholders and admission | Crit/Agg remain zero-transition templates. Request fields are staged, but the SDN policy treats a request as an abstract trigger; preservation of strict requirements is not enforcement. Reconfiguration is only logged. | P2 reviewer: explicitly accept these exclusions as sufficient for the article's scope or require new P2 implementation. Do not infer complete service/criticality/aggregation behavior from process names. |
| Source age and telemetry aggregation | Generation-time clock, latest mailbox, overwrite/loss flags, old delivery invalidated at new sampling; sensing PHY age drives shared SDN freshness while MAC contributes slice inputs. | P2 reviewer: accept age metric, conservative invalidation, fan-out order, one-slot loss model and simplified multi-source aggregation, or request corrections. Review arrival/expiry coincidences. |
| Observer/event adaptation | Eight APP counters become oldest-outstanding latches; repeats before a response are coalesced. PHY timing checks move to committed receive-followup locations. Other guard-polled triggers remain. | P2 reviewer: decide whether one response legitimately discharges coalesced events; review each mapped formula, deadline visibility, coverage and noninterference. Replay tests are not timed verification or trace-equivalence proof. |
| Finite environment | One BS/UAV/link/controller/service, one optional fault, sampled finite tuples, independent scenario labels and possible physically inconsistent combinations. Missed offers/losses remain possible. | P1/P2 reviewer: accept exact envelope and exclusions or require a concrete abstraction relation. Completion at 40 does not stop all other processes; no global horizon, time-divergence or fairness proof is supplied. |
| Policy/ACK semantics | Typed rule/control/recovery ACKs, staged payloads, MAC send-time ACK-clock reset and explicit loss paths; retained SDN policy-location versus selected-value ambiguity and overlapping risk guards. | P2 reviewer: accept semantic adaptations and retained nondeterminism; review channel ownership and deadline equality. A delivery ACK is not successful beam recovery/routing/SLA fulfillment. |
| Query coverage and downstream C01/C02 | 81 candidate formulas with source mapping and observer reachability queries. Finite queue/resource labels and enabled-policy counts are not packet-capacity or retry-count bounds. | Independent scientific reviewer with P1/P2 owners: record the intended C01/C02 interpretation, suitable bounded-response observers and absent numeric dimensions before freeze. If implementation is needed, assign a separate scoped P2 Issue; do not start P3 here. |

## Proposed successor and safe handoff to the next task

[proposed-baseline.json](proposed-baseline.json) is a report artifact, not an
active manifest. It proposes `reviewer-r1-integrated-single-uav-v1`, remains
`frozen:false`, includes all parameter constants, vector bindings/order, 81-query
map, source/context/implementation pins, manuscript/PDF hashes and claim limits.

| Pin | SHA256 |
|---|---|
| Integrated XML | `2b6928bda92bfb9bad5c74e91cf78c0b15beb4e7300bea401de8b4dc2cf592a4` |
| Query bytes | `af9bbd8e73b1bc73eb7e957a89b826d24e04f1c2f1eed2f1b1e5bb4a55cd25b9` |
| Integrated implementation aggregate | `3a949a322f5404816e94966882b300f9d30b34af6605b1617289bccb8fc13aa8` |
| Complete parameter-set artifact | `33b3c54bb51090f40b85e3b1e795cf6ef8ebf2c1affe8de6047fe93370d26911` |
| Extracted instance-vector artifact | `12395becdff53baae71f7094c82c55cd4def6370d692a16fc8f13966541776b8` |
| Query mapping artifact | `cee791090504547e87f8fa8266445d5e0727dd8a77bb7dec45e0bc31be12b96f` |

The extracted vector has its own serialization hash; the original specification
file remains pinned at `ebbaabd0603eb3dfc8b537b19e61e36f35878f84173cca398e243871eb572a45`.
Its historical `proposed_not_implemented_not_accepted` status is retained as input
provenance, not misreported as the current implementation state. The proposal
also distinguishes all-39-input `source_hash`, four-formalization hash and the
seven-file implementation aggregate. These constructions must be accepted
explicitly; they must not silently replace the old aggregate definitions.

Next steps belong to separate contracts and independent decisions:

1. Assign an independent scientific reviewer; record P1/P2/interface/parameter/
   query-scope dispositions in their owning Issues. Accept exact artifacts or
   return concrete corrections to separately scoped P2 work.
2. Create a minimal licensing runner Issue: exact tiny fixture/query, engine
   command/version, run directory, environment, stdout/stderr and result capture.
   Its only claim is engine/license availability for that fixture/environment;
   it supplies no integrated-candidate verdict and is not P3/P4.
3. Record canonical manuscript selection and build/PDF-comparison disposition.
   This report only hashes existing files; it neither builds nor edits the paper.
4. After prerequisites, create a dedicated P0 supersession/freeze Issue with an
   exact successor path such as `manifests/baselines/reviewer-r1-integrated-v1.yaml`,
   any required exact active-pointer path, and its own governance evidence path.
   Obtain accepted Integrator authorization before manifest edits. Coordinate
   overlapping manifest ownership with still-open #6 first.
5. Account for strict pins: `inputs.py` enforces the old baseline and scientific
   manifests through the P2 inventory. Altering those files may reject generation
   even when model bytes would be unchanged. Preserve the historical pinned
   inputs; if activation requires their replacement, prepare a separately scoped,
   reviewed P2 pin update and prove relevant model/query bytes again. This report
   does not authorize weakening scientific pins or extending AGENTS exemption.
6. Recheck live scopes/refs; record Gate 1 accepted/rejected with exact commit,
   hashes, parameter/vector/query set, tool configuration, reviewer identity and
   timestamp. Only an accepted Gate 1 can permit the separately assigned P3/P4.

No acceptance, manifest replacement, licensing run or P3/P4 execution is performed
by this handoff.
