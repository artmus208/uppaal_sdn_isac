# Scientific evidence review for integration #92

Reviewed 2026-10-03 against `origin/read` commit `452571598d4a5c1e070dace3a918ea737904e239`. Scope: source inspection, saved-result aggregation and live GitHub decisions; no verifier, replay, GUI experiment, source-model edit or GitHub mutation. This updates the existing `chat_histories/03.10.2026-audit-prism.md` audit only where needed for integration. It is not scientific gate acceptance.

## Claims that can be used

1. The historical 50-process model has actual positive existential results and negative universal results. Its aggregate queue reaches the absorbing overflow witness after five arrivals without service at capacity four. Control ACKs do not dequeue work.
2. The finite-family P4 experiment executed 90 scientific attempts: 12 satisfied, 6 violated, 72 timeout. It measures verifier cost under a fixed budget, not operational network scalability or a general cutoff.
3. The changed 51-process model has one reproducible successful, request-correlated symbolic execution: 100 transitions, 101 states, request age exactly 14 at receipt, sample age in [4,5). This is simulation/replay evidence, not a universal SLA or a successful exhaustive query.
4. All eleven exhaustive attempts on that exact 51-process model timed out, with null verdicts. They neither prove nor refute their formulas. Queue/recovery bounds and a genuine universal bounded-response formulation remain coverage gaps in that eleven-query package.
5. All time values in the models are abstract. No physical calibration, ns-3/OMNeT++ experiment, or general concrete-to-abstract soundness result is supplied by these packages.

## Current decisions: acceptance is distinct from merge

- v2 was activated at `2026-09-28T20:38:12Z`, activation commit `05ac107789532b6d2eac9914433a4b8408835057`, after PR #65 merged. This changes operational coordination, not scientific gates: [#64 decision](https://github.com/artmus208/uppaal_sdn_isac/issues/64#issuecomment-5878071165).
- Historical P3 core C01-C05 has an explicit qualified acceptance decision; C06 and Gate 2 are excluded: [#39](https://github.com/artmus208/uppaal_sdn_isac/issues/39#issuecomment-5834333757). Do not erase this decision because later local files retain proposal wording. Conversely, the decision must not be stretched into automatic acceptance of every later whitelist revision or a new model. The later `p3-20260926-core-acceptance/accepted-runs.json` is useful as a provenance registry, not independent evidence of its own acceptance.
- P4 PR #77 merged at `2026-09-29T20:56:27Z`, commit `8237e8c2bec41aa1bb943cc33be1ac9586d03759`. Live #76 comments and PR #77 reviews were empty at this review. Its PR body explicitly retains independent acceptance as pending; the saved report excludes Glonina comparison/full R03/R04/C06 closure. No separate scientific acceptance was found in these records. [PR #77](https://github.com/artmus208/uppaal_sdn_isac/pull/77).
- [#84 A/B](https://github.com/artmus208/uppaal_sdn_isac/issues/84#issuecomment-5946722646) accepts limited P1/P2 applicability and exact input Gate 1 for `uav-service-completion-r1-20261002`, N=1, 51 processes, one request/result. [#84 C](https://github.com/artmus208/uppaal_sdn_isac/issues/84#issuecomment-5947256320) activated that selection at `2026-10-02T07:18:22Z`, after PR #86 merged as `46bf268c66d6ec2c106ae4ce8e8d5f893315ad91`. D explicitly excludes universal guarantees, P3 acceptance and R07 closure. Historical preparation flags in immutable artifacts are superseded by these exact decisions only within their scope.
- PR #88 **is now merged**, at `2026-10-03T10:16:57Z`, commit `452571598d4a5c1e070dace3a918ea737904e239`. Live PR reviews were empty. Its body and [#87 handoff](https://github.com/artmus208/uppaal_sdn_isac/issues/87#issuecomment-5950077723) retain independent budget/coverage disposition as pending. Merge is not a positive verdict or scientific gate acceptance. This supersedes the older audit's statement that PR #88 awaited merge. [PR #88](https://github.com/artmus208/uppaal_sdn_isac/pull/88).

Live source response projection: `evidence-github-snapshot.json` in this directory records the consulted Issue comments, PR metadata/body and empty review arrays.

## Exact model identities

| Configuration | Processes | SHA256 of exact model XML |
|---|---:|---|
| `reviewer-r1-gate1-20260923` | 50 | `592678ed678ce8f70cf278f542e48bd2bb739969b53a962423d3e63f91e3e1e2` |
| `uav-family-r1-20260929`, N=1 | 50 | `5234cb087e5274798926d516dedc77d1f9542ea7df59cec39f83859771ce1385` |
| same family, N=2 | 99 | `e7ac599140b7beeb94acdf0e3535a727c2eccc40aa15314afa3371eb09700208` |
| same family, N=3 | 148 | `aa1c0ecf1a0e8846421ebff91ac19ffc1645724d4309a38c568edbf23273ce90` |
| same family, N=4 | 197 | `e8a4cdb0a4ea795ca2c90a0dfdee8cff7b9fbc3093369fa8141d61750a28033a` |
| `uav-service-completion-r1-20261002`, N=1 | 51 | `b8ab50e112b71491f8242789cc7906497baf8440c473d7a5a4d5214840187e02` |

Old-family construction is 49N+1 processes: per UAV 20 core, 22 observer, 7 private boundary processes, plus one shared service boundary. The 51-process composition retains all 50 N=1 processes and adds one result job; it also changes selected existing templates and must not be described as behaviorally equivalent merely because most instances are retained.

## Historical P3: precise interpretation

Primary sources: `evidence/verification/p3-20260926-dispositions/README.md`, its `audit.json`, `evidence/verification/p3-20260926-core-acceptance/accepted-runs.json`, and the immutable raw archives identified in each registry row. The registry's 43 full-model selected records contain nine explicit results (seven existential witnesses, two counterexamples), 32 timeouts and two errors. Four separate reduced/control results and one recovered resource diagnostic are different evidence classes; do not pool their counts as full-model successes.

For historical run `p3-20260923-003`, raw `run.yaml` additionally confirms native Windows 11 build26200, Ryzen5 1400 (4 cores/8 logical), RAM17106464768 bytes, a WSL driver,60s per-query limit and2GiB sampled stop. Do not apply that host description automatically to every historical run.

The queue counterexample is `p3-20260923-003-02-C01-queue`, `status=success`, `verdict=violated`, query `A[] !mac_queue_overflow_seen`, query SHA256 `694501c262583dfe43e22a907f10080795fd63b8bc534a11cd9338c84a704051`, historical full-model hash above, UPPAAL `5.0.0 (rev. 714BA9DB36F49691), June 2023`. Raw trace: `evidence/verification/runs/p3-20260923-003.tar.xz`, member `02-C01-queue-trace1.xml`. The saved audit finds q: 0,1,2,3,4,5 through five `arrival=1,service=0` transitions. K=4; the final transition records overflow. Four matching PHY ACK transitions do not change occupancy. This is violation of the universal non-overflow property under the accepted environment, not violation of the implementation's explicit overflow contract. Trace lengths are not explored-state counts or physical duration.

The inductive recovery argument has per-episode `primary<=1`, `rollback<=1`, `total<=2` and recorder discipline. It does not prove successful recovery, service restoration or termination. Source: `evidence/verification/p3-20260925-c01-structure/README.md` and its pinned XML audit, as retained by dispositions.

The C02 reduced-model argument preserves the MAC send-to-ACK-or-ScheduleFailure clock predicate. Bounded completion is qualified by **time-divergent executions**, bound 3 abstract units. Direct full-model checking remains inconclusive; unconditional ACK completion has a saved negative result. No unconditional successful ACK, deadlock freedom, Zeno freedom, or time-divergent continuation from every request follows. Sources: `evidence/verification/p3-20260924-c02-reduced/README.md`, `evidence/verification/p3-20260925-c02-audit/README.md`, and dispositions. Reduced C02 model hash `536233940526a1716006d6769c84c9faf6dc3d7bf0e6ffa0981aa60b56a49241`; negative-control model hash `b474572cb0ceb80d821fb08ea74954569324ddfcb8dacfdfc10a1b9eea885fd6`. C02 query hash `cec919bc6e2d960160976799d3d52ff4f25eea9f136f7b0231c02cec13f162db`. Four reduced/control raw memory zeros mean no sample before exit; citable memory is null, not zero.

## P4 series: results and resources

Sources: `evidence/scalability/runs/uav-family-p4-20260929/{RESULTS.md,SUMMARY.json,query-observations.csv}`, `campaign-002/runs.json` and each cell's stdout/stderr/native monitor/traces. Baseline manifest SHA256 `5480bef5b00020735259f10eb43bdd9bc79ebc364a3bbcacad34c78fd0552cbf`; execution source `877fa69a29e1732db2b4047eebdd99591b185c77`. Tool version in every scientific record: `UPPAAL 5.0.0 (rev. 714BA9DB36F49691), June 2023`.

117 completed phases: 3 generations, 12 compile-only, 12 load/parse and 90 scientific attempts (3 repeats, N=1..4). Native verifier host: Windows 11 build 26200, AMD Ryzen 5 1400, 8 logical CPUs, RAM 17106464768 bytes; WSL orchestrator with native Windows CPU/memory measurement. One verifier at a time, search timeout 60 s, sampled memory stop 2 GiB. Observed timeout wall time 62.063-62.285 s includes process termination. Budget charged 4984.387/7200 s includes separately defined overhead, not just scientific CPU time. Minimum prelaunch available RAM 5.925 GiB. Requested memory sampling 50 ms; largest actual gap 0.618 s. No memory stops or omitted scientific cells.

| N | Processes | Attempts | Satisfied | Violated | Timeout | Observed scientific wall sum (s) | CPU sum (s) | Maximum observed memory (MiB) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|1|50|18|6|6|6|495.133|407.719|231.230|
|2|99|21|3|0|18|1161.420|931.438|147.098|
|3|148|24|3|0|21|1434.745|1204.375|183.301|
|4|197|27|0|0|27|1676.742|1465.531|210.676|

Memory is the recorded maximum of private and reported working-set measures on the target process, including censored attempts; it is not required memory to complete a query. CPU/wall sums above were computed from the 90 raw scientific rows. Different numbers of queries at each N mean these totals are coverage workloads, not one-query costs or a scaling law.

Completed-query medians and ranges (three completions each): N1 queue-full 12.467 s [8.970,14.383], satisfied; N1 u0-queue-safety 12.739 [10.458,17.330], violated; N1 family-queue-safety 13.198 [10.367,14.500], violated. Joint-backlog: N1 2.792 [1.986,3.241], N2 15.335 [9.249,18.804], N3 43.503 [27.799,58.968], all satisfied; N4 all three time out. Fixed-u0 queue predicates at N>=2 time out; all 12 shared-capacity attempts and all 30 per-UAV service attempts time out. Fixed-u0 and growing-global formulas are different comparisons; N service formulas form N separate queries. Fixed notification order does not justify UAV symmetry. No randomization/background-load control was used. No general cutoff, fairness, SLA or physical network capacity follows.

## The 51-process request-correlated model

Sources: `evidence/instantiation/uav-service-completion-candidate/{contract.md,parameters.json,instance-vector.json,changes.json,completion-record.json,results.json}`, `runs/simulate-006/`, `runs/replay-001/`, `raw-traces.zip`, `raw-index.json`, and governance inventories under `evidence/governance/uav-service-completion-baseline-20261002/`.

Exact scientific input commit `61386aa358805082b705dcd00c8cbfde5fb98248`; manifest SHA256 `4b4bf71f55767123cc5934074024179289fa5ad3355fa4c0e37385e8261ef98d`; generator SHA256 `a5310747b9e2f1b837d0fefdff26d04c9218b7f22a87672bfaa13e7ee58e0ba2`; selected eleven-query aggregate `2b31aad5e75374eac5b81c5e062e28eaca6ebfffb974abd32709b4f9d8ad2b23`. The older candidate query-pack aggregate uses its own construction and must not be substituted for this accepted aggregate.

One BS, one UAV, one link, one target, one SDN/MAC context, one session, one aggregate queue/server, one explicit result token, zero explicit packet objects. Processes: PHY5+MAC5+SDN6+APP4=20 core, 22 observers, 7 private boundary+1 shared boundary, 1 result job =51. APP Crit/Agg remain zero-transition placeholders; retaining them does not implement missing behavior.

| Parameter | Value and interpretation |
|---|---|
| acquisition duration | exactly 5 abstract units; deliberate new assumption |
| result transmission | one lossy attempt, bound 1 abstract unit; no retry |
| relative service deadline | request age <=40 from actual APP request emission, including admission |
| freshness | fresh [0,5), stale [5,10), expired >=10; strict UAV success requires <5 |
| deadline equality | at age40, receipt may succeed and timeout is also enabled |
| queue | K4; FIFO rank at insertion is prior occupancy+1; absorbing K+1 overflow fails result |
| shared service | optional, <=1 per 5-unit epoch, eligible COMM/JOINT; no fairness |
| identity bounds | one admitted request, one sample/result; no ID reuse |
| physical scale | unspecified; no claim in seconds/ms; update bands are sample-age abstraction, not measured update period |

Healthy execution: `uav-completion-82-20261002-simulate-006`, status `goal_reached`, source `cd40b5107b201b97b0dc31432cf9cf9f25e8f5d8`; replay `uav-completion-82-20261002-replay-001`, status `replay_complete`, source `f6adba0aee8e037557020009fc43591d732f053d`. Both have query_hash=null and property_verdict=null. Exact engine version: `UPPAAL version 5.0.0 (rev. 714BA9DB36F49691), June 2023 -- server. Licensed to Artur / ITMO University, Faculty of Software Engineering and Computer Systems (itmo.ru)`.

Replay trace/input SHA256 `7ef37b0e6abc77eace7aa270ce3aea6a35d10724cb662508e1f54104123ddfaf`. Milestone states: 4 actual request/reset, 62 admission, 84 actual matching PHY sample, 85 queue insertion, 96 eligible token service, 99 transmission attempt, 100 matching fresh receipt/APP Completed. State100: all correlated IDs1, stored Pd/false-alarm/miss/accuracy/coverage classes0, request age14, global time15, sample age[4,5). Sample event in (10,11]; these constraints come from one consistent replay DBM. Do not replace them by independently chosen point times. Healthy completion does not require a PHY-command ACK, which is a separate control protocol. Stored sample can remain fresh when a later global KPI is stale.

Wrong received-sample-ID and incompatible sample-age controls reject at state100 after 99 accepted transitions. The stale-at-age5 diagnostic in simulate-005 follows ServiceFailed but its final run status is error/branch-cap exhaustion; do not promote it to a satisfied query. All nine native cells and failures are preserved. Total measured native wrapper wall 76.3003998 s within the original 600 s cap; this is separate from the later P3 campaign.

## Eleven-query campaign on the new model

Source `evidence/verification/uav-service-completion-p3-20261002/results.json`, with per-row exact source commits, executable hashes, commands and raw file inventories. Each query used one BFS attempt, no retries, `timeout`, verdict=null, on the new model hash above. Actual tool version `UPPAAL 5.0.0 (rev. 714BA9DB36F49691), June 2023`; executable SHA256 `4c8af2716ff61f3cf35c6d1dc408ccf306d44bb22478e104548a8f0f7a3febe5`.

Nominal limit600 s/query; aggregate observed attempt wall6607.477845500001 s, exceeding6600 by7.477845500001 s. Supplemental budget guard failed with PermissionError reading status.json. Do not call the aggregate budget compliant. Total recorded CPU6412.578125 s; max sampled RSS982.2734375 MiB. Native physical RAM17106464768 bytes; sampled stop8156 MiB/8552185856 bytes. Null explored-state metrics remain null and no diagnostic traces were emitted. Acceptance/budget disposition remains separate. The simulation witness and these incomplete exhaustive searches are compatible evidence: a directed feasible execution does not imply completed universal exploration.

## P1/P2 validation boundaries

Read the accepted scope, not only outdated proposal labels in original P1/P2 drafts. Sources: `evidence/validation/20260910-phy-revision/validation-report.md`, `evidence/governance/20260910-p1-p2-review/final-20260923/README.md`, selected baseline, and new #84 A/B applicability decision. [P1 methodological acceptance](https://github.com/artmus208/uppaal_sdn_isac/issues/15#issuecomment-5678926378) accepts V01/V04 as methodology, V02/V05 in stated abstract scope. The later #84 decision accepts that limited applicability for the precise changed model.

The source inventory covers43 layer timing constants plus14 integration parameters, later queue/attempt and new result-job parameters; provenance is illustrative abstract engineering choices, not measured bounds. Dense clocks do not imply discrete time. The finite environment excludes the demo raw-measurement classifier; its missing/NaN behavior cannot be used as evidence of good telemetry. Historical threshold equality defects were fixed in PR#24, so the old P1 finding must not be presented as current unfixed code.

The scheduler's 51840 valuations are the Cartesian product of selected finite **inputs only**, not its reachable states and not the whole model's state count. Observer removal or fewer XML edges does not prove state-space reduction or noninterference. Existing observers may constrain the composition; excluding queries does not remove that effect. Known PHY measurement5 versus period+jitter6 discrepancy and global deadlock remain open. ACK is command delivery, not result service. Local stage deadlines do not add up automatically to an end-to-end guarantee.

Proposed external workflow (not implemented): ns-3/OMNeT++ or measurements -> immutable timestamped trace -> finite-class/event conversion with versioned thresholds -> selected UPPAAL environment -> event/order/timing/outcome comparison -> discrepancy analysis. Preserve scenario/entity/transaction IDs, source-sample and observation timestamps, values/units/uncertainty, original records, versions/seeds/parameters and conversion hashes. Preserve source age across delayed/reordered delivery; reject/mark missing, nonfinite or incompatible input; define physical scale and rounding if introduced. Separate calibration data from evaluation cases and define criteria before experiments. No adapter, data exchange or empirical validation experiment is presented.

## Glonina comparison: applicability, not borrowed guarantees

Primary source: A. B. Glonina, *Analysis of configurations of modular computing systems for checking real-time constraints*, dissertation, Moscow State University,2020, `pdfs/dissertation.pdf`, SHA256 `4f8a778c52ff1e6b33383d447ebc13e91b8d18ce8161996d79d86dc32d0f5de6`. Printed page numbers equal PDF page numbers in the inspected sections. The unrelated `PHY уровень/dissertation_fragment_extracted.txt` is not this source.

| Aspect | Glonina | Present study and applicability |
|---|---|---|
| Workload/time assumptions | pp23-25: known fixed worst-case job execution/message durations and deterministic scheduling define one execution time diagram per configuration. | Finite quality inputs, optional service, loss, failure and equal-deadline alternatives are nondeterministic; no equivalent-diagram theorem. Her single-run reasoning cannot establish our universal properties. |
| Correctness decomposition | pp63-64: prove component contracts imply global correctness and determinism, then check component automata with a verifier. | A useful research method; our layer/interface descriptions do not by themselves establish that composition theorem or physical adequacy. |
| Observers/parameter checking | pp65-67: observers offer synchronization partners for all possible component actions; bad-location reachability captures violations; finite admissible parameter values and nondeterministic external-variable changes cover environments. | Event identity, reset discipline, nonblocking coverage and permitted environment assumptions must be checked explicitly. Our retained legacy observers are not all proved passive. |
| Whole-system scale | pp79-86: unknown component count and verification cost motivate mathematical proofs for the whole parameterized system; determinism proof assumes correct components/inputs. | N=1..4 is a measured finite series. No theorem transfers to our shared-resource, fixed-notification-order family; no general cutoff is supplied. |
| Inconclusive results | p67: an indefinite result does not establish component correctness; further model construction/proof is needed. | Timeouts remain inconclusive. Reporting them is valid experimental evidence but supplies no safety/SLA guarantee. |

Safe manuscript conclusion: the two works share explicit component contracts and observer-based checking, but Glonina's verified-component/deterministic-composition route has assumptions not established for the present nondeterministic network model. The observed budgets characterize this implementation and query family only. This newly written comparison is an integration draft requiring review, not retroactive R04/P4 acceptance.

## Machine-derived tuple appendix

The tables below are projections of preserved machine registries, not new runs. Full actual version banners, hardware, flags and raw-file hashes stay in the referenced registries. All SHA256 strings are exact-byte identities; no local newline conversion may redefine an input.

### Historical explicit results

All rows: status `success`; full-model rows use historical model SHA256 above. Reduced/control model hashes are given in the prose. Source: `evidence/verification/p3-20260926-core-acceptance/accepted-runs.json`.

|run_id|Scope|Verdict|Query SHA256|Wall s|Sampled peak MiB|
|---|---|---|---|---:|---:|
|`p3-20260923-002-06-queue-nonempty`|full_frozen|satisfied|`8b2bd0fe93ab5abd133b7677adc18fd339d6177314bc9a8507756c6ccfaa67cc`|11.9989029|105.023438|
|`p3-20260923-003-02-C01-queue`|full_frozen|violated|`694501c262583dfe43e22a907f10080795fd63b8bc534a11cd9338c84a704051`|19.4386224|182.917969|
|`p3-20260923-003-06-queue-full`|full_frozen|satisfied|`132fb1f5ffd023f31064a089113bf1300f99fe75ce78394fb796d2873d67e6e6`|17.2232517|166.765625|
|`p3-20260923-003-07-queue-overflow`|full_frozen|satisfied|`716ec20a3050dbbb7276f786f356042787f5611b315676fe012623d6bc551b78`|22.2454948|182.925781|
|`p3-20260923-003-12-ack-start`|full_frozen|satisfied|`3d5b58517dd881b78d198f47d517e391ca4234b2cec59701834a6ad2cd6d29e6`|11.2588259|127.488281|
|`p3-20260923-003-14-ack-unconditional-completion`|full_frozen|violated|`3f406107b55e4e196c2416c16e0573e3b362e2ff0396ab3ac696b183e252d249`|9.9051675|128.734375|
|`p3-20260925-ack-timeout-001-01-ack-timeout`|full_frozen|satisfied|`4892fb12401d1ce0a6e9b09652a39d47130aa1e0d69eb3926c8e00157a508714`|10.1930517|183.269531|
|`p3-20260925-recovery-001-01-attempt-start`|full_frozen|satisfied|`b2bd4430e694dc28cbe282e253a50b0f2554b37b0901a0bb378cec8eda3757c4`|10.0101312|177.816406|
|`p3-20260925-recovery-002-02-attempt-rollback`|full_frozen|satisfied|`941ab6cc9a4fdfb2803b0b549c2452a11e2cecbfcef52d9af712af7772fdb124`|9.8867068|177.613281|
|`p3-20260924-c02-reduced-001-C02`|C02_abstraction|satisfied|`cec919bc6e2d960160976799d3d52ff4f25eea9f136f7b0231c02cec13f162db`|0.0659991|null|
|`p3-20260924-c02-reduced-001-active`|C02_abstraction|satisfied|`3d5b58517dd881b78d198f47d517e391ca4234b2cec59701834a6ad2cd6d29e6`|0.0678532|null|
|`p3-20260924-c02-reduced-001-deadline`|C02_abstraction|satisfied|`b72ba279271b292383b371a5ce5d3766cf27b84b375403605b2b7d3b66857a56`|0.0665168|null|
|`p3-20260924-c02-reduced-001-negative-control`|negative_control|violated|`cec919bc6e2d960160976799d3d52ff4f25eea9f136f7b0231c02cec13f162db`|0.0712502|null|

Exact formulas in the same row order:

- `p3-20260923-002-06-queue-nonempty`: `E<> mac_queue_q > 0`; source commit `efc7978f398f05f072712b3ca88e3c7cfe2cc87c`.
- `p3-20260923-003-02-C01-queue`: `A[] !mac_queue_overflow_seen`; source commit `a602ec48c2c00842f8461e13db32f7bbf283f0bc`.
- `p3-20260923-003-06-queue-full`: `E<> mac_queue_q == mac_queue_K && !mac_queue_overflow_seen`; source commit `a602ec48c2c00842f8461e13db32f7bbf283f0bc`.
- `p3-20260923-003-07-queue-overflow`: `E<> mac_queue_overflow_seen`; source commit `a602ec48c2c00842f8461e13db32f7bbf283f0bc`.
- `p3-20260923-003-12-ack-start`: `E<> mac_obs_ack_active`; source commit `a602ec48c2c00842f8461e13db32f7bbf283f0bc`.
- `p3-20260923-003-14-ack-unconditional-completion`: `mac_obs_ack_active --> !mac_obs_ack_active`; source commit `a602ec48c2c00842f8461e13db32f7bbf283f0bc`.
- `p3-20260925-ack-timeout-001-01-ack-timeout`: `E<> mac_phy_ack_timeout`; source commit `e5361bdbb7daa56a0b747345390689e533524f0e`.
- `p3-20260925-recovery-001-01-attempt-start`: `E<> sdn_attempt_active`; source commit `7a4ac3c47329548612b0a563bf9cae20e3835384`.
- `p3-20260925-recovery-002-02-attempt-rollback`: `E<> sdn_attempt_rollback == 1`; source commit `bf1dc81db827e051d8e0d3b75222ee5f72b18a00`.
- `p3-20260924-c02-reduced-001-C02`: `A[] (!mac_obs_ack_late && (mac_obs_ack_active imply mac_c_obs_ack <= mac_D_phy_ack))`; source commit `ef32ac485dd95d7bf4514975c672ddd44d1d61e7`.
- `p3-20260924-c02-reduced-001-active`: `E<> mac_obs_ack_active`; source commit `ef32ac485dd95d7bf4514975c672ddd44d1d61e7`.
- `p3-20260924-c02-reduced-001-deadline`: `E<> mac_obs_ack_active && mac_c_obs_ack == mac_D_phy_ack`; source commit `ef32ac485dd95d7bf4514975c672ddd44d1d61e7`.
- `p3-20260924-c02-reduced-001-negative-control`: `A[] (!mac_obs_ack_late && (mac_obs_ack_active imply mac_c_obs_ack <= mac_D_phy_ack))`; source commit `ef32ac485dd95d7bf4514975c672ddd44d1d61e7`.

### All eighteen completed P4 rows

All rows: status `success`; exact per-N model hashes above. Source: `evidence/scalability/runs/uav-family-p4-20260929/campaign-002/runs.json`. Full raw stdout/stderr/trace paths and hashes are in each row.

|run_id|N|Verdict|Query SHA256|Wall s|CPU s|
|---|---:|---|---|---:|---:|
|`uav-p4-76-campaign-002-005-r1-n1-joint-backlog`|1|satisfied|`706bd493fef18a2de31be212156825af913ef21adde7d15cda47dc1bc1825afe`|1.9864937|1.640625|
|`uav-p4-76-campaign-002-006-r1-n1-u0-queue-safety`|1|violated|`48989eef927665697ce2687c5eccfcd99da2a9e46b97640003421fd620ca3291`|10.4575651|7.890625|
|`uav-p4-76-campaign-002-007-r1-n1-family-queue-safety`|1|violated|`c820090fc19ffc80284d62194b40f62396cdeedc10fc1db0d853f4293b64656e`|10.3666845|7.875000|
|`uav-p4-76-campaign-002-008-r1-n1-u0-queue-full`|1|satisfied|`3818bec4871dc7de0d63514ca87ad26065f0abecee33e8cb6f45d999ddd09e55`|8.9701017|6.406250|
|`uav-p4-76-campaign-002-014-r1-n2-joint-backlog`|2|satisfied|`eef1fd0aa322d66e7142f4a04573aadb213b02b62eb0a5d3630572a0b98d5cfc`|9.2488728|8.140625|
|`uav-p4-76-campaign-002-024-r1-n3-joint-backlog`|3|satisfied|`08c11b52543f7ce4217ecdddaa73b5a7b30bee3c702aaf9977f976c81781704d`|27.7991571|25.875000|
|`uav-p4-76-campaign-002-044-r2-n1-joint-backlog`|1|satisfied|`706bd493fef18a2de31be212156825af913ef21adde7d15cda47dc1bc1825afe`|3.2409179|2.296875|
|`uav-p4-76-campaign-002-045-r2-n1-u0-queue-safety`|1|violated|`48989eef927665697ce2687c5eccfcd99da2a9e46b97640003421fd620ca3291`|17.3299242|10.359375|
|`uav-p4-76-campaign-002-046-r2-n1-family-queue-safety`|1|violated|`c820090fc19ffc80284d62194b40f62396cdeedc10fc1db0d853f4293b64656e`|14.4998189|9.296875|
|`uav-p4-76-campaign-002-047-r2-n1-u0-queue-full`|1|satisfied|`3818bec4871dc7de0d63514ca87ad26065f0abecee33e8cb6f45d999ddd09e55`|12.4672218|7.406250|
|`uav-p4-76-campaign-002-053-r2-n2-joint-backlog`|2|satisfied|`eef1fd0aa322d66e7142f4a04573aadb213b02b62eb0a5d3630572a0b98d5cfc`|15.3348126|10.484375|
|`uav-p4-76-campaign-002-063-r2-n3-joint-backlog`|3|satisfied|`08c11b52543f7ce4217ecdddaa73b5a7b30bee3c702aaf9977f976c81781704d`|58.9681631|37.828125|
|`uav-p4-76-campaign-002-083-r3-n1-joint-backlog`|1|satisfied|`706bd493fef18a2de31be212156825af913ef21adde7d15cda47dc1bc1825afe`|2.7920825|2.125000|
|`uav-p4-76-campaign-002-084-r3-n1-u0-queue-safety`|1|violated|`48989eef927665697ce2687c5eccfcd99da2a9e46b97640003421fd620ca3291`|12.7388912|8.953125|
|`uav-p4-76-campaign-002-085-r3-n1-family-queue-safety`|1|violated|`c820090fc19ffc80284d62194b40f62396cdeedc10fc1db0d853f4293b64656e`|13.1977209|8.687500|
|`uav-p4-76-campaign-002-086-r3-n1-u0-queue-full`|1|satisfied|`3818bec4871dc7de0d63514ca87ad26065f0abecee33e8cb6f45d999ddd09e55`|14.3833584|8.687500|
|`uav-p4-76-campaign-002-092-r3-n2-joint-backlog`|2|satisfied|`eef1fd0aa322d66e7142f4a04573aadb213b02b62eb0a5d3630572a0b98d5cfc`|18.8037164|12.359375|
|`uav-p4-76-campaign-002-102-r3-n3-joint-backlog`|3|satisfied|`08c11b52543f7ce4217ecdddaa73b5a7b30bee3c702aaf9977f976c81781704d`|43.5034780|31.578125|

### All eleven new-model attempts

All rows: status `timeout`, verdict `null`, new model SHA256 above. Source: `evidence/verification/uav-service-completion-p3-20261002/results.json`.

|run_id|Query SHA256|Wall s|CPU s|Sampled RSS MiB|
|---|---|---:|---:|---:|
|`issue87-01-admitted-attempt01-20261002`|`40794bff7b5afc7a2e8de7a3a353826c409b5396d6441fa5541c4aaff7fbb106`|601.0388965|590.765625|976.828125|
|`issue87-02-measurement-attempt01-20261002`|`ceaf3bf6ea788bd8679e801c9238b2f634c6d45445ccc8be2a28db175176f409`|600.6039708|587.718750|965.285156|
|`issue87-03-enqueue-attempt01-20261002`|`f53c1a24aff330214fd481f8d733f655b6fadc0ee1cd511f99e6a1ed6a0e1157`|600.9599769|588.015625|970.539062|
|`issue87-04-attempt-attempt01-20261002`|`738df1dd189ee021898ecf777b3e1f03cfc5f59e82f116556fe6f8cff59840d2`|601.0337728|588.203125|958.429688|
|`issue87-05-success-attempt01-20261002`|`745ab5968a673463fac5e014c7d7f192d4ed9d43ad5e193e1b7736af6d44541b`|600.7920977|587.562500|971.558594|
|`issue87-06-loss-attempt01-20261002`|`cc7fcd3791741da3b6df29a6e91cad409773a16d6424a4d85aceaa33cd5a618f`|600.6074797|589.625000|977.210938|
|`issue87-07-timeout-attempt01-20261002`|`139271712e0e0144bcf7471257bf9e99d9e7f2779a20006bcfe1e6803a5798d9`|600.4676331|591.187500|982.273438|
|`issue87-08-cancel-attempt01-20261002`|`5265ffc294528d7bc18db8a8146ac3a53cd38a8951e17c9a3d83ced30d4c2298`|600.4278674|586.343750|966.671875|
|`issue87-09-deadline-equality-attempt01-20261002`|`0e613481a75b4f41db6e5c1a8bb103b28e169f0ee069b5b5fe431a87cffedcb4`|600.1930379|554.062500|863.457031|
|`issue87-10-completion-safety-attempt01-20261002`|`f3cfb3800063b21045d94625f616950944663fcba61956a3498aba62ca32edf9`|600.5930649|571.390625|899.675781|
|`issue87-11-deadlock-attempt01-20261002`|`a53c752ecabf84d28dc0ea1567c0589ffb632777a5ad7178f70be0d2d99e5334`|600.7600478|577.703125|509.851562|

### Historical/new verifier banner

The native full banner is preserved verbatim in each P3 row; the machine-readable first line is the shared version above. This appendix omits repeated copyright/build/license lines for readability, rather than replacing their underlying records. P4 uses its preserved version capture; replay uses the separate Engine.getVersion string in the prose.
