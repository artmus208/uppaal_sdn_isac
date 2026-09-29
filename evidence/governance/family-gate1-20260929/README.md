# Family Gate 1 decision proposal — Issue #72

**Proposal only: no new gate accepted, no operational baseline changed, no P4
execution authorized.** Owner/account-id: vadimnbkg. Independent reviewer and
Integrator: artmus208 / user-integrator. Atomic IDs: N/A — coordination-only.

Base `origin/read`: `52c5c8d94122f5fbd2a7b689fd9e764583de3226`.
Branch: `codex/vadimnbkg/72-family-gate-proposal`; PR target: `read`.
Write scope: `evidence/governance/family-gate1-20260929/**` only.

The accepted historical Gate 1 (`reviewer-r1-gate1-20260923`) remains valid for
its original pinned model. The family candidate and diagnostic report were
accepted separately:

- [#69 decision](https://github.com/artmus208/uppaal_sdn_isac/pull/69#issuecomment-5889994466): reproducible N=1..4 candidate and experiment protocol preparation.
- [#71 decision](https://github.com/artmus208/uppaal_sdn_isac/pull/71#issuecomment-5890111952): reproducible report of ten diagnostic timeouts.

Neither decision accepted a new Gate 1 or P4 readiness. Plan v2 §5 says Gate 1
fixes inputs and is not a claim that every formula holds. Its §1.1 permits
independent bounded work with open statements, but requires an explicit
Integrator disposition for changed claim scopes/dependencies.

## Reviewable package

- [DECISION-DRAFT.md](DECISION-DRAFT.md): Russian draft separating exact family
  freeze, a proposed restricted tool-cost experiment claim, and activation/execution.
- [baseline-candidate.json](baseline-candidate.json): four model/generator/query
  sets, parameter/vector references, observed exact tool version, historical
  baseline lineage and decision flags (all new acceptance/authorization flags false).
- [QUERY_TABLE.md](QUERY_TABLE.md) and [query-dispositions.json](query-dispositions.json):
  all 30 P4 query files and all 36 existing scientific attempts, with exact
  run_id/status/verdict/model_hash/query_hash/tool_version references.
- [input-hashes.json](input-hashes.json): exact-byte pins checked against the
  accepted base commit. Existing evidence files are referenced, not rewritten.

The evidence table contains five queries with explicit recorded results, 21
queries attempted without a verdict, and four family-queue-safety formulas never
attempted. There are 31 timed-out attempts and five explicit results in total;
repeated service attempts retain separate run IDs/strategies. No result is
inferred for a syntactically different query, even the N=1 family-safety formula.
The earlier metadata-only monitor error remains in #70's unchanged evidence;
it is not counted as a scientific attempt. Preparation/load runs are not
substituted for nonvacuity evidence.

A decision can freeze an experimental input without asserting its service
property. A restricted future experiment would measure the cost of declared
verifier attempts, with censored observations explicitly reported; it could not
establish scalability of a working serviced network. That narrowing is only a
proposal pending explicit acceptance. R03/R04/C06, the article's obligations,
historical P3 and the old baseline are unchanged.

## Reproduction

From a checkout containing the pinned base and this package:

```sh
python3 -B evidence/governance/family-gate1-20260929/build_packet.py --self-test
```

This checks deterministic packet bytes, exact input/base identity, coverage,
source run records and eight negative controls against invented acceptance,
missing queries, hash changes and fabricated verdicts. It never launches UPPAAL.
`--write` regenerates only this proposal's derived files; do not use it to change
previous evidence or operational manifests. Repository validation and scope
results are recorded under checks/. Publication and exact HEAD are in Issue #72.

Next: independent review of this proposal, then explicit A/B dispositions and
a separately assigned manifest activation if accepted. No new verifier runs or
long measurement campaign is part of this deliverable.
