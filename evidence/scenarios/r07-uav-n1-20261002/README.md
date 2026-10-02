# R07 UAV N=1 candidate — APP rejection and recorded SLA violation

**A complete cross-layer failure path reaches an APP outcome.** The real UPPAAL
engine generated 63 transitions ending in `A_REQ.Rejected` and `A_SLA.SLAReported`;
an independent replay accepted all 63 from the initial state. Both negative
controls reject state 63. Successful service completion is not claimed.

| Run ID (prefix `r07-80-20261002-`) | Method | Status | Accepted transitions |
|---|---|---|---:|
| sim001 | directed symbolic simulation | goal_reached | 63 |
| replay001 | independent symbolic replay | replay_complete | 63 |
| negative-discrete001 | wrong final APP admission value | rejected: discrete_state_mismatch | 62 |
| negative-clock001 | impossible final SLA clock | rejected: clock_zone_disjoint | 62 |

All cells use `property_verdict=null`, `query_hash=null`. Native execution including
probes/cleanup totals 27.88949 seconds against the 600-second campaign cap.
Each cell completed below 60 seconds and below the sampled 2 GiB owned-tree
threshold; native process termination is recorded. This is feasibility evidence,
not a model-checking verdict. Actual version in every result:
`UPPAAL version 5.0.0 (rev. 714BA9DB36F49691), June 2023 -- server`.

## Scientific meaning

At time 1 APP forwards its single strict safety-critical UAV request. At time 5
PHY supplies `PD_FAILED=2`, consistent `MISS_CRITICAL=2` and sensing degradation.
The KPI boundary maps and fans out telemetry to MAC/SDN/APP. MAC consumes it
and selects JOINT; SDN proposes degraded sensing-boost admission; the APP safety
guard converts that proposal to rejection. APP records the SLA violation report
at the same time. Reachable suffix DBMs consistently fix time 5; the pre-report
elapsed clock is 0, within the abstract response deadline 3. Request-to-rejection
elapsed time is 4, within admission bound 15. These are observations on this
path. The response deadline concerns reporting an SLA failure, not providing
successful service. Marginal intervals in earlier table rows are not independent
chosen timestamps; full inter-clock constraints remain in the retained DBMs.

`SEMANTICS.md` identifies the code/guards and the correlation available in the
single service context. No explicit packets or request IDs connect queue service
to APP completion. `service_complete` comes from an environment timer/termination
event, not a delivered item. The exact path also exposes the existing mismatch
between sensing location `FreshnessLimited` and `SensingState=7`; no model edit
was made. The rejection follows failed KPI classes and the explicit safety rule.
The SDN pending decision reads mapped global telemetry; it does not receive the
second KPI notification while already in Evaluate. SDN's monitor receives it.
APP's request automaton ignores the KPI broadcast while pending; its SLA
automaton consumes the subsequent guarded violation notification.

## Inputs, ownership and acceptance

- Issue #80; P5 draft; atomic ID R07; owner/account-id vadimnbkg.
- Base ref origin/read; base commit 91113a1b634f030c7e895f54f5c36a0b140d66eb.
- Branch codex/vadimnbkg/80-r07-service-trace; target read.
- Baseline explicitly audited as candidate: uav-family-r1-20260929.
- Model SHA256: 5234cb087e5274798926d516dedc77d1f9542ea7df59cec39f83859771ce1385.
- Manifest SHA256: 5480bef5b00020735259f10eb43bdd9bc79ebc364a3bbcacad34c78fd0552cbf.
- Parameters/instance vector and complete per-run provenance: results.json.
- Sole write scope: evidence/scenarios/r07-uav-n1-20261002/**.

User explicitly instructed running the scoped prompt; this authorizes candidate
simulation, not final P5 acceptance. Limited P1/P2 applicability and v2 decisions
were read from GitHub and saved in decisions.json. The published read base was
fetched over public HTTPS and PR #79 merge was confirmed. Final P5 acceptance
still needs P5-applicable Gate 1, accepted P3 core evidence and a matching accepted
verification run. Reviewer artmus208 remains proposed until independently
confirmed. Neither R07 nor Issue #80 is closed by the author.

## Artifacts and reproduction

`scenario-for-paper.md` and `response-R07-draft.md` are English integration drafts.
`scenario-events.md` selects 20 milestones; `scenario-events.csv` covers all 63
steps with synchronized processes, channels, changed values/locations and trace
references. `model-map.json` maps all 50 processes/edges. `spine.tsv` is the executed
bounded selection schedule; it chooses successors without changing the XML.
`PROTOCOL.md` records budgets, target, stop/cleanup policy and interpretation.

Read-only audit, with Python standard library and no engine launch:

```sh
python3 -B evidence/scenarios/r07-uav-n1-20261002/audit.py
python3 -B -m unittest discover -s evidence/scenarios/r07-uav-n1-20261002 -p 'test_*.py' -v
```

Raw XTRs are losslessly stored as .xz, per-step logs and Windows raw text as .gz.
Native JSON has an LF-normalized inspection copy plus the original .json.gz.
lossless-archive.json records packed and original hashes/sizes; audit checks both.
Decompress with Python lzma/gzip to inspect/import XTRs. The simulator XTR was
generated by UPPAAL API transitions; replay XTRs retain reachable intersections.
No manually invented final state is used. External binary hashes are checked by
the audit when those installed paths exist; absent binaries do not prevent
read-only archive auditing.

Native reproduction needs a separately agreed output/run ID and Windows
UPPAAL 5.0.0/JDK17. Restore execution source checkpoint `239ae70` from the full
handoff bundle in an isolated checkout to start before the retained campaigns.
Build using `python3 -B evidence/scenarios/r07-uav-n1-20261002/run.py --build`,
save build logs in a clean reproduction checkpoint, then use the recorded commands:

```sh
python3 -B evidence/scenarios/r07-uav-n1-20261002/run.py --cell simulate --name sim001 --input evidence/scenarios/r07-uav-n1-20261002/spine.tsv
python3 -B evidence/scenarios/r07-uav-n1-20261002/run.py --cell replay --name replay001 --input evidence/scenarios/r07-uav-n1-20261002/runs/sim001/trace.xtr
python3 -B evidence/scenarios/r07-uav-n1-20261002/run.py --cell negative-discrete --name negative-discrete001 --input evidence/scenarios/r07-uav-n1-20261002/runs/sim001/trace.xtr
python3 -B evidence/scenarios/r07-uav-n1-20261002/run.py --cell negative-clock --name negative-clock001 --input evidence/scenarios/r07-uav-n1-20261002/runs/sim001/trace.xtr
```

Checkpoint each cell before the next. Existing output directories are immutable:
the retained latest checkout is for auditing, not overwriting runs. Commands,
source commits, binary hashes, environment and hardware are in per-cell provenance.
The original compile sandbox interop failure is disclosed in build-attempts.md;
its raw stderr was overwritten before preservation, so only the observed tool
output transcription remains. The authorized native build and all four engine
cells succeeded. Repository and package check details are in checks/ and HANDOFF.md.
