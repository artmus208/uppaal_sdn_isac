# Evidence index for the MoNoTeC-2026 integration draft

This map accompanies `levels_tex/samplepaper.tex` and its matching PDF/DOCX. All
paths below are relative to the repository root. It describes saved artifacts,
not new experiments. Source review: `evidence/integration/20261003-submission/checks/evidence-review.md`;
its tuple appendix retains the longer per-run numerical tables. Live decision
projections are preserved in the adjacent `checks/evidence-github-snapshot.json`.
The manuscript's stable LaTeX labels identify locations without depending on PDF pagination.

## Availability, checking, acceptance and inclusion

These are four separate statuses: **available** means persisted artifacts exist;
**technically checked** means the specific source/hash/result/trace inspection is
recorded; **accepted** requires an applicable scientific decision; **included**
means the draft reports the evidence with its limitations. An artifact's old
`accepted` field, a merge, an agent review and a positive verdict are not interchangeable.

| Evidence | Available / technically checked | Scientific acceptance | Included in this draft |
|---|---|---|---|
| Historical H core | XML, query results, raw counterexamples and proof documents; agent source/tuple inspection recorded | Qualified C01-C05 disposition in [#39](https://github.com/artmus208/uppaal_sdn_isac/issues/39#issuecomment-5834333757); excludes C06/Gate 2 and does not automatically accept every later registry revision | Historical negative queue result, reachability and qualified MAC argument; `tab:evidence` |
| F finite P4 campaign | All 90 scientific records and native raw monitoring/output retained; aggregates checked | PR #77 merged; no separate scientific acceptance found; full R03/R04/C06 remain open | Measured finite outcomes/costs only; `tab:scalability` |
| S model and successful execution | Exact XML, simulator trace and separate engine replay retained; causal IDs/times checked | [#84 A/B](https://github.com/artmus208/uppaal_sdn_isac/issues/84#issuecomment-5946722646) and [activation C](https://github.com/artmus208/uppaal_sdn_isac/issues/84#issuecomment-5947256320) accept scoped P1/P2/input Gate 1, not P3 guarantees or R07 closure | Composition, parameters and one successful causal execution; `tab:composition`, `tab:parameters`, `tab:scenario` |
| S eleven-query campaign | Eleven timeout records/raw files and budget deviation retained; aggregates checked | PR #88 merged at `452571598d4a5c1e070dace3a918ea737904e239`; scientific budget/coverage acceptance is absent | All eleven timeout/null; no universal verdict; `tab:evidence` |
| F1 rejection scenario | 63-transition simulation/replay and negative controls retained; causal interpretation checked | R07 candidate; no accepted end-to-end verification run attached | One rejection/violation-report example, not successful service |
| #89 six-slot proposal | Exact published preparation and an agent technical review; zero attempts | User authorized one bounded attempt, but exact runner is technically blocked; no result or scientific acceptance | Unexecuted follow-up and its limitation only |

Checks are agent technical/source checks, not external peer review. Parameter
values remain abstract engineering choices without physical calibration.

## Exact model identities

| Key | Processes | XML SHA256 | Persisted XML |
|---|---:|---|---|
| H | 50 | `592678ed678ce8f70cf278f542e48bd2bb739969b53a962423d3e63f91e3e1e2` | `evidence/governance/20260906-baseline/gate1-20260923/model.xml` |
| F1 | 50 | `5234cb087e5274798926d516dedc77d1f9542ea7df59cec39f83859771ce1385` | `evidence/scalability/family-series-68/generated/n1/model.xml` |
| F2 | 99 | `e7ac599140b7beeb94acdf0e3535a727c2eccc40aa15314afa3371eb09700208` | `evidence/scalability/family-series-68/generated/n2/model.xml` |
| F3 | 148 | `aa1c0ecf1a0e8846421ebff91ac19ffc1645724d4309a38c568edbf23273ce90` | `evidence/scalability/family-series-68/generated/n3/model.xml` |
| F4 | 197 | `e8a4cdb0a4ea795ca2c90a0dfdee8cff7b9fbc3093369fa8141d61750a28033a` | `evidence/scalability/family-series-68/generated/n4/model.xml` |
| S | 51 | `b8ab50e112b71491f8242789cc7906497baf8440c473d7a5a4d5214840187e02` | `evidence/instantiation/uav-service-completion-candidate/model.xml` |

H, F1 and S are different models. F2-F4 also have distinct XML/query hashes; no
historical verdict is transferred to S. The governing manifests are
`manifests/baselines/reviewer-r1.yaml`, `uav-family-r1.yaml` and
`uav-service-completion-r1.yaml` in that same directory. S's scientific input
commit is `61386aa358805082b705dcd00c8cbfde5fb98248`.

## H: queue and MAC response

Exact record selector: `evidence/verification/p3-20260926-core-acceptance/accepted-runs.json` -> `accepted_runs[]` -> `run_id` below.
Every row uses model H and actual verifyta `UPPAAL 5.0.0 (rev. 714BA9DB36F49691), June 2023`;
complete captured banners, commands and resources remain in the source records.

| Run ID | Exact formula | Status/verdict | Query SHA256 |
|---|---|---|---|
| `p3-20260923-003-02-C01-queue` | `A[] !mac_queue_overflow_seen` | `success/violated` | `694501c262583dfe43e22a907f10080795fd63b8bc534a11cd9338c84a704051` |
| `p3-20260923-003-06-queue-full` | `E<> mac_queue_q == mac_queue_K && !mac_queue_overflow_seen` | `success/satisfied` | `132fb1f5ffd023f31064a089113bf1300f99fe75ce78394fb796d2873d67e6e6` |
| `p3-20260923-003-14-ack-unconditional-completion` | `mac_obs_ack_active --> !mac_obs_ack_active` | `success/violated` | `3f406107b55e4e196c2416c16e0573e3b362e2ff0396ab3ac696b183e252d249` |

Metadata for these rows:
`evidence/verification/p3-20260923/p3-20260923-003/{results.json,run.json,run.yaml}`.
Raw archive: `evidence/verification/runs/p3-20260923-003.tar.xz`, whose member root
is `p3-20260923-003/`. Essential members include each selected stem's `.q`,
`.stdout.txt`, `.stderr.txt`, `.native.json`, and `02-C01-queue-trace1.xml`.
The registry's `trace_paths` names the other exact trace members. The queue row
has runtime 19.4386224 s and peak 182.917969 MiB; queue-full has 17.2232517 s.
`evidence/verification/p3-20260926-dispositions/audit.json` supplies the inspected
five arrivals without service, q=0..5/K=4 and four control ACKs that do not dequeue.
This is a violated non-overflow property under the allowed environment.

The three-unit MAC claim additionally needs
`evidence/verification/p3-20260925-c02-audit/{README.md,premises.json}` and
`evidence/verification/p3-20260924-c02-reduced/{README.md,source-audit.json,model.xml,C02.q}`.
It is an ACK-or-timeout argument on time-divergent executions, not unconditional
ACK delivery or a completed full-H universal verdict. Reduced model SHA256:
`536233940526a1716006d6769c84c9faf6dc3d7bf0e6ffa0981aa60b56a49241`.
In `evidence/verification/p3-20260924-c02-reduced/runs/p3-20260924-c02-reduced-001/results.json`, run
`p3-20260924-c02-reduced-001-C02` is `success/satisfied`, query SHA256
`cec919bc6e2d960160976799d3d52ff4f25eea9f136f7b0231c02cec13f162db`.
The same query on the negative-control model
`b474572cb0ceb80d821fb08ea74954569324ddfcb8dacfdfc10a1b9eea885fd6`
is `success/violated` under suffix `-negative-control`. Suffixes `-active` and
`-deadline` are separate positive reduced-model reachability results. Their raw
memory zeros mean no sample before exit; citable memory is null. The distinct
per-episode recovery proof is in `evidence/verification/p3-20260925-c01-structure/README.md`;
it is not a machine result or a proof of successful recovery.

## F: all 90 scientific P4 attempts

Primary registry: `evidence/scalability/runs/uav-family-p4-20260929/campaign-002/runs.json`.
Select exactly rows with `phase == "model-checking"` (not generation or load/parse).
Each row stores `run_id`, `query_id`, `formula`, `query_hash`, `model_path`,
`model_hash`, `status`, `property_verdict`, `tool_version` and native resources.
All scientific rows use actual verifyta 5.0.0 revision 714BA9DB36F49691; execution
source commit is `877fa69a29e1732db2b4047eebdd99591b185c77`.

| N / model F_N | Attempts | success/satisfied | success/violated | timeout/null |
|---:|---:|---:|---:|---:|
| 1 | 18 | 6 | 6 | 6 |
| 2 | 21 | 3 | 0 | 18 |
| 3 | 24 | 3 | 0 | 21 |
| 4 | 27 | 0 | 0 | 27 |

Concrete anchor: `uav-p4-76-campaign-002-005-r1-n1-joint-backlog`, formula
`E<> u0_mac_queue_q > 0`, F1, `success/satisfied`, query SHA256
`706bd493fef18a2de31be212156825af913ef21adde7d15cda47dc1bc1825afe`.
Raw directory is `evidence/scalability/runs/uav-family-p4-20260929/campaign-002/005-r1-n1-joint-backlog/`.
For every other row, use its `cell_id` under the same campaign root and follow
`stdout.reference`, `stderr.reference`, `trace.files[].reference`,
`monitor_reference` and `memory_samples_reference`; these references are relative
to `evidence/scalability/runs/uav-family-p4-20260929/`. Query/model paths in each row are relative to the repository.
Some raw streams/traces are gzip-compressed: validate storage SHA256 first,
then decompress for the original-byte SHA256. Do not reinterpret a timeout's
partial stdout as a completed verdict.

`query-observations.csv`, `SUMMARY.json` and `RESULTS.md` in that P4 root derive
the completed-query medians, 231.23 MiB observed maximum and 0.618 s sampling gap.
All 30 per-UAV service attempts are timeout/null. There are 117 completed phases
in total, including 27 non-scientific generation/compile/load phases. Different
query counts per N, censored attempts and one native host do not establish a
general cutoff, required completion memory, service guarantee or physical scale.

Read-only audit, requiring only the selected persisted evidence and Python:

```sh
python -B evidence/scalability/runs/uav-family-p4-20260929/audit_evidence.py --root .
```

This audit checks archived evidence; it does not invoke verifyta.

## S: one successful simulation and independent engine replay

Registry: `evidence/instantiation/uav-service-completion-candidate/results.json` -> `runs[]`.

| Run ID | Exact result path under the candidate root | Status | query_hash / property_verdict |
|---|---|---|---|
| `uav-completion-82-20261002-simulate-006` | `runs/simulate-006/result.json` | `goal_reached` | null / null |
| `uav-completion-82-20261002-replay-001` | `runs/replay-001/result.json` | `replay_complete` | null / null |

Both use model S and actual Engine banner
`UPPAAL version 5.0.0 (rev. 714BA9DB36F49691), June 2023 -- server` (full banner
in each record). Simulation source is `cd40b5107b201b97b0dc31432cf9cf9f25e8f5d8`;
replay source is `f6adba0aee8e037557020009fc43591d732f053d`.
`raw-traces.zip` retains the large raw members; do not omit it from a source bundle.
`raw-index.json` maps each member to its SHA256. Replay input is ZIP member
`runs/simulate-006/trace.xtr`, SHA256
`7ef37b0e6abc77eace7aa270ce3aea6a35d10724cb662508e1f54104123ddfaf`.
The simulator/replay `steps.jsonl` members retain full vectors, edge selections
and clock zones; `source-snapshots.zip` preserves the producer's exact sources.

`completion-record.json` and `replay-steps.csv` establish states
4/62/84/85/96/99/100 (send/admit/sample/enqueue/service/attempt/receipt), 100
transitions and 101 states. At receipt: request age 14, global time 15, sample
age in [4,5), and correlated request/sample IDs 1. `contract.md`, `parameters.json`
and the exact S XML define acquisition duration 5, a one-unit transport stage
from actual transmission attempt, service age bound 40 and strict freshness <5.
There is no finite dispatch-to-attempt bound supplied by that transport clock.
These are one feasible execution plus replay, not exhaustive property verdicts.
The distinct 243-quality-tuple regression is `test_candidate.py::CandidateTests.test_every_stored_quality_combination`,
with saved outcome in `checks/regression-final.txt` under the candidate root.
It tests a finite guard/software oracle, not 243 reachable states or native queries.

## S: all eleven exhaustive attempts remain inconclusive

Registry: `evidence/verification/uav-service-completion-p3-20261002/results.json` -> `queries[]` -> `run_id` below.
Every row has model S, `status=timeout`, `verdict=null`, actual verifyta 5.0.0
revision 714BA9DB36F49691. Each row preserves exact `formula` and query hash.

| Run ID | Query ID | Query SHA256 |
|---|---|---|
| `issue87-01-admitted-attempt01-20261002` | `admitted` | `40794bff7b5afc7a2e8de7a3a353826c409b5396d6441fa5541c4aaff7fbb106` |
| `issue87-02-measurement-attempt01-20261002` | `measurement` | `ceaf3bf6ea788bd8679e801c9238b2f634c6d45445ccc8be2a28db175176f409` |
| `issue87-03-enqueue-attempt01-20261002` | `enqueue` | `f53c1a24aff330214fd481f8d733f655b6fadc0ee1cd511f99e6a1ed6a0e1157` |
| `issue87-04-attempt-attempt01-20261002` | `attempt` | `738df1dd189ee021898ecf777b3e1f03cfc5f59e82f116556fe6f8cff59840d2` |
| `issue87-05-success-attempt01-20261002` | `success` | `745ab5968a673463fac5e014c7d7f192d4ed9d43ad5e193e1b7736af6d44541b` |
| `issue87-06-loss-attempt01-20261002` | `loss` | `cc7fcd3791741da3b6df29a6e91cad409773a16d6424a4d85aceaa33cd5a618f` |
| `issue87-07-timeout-attempt01-20261002` | `timeout` | `139271712e0e0144bcf7471257bf9e99d9e7f2779a20006bcfe1e6803a5798d9` |
| `issue87-08-cancel-attempt01-20261002` | `cancel` | `5265ffc294528d7bc18db8a8146ac3a53cd38a8951e17c9a3d83ced30d4c2298` |
| `issue87-09-deadline-equality-attempt01-20261002` | `deadline-equality` | `0e613481a75b4f41db6e5c1a8bb103b28e169f0ee069b5b5fe431a87cffedcb4` |
| `issue87-10-completion-safety-attempt01-20261002` | `completion-safety` | `f3cfb3800063b21045d94625f616950944663fcba61956a3498aba62ca32edf9` |
| `issue87-11-deadlock-attempt01-20261002` | `deadlock` | `a53c752ecabf84d28dc0ea1567c0589ffb632777a5ad7178f70be0d2d99e5334` |

Raw root for each row: `evidence/verification/uav-service-completion-p3-20261002/runs/<run_id>/`.
`raw_files[]` names every persisted file relative to that campaign root and its
SHA256; `manager_attempt_id` identifies the `attempts/<id>/result.json`,
stdout/stderr and telemetry. All eleven run directories are included in the
selection. `budget-stop-failure.json`, `environment.json`, `query-ledger.json`
and `report.md` preserve the declared 6600 s versus measured 6607.4778455 s,
guard failure and manual stop. No false/satisfied verdict follows from these
outcomes. PR #88's merge did not dispose of the scientific coverage/budget gap.

## F1: distinct rejection/violation-report scenario

Registry `evidence/scenarios/r07-uav-n1-20261002/results.json` and run results
`runs/sim001/result.json` / `runs/replay001/result.json` identify
`r07-80-20261002-sim001` (`goal_reached`) and
`r07-80-20261002-replay001` (`replay_complete`), both model F1, null query hash and
null property verdict. The package contains 63 transitions, request at global
1, failed sensing inputs/rejection at 5 and violation-to-report latency 0.
`scenario-events.csv`, `scenario-for-paper.md`, `SEMANTICS.md` and retained raw
run members support that interpretation. `lossless-archive.json` maps the
compressed negative-clock control stream. This F1 episode is not the S
successful-result experiment and does not close R07.

## #89: exact unused preparation and technical blocker

Published preparation commit `77c0431049e4b5d367d56e1eb5232ed2d330258e`,
[PR #90](https://github.com/artmus208/uppaal_sdn_isac/pull/90), contains
`evidence/verification/uav-bounded-response-89/{PROTOCOL.md,RUNNER.md,config.json,seal.json,query-inventory.json,query-ledger.json,driver.py}`.
This tree is absent from the integration base and is a separately pinned bundle
input. `query-inventory.json` contains all six exact formulas/hashes; ledger run
IDs `uav-br89-q1-001` through `uav-br89-q6-001` are planned, unconsumed,
`not_executed/null`. Q1-Q5 use prospective Hnom SHA256
`3d29abc8a19aa743fa5e83bde7c83e3c45de36f166ea2b74315443156b073e03`;
Q6 uses original S. Hnom was not materialized. Caps remain
180/180/180/600/180/180 s, 1500 search and 1800 session seconds, one verifier/no retry.

`checks/protocol-review.md` records the reproduced blocker: sealed `driver.py`
requires both approver/runner `artmus208`, hardcodes that branch and producer,
and rejects truthful `vadimnbkg` at line 91. No signature, identity, seal or
checkpoint was substituted. The existing direct user authorization supersedes
old manual-approval wording; the refusal is technical incompatibility of that
exact runner. Zero verifier preflight/query slots were used during this review.
Hnom is an external-input diagnostic restriction, not a sufficient reliability
contract or a frozen/verified baseline.

## Source-bundle selection and reproduction boundary

`sources/evidence-bundle-paths.json` provides exact repository-relative file paths,
groups and total byte count. Copy `paths` unchanged with their directory layout.
`pinned_git_inputs` must be read from its exact commit (or the clean `runner-89`
clone at that commit), never from an unrelated branch. Preserve ZIP/XZ/GZ bytes.
The selection supports checking the paper's saved outcomes, hashes, causal
traces and P4 numerical aggregation; it is not the entire repository history.
The lead packager should additionally include the final TeX/style/bibliography,
figure sources/assets, reviewer response and this index. Build tools, binaries,
virtual environments, caches and intermediate rendering trees are excluded.

Literature claims retain their primary citations in the final bibliography and
`checks/literature-review.md`. The Glonina comparison uses the 2020 dissertation,
printed pp. 23-25, 63-67 and 79-86; the local source is `pdfs/dissertation.pdf`,
SHA256 `4f8a778c52ff1e6b33383d447ebc13e91b8d18ce8161996d79d86dc32d0f5de6`.
Third-party full papers are not copied into this minimal execution-evidence selection.

No bundled command authorizes fresh model checking. Rerunning native verification
or engine replay needs a separately available licensed UPPAAL installation and
an applicable experiment authorization. Historical registries may reference
unselected runs beyond the manuscript's claims; retrieve their exact canonical
commit if that larger historical audit is desired. The full #39 registry is
retained as provenance, not as a claim that every listed later row was accepted.
