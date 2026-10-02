# UAV APP-completion baseline proposal — Issue #84

Status: **ready for independent decision; Gate 1 and activation pending**.
This package proposes `uav-service-completion-r1-20261002`: only UAV N=1,
full 51-process composition, one request and one corresponding sensing result.
It fixes an object of study; it proves no universal property.

Assignment and scope: [Issue #84](https://github.com/artmus208/uppaal_sdn_isac/issues/84).
Base/input commit: `61386aa358805082b705dcd00c8cbfde5fb98248`, `origin/read`.
Accepted candidate publication: `fdbfd5619385eae31101dcfc285010b96cc85b45`;
[PR #83](https://github.com/artmus208/uppaal_sdn_isac/pull/83) independently approved
by artmus208 and merged as `07e45268bbfbb4c1293e4e4f4227792794583509`.
The Git subtree is byte-identical at publication, merge and this input commit.
Approval/merge accepts the candidate; the new P1/P2 applicability and Gate 1
remain separate decisions. `github-snapshot.json` records the observed assignment,
review and historical decisions; it is a captured snapshot, not live task state.

## Reviewable inputs

- `proposed-baseline.yaml`: single-model manifest in JSON-compatible YAML; proposed,
  not frozen or activated. Hardware and execution source commits remain per-run.
- `input-hashes.json`: 192 exact Git-blob SHA256 pins, including accepted artifacts,
  archives, generation inputs, historical lineage, protected pointer and generator pins.
- `parameter-inventory.json`: inherited parameter set, new contract choices and every
  emitted global/template constant declaration; historical T_complete is inactive.
- `instance-inventory.json`: full vector, constructor arguments and all 51 ordered bindings.
- `query-inventory.json`: exact formulas/files/hashes for all eleven queries. All selected
  only as a proposal and all verdicts null. Selected-set hash is explicitly constructed
  from the sorted path/hash dictionary. Old run `query_pack_hash` hashes inventory.json,
  which is a different object; it is not a query execution hash.
- `decision-pins.json`: concrete hashes for the independent decision record.
- `machine-evidence-inventory.json`: every candidate native cell and its own source/model
  identity, command, version, resource and raw/source archive references. Earlier changed
  models are marked diagnostic-only. No accepted verification run is registered.
- `proposed-operational.patch`: adds the one-model manifest and appends explicit P3/P5
  selection policy. It is checked for applicability without touching operational files.
- `proposed-integrator-decision.md`: separate A/B/C/D dispositions and post-merge template.

## Scientific contract and limits

Actual APP service_request emission starts `c82_service_age` and request ID 1.
Admission, job, sensing sample, transmitted payload and APP receipt bind to that ID.
PHY first reaches sensing readiness, then performs a five-unit acquisition; the
actual matching measurement event creates the sample and resets its age. Stored
Pd/false-alarm/missed-detection/accuracy/coverage values remain the sensing result;
later global KPI values cannot replace them. The result enters the numerical queue
as a FIFO token; only an eligible COMM/JOINT MAC service reaching rank 1 dispatches
it. Grant/command ACK is distinct from result delivery. Transmission can lose it.
Completed requires actual APP receipt of the admitted matching fresh result,
strict stored quality, request age **<=40** and sample age **<5**. Admission failure,
sensing/queue/transport failure, timeout and cancellation do not set success.
Receipt flags/bands are immutable retrospective records, so later terminal clock
advance does not invalidate a past timely receipt.

At sample age=5 strict freshness already fails. Sample-age classes are [0,5),
[5,10), [10,infinity). Request age=40 permits the contract's receipt/timeout
alternatives; their global reachability is still an unexecuted diagnostic query.
One request/result with bounded identities/no reuse, fixed acquisition duration=5,
FIFO rank abstraction with K=4 and absorbing overflow, optional one service per
five-unit epoch, one lossy transmission bounded by D_bus=1/no retry are assumptions.
Update class uses sample-age bands, not a measured inter-sample period. Time units
and quality classes have no physical calibration. No fairness assumption is added.

The static audit found no new contradiction between the accepted emitted model
and its stated contract. This does not establish global deadlock freedom or all
boundary scenarios. Inherited observer/report and timing abstractions, age-based
update mapping, warning/termination policy and abstract acquisition/transport
require explicit P1/P2 disposition; they cannot silently become calibrated claims
or whole-system equivalence. The acquisition stores current PHY abstract classes
at its completion event; it does not model a physical sensor waveform or measured
quality distribution. See the unchanged candidate `contract.md` and `changes.json`.

## Evidence boundary and historical correspondence

Healthy `simulate-006`: goal_reached, 100 transitions. Independent `replay-001`:
replay_complete, 100 transitions/101 states. Two negative engine replay controls
were rejected. Healthy receipt has request age=14 and sample age=[4,5), global
age=15; exact DBM bounds are in candidate `completion-record.json`. Both healthy
runs use the proposed model hash, but their actual execution checkpoints differ.
Every run has query_hash=null and property_verdict=null. All eleven exhaustive
query verdicts remain open, including completion safety and deadlock freedom.
The healthy path is feasible engine simulation/replay, not universal SLA,
completion, fairness or liveness verification.

Historical reviewer-r1 remains selected by current.json. The finite uav-family-r1
supplies the exact 50-process N=1 source XML, vector and inherited parameters;
its compiler/production sources are lineage, not live inputs of this transformer.
Limited P1/P2 applicability in PR73 and P4 activation in PR75 are restricted to
that historical family. The candidate changes four templates and adds ResultJob;
other original templates/instances are structurally preserved, not proved equivalent.
Prior P3/P4 results retain their exact prior configuration. PR81 is an APP rejection
trace on the old 50-process XML and is excluded from this model's evidence registry.
It is used only as a negative cross-baseline attribution control.
Candidate preparation base `91113a1b634f030c7e895f54f5c36a0b140d66eb`, per-run archived
execution checkpoints, publication HEAD and governance input commit are distinct.
Source ZIP contains hash-auditable checkpoint commit objects and selected input blobs;
it is not a complete Git history. Original candidate HANDOFF points to its full
owner-side bundle if execution history restoration is needed.

## Reproduction

Run from the repository root with Python >=3.10; proposal audit needs stdlib only:

```bash
python3 -B evidence/instantiation/uav-service-completion-candidate/generate.py --check
python3 -B evidence/instantiation/uav-service-completion-candidate/audit.py
python3 -B evidence/governance/uav-service-completion-baseline-20261002/check.py --source-history
python3 -B -m unittest discover -s evidence/governance/uav-service-completion-baseline-20261002 -p 'test_*.py' -v
```

For --source-history, restore the original execution ref from the full governance
bundle or candidate bundle (see HANDOFF.md). This mode additionally checks every
archived input against its actual execution Git tree, rather than archive identity
alone. The governance bundle includes that execution history.

`prepare.py` derives only proposal files from immutable inputs. `check.py` checks
exact hashes/Git publication equality, generation, parameters/constants, constructor
order, query dispositions, all raw/source archives, per-cell model/generator/source
hashes, original execution identity, raw engine version responses, patch applicability,
historical pointer and absence of unsupported acceptance claims. Negative controls
change real parameters/vector/query, model hash, pointer, run identity and Gate flags.
Commands, exit codes and environment limits are preserved in `checks/` and
`check-results.json`. All checks here are **static validation**. No new UPPAAL run,
license probe, scenario or scientific verdict was requested or produced.

## Operational disposition

Only `evidence/governance/uav-service-completion-baseline-20261002/**` is active.
Integrator must separately decide A: changed-composition P1/P2 applicability;
B: exact input freeze/Gate 1 and eleven-query selection; authorize the proposed
manifest-specific scope; then C: operational activation after independently accepted
operational PR merges into read, recording actual merge SHA and decision UTC time.
D keeps exhaustive claims open. P3/P5 must explicitly pin baseline ID, manifest hash,
input commit and activation record. Selection does not authorize engine execution,
transfer old verdicts, accept P3_core_evidence_accepted or close R07 in Issue #80.
The historical current pointer and existing P4 selection policy remain intact.
