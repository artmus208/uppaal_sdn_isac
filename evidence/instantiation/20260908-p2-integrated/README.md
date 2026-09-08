# P2 integrated single-UAV candidate — Issue #19

Owner: artmus208. Branch: `codex/artmus208/19-scoped-candidate`; PR target: `read`.
Scoped base: `426cf570138231765b21d518f9d20289e2b11b63`.
Historical implementation base: `dc7eeb05f1fd3f2a4775428b1cd250363893128d`.
Dependencies: merged PR #16 (P1 source audit) and #18 (P2 specification).
Baseline: reviewer-r1-candidate, frozen:false; scientific acceptance and Gate 1 pending.
IDs R01/R02/R05/R06 remain implementation continuation of #17.

## Current result

[reviewer-scoped-005-20260908](reviewer-scoped-005-20260908/README.md) records
21 focused tests and the full 147-test suite, no errors/failures/skips, exit 0.
Every recorder command, compile-only and static audit exited 0 outside sandbox.
The model and query bytes match historical run-003: 20 core + 8 boundary +
22 observer processes. No property checking, scientific acceptance or gate claim.

The user authorized the scoped continuation in #19. Only AGENTS.md is classified
as operational context: its historical and actual hashes are saved separately in
`context_document_hashes`. All remaining inventory entries, both specification
JSON files, scientific manifests and model/generator sources remain strict pins.
Regression tests check that documentation drift preserves XML/query bytes and
model/specification/manifest mutations still fail. The audit also checks recorded
context hashes. The original specification and AGENTS.md are read-only.

This branch was constructed from current read and only the three permitted paths
were transferred. The prior AGENTS.md/two promts PR scope violation is absent.
Previous branches and historical run files were preserved unchanged.

## Reproduction

Use a fresh isolated venv (Python 3.10+) in a clean checkout:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -e . PyYAML
.venv/bin/python -B -m unittest discover -s tests -p test_sdn_layer.py -k Integrated -v
.venv/bin/python -B evidence/instantiation/20260908-p2-integrated/checks.py --output evidence/instantiation/20260908-p2-integrated/reviewer-new --python .venv/bin/python --verifyta '/mnt/c/Program Files (x86)/UPPAAL-5.0.0/bin/verifyta.exe'
.venv/bin/python -B evidence/instantiation/20260908-p2-integrated/audit.py evidence/instantiation/20260908-p2-integrated/reviewer-new
```

Save focused logs outside the checkout until the recorder starts. Use a new
output directory. On native Windows substitute .venv/Scripts/python.exe and the
actual verifier path. Omit --verifyta if unavailable; it is recorded as unavailable.
On WSL, the recorder translates paths with wslpath and forwards
UPPAAL_COMPILE_ONLY via WSLENV; on native Windows it sets the variable directly.
Only compilation is requested, not property exploration.

Recorder commands retain process-only core.autocrlf=false, PYTHONUTF8=1 and
PYTHONDONTWRITEBYTECODE=1; inherited PYTHONPATH is cleared. See checks.json for
exact commands, timings, environment, hardware and stdout/stderr hashes.
The generated composition records source/implementation/context hashes,
parameters, instance/query/process/endpoint maps and exact adaptation records.
The source implementation commit and its published equivalent tree are in
summary.json. Audit checks XML/query reproduction and provenance/log integrity.

## Criterion mapping

| Criterion #19 | Artifact | Command/result | Limitation |
|---|---|---|---|
| Deterministic 20+8+22 composition | generated/model.xml and composition.json | focused and audit exit 0 | Candidate, no scientific acceptance |
| Remove stubs; namespace symbols/clocks | xmlutil.py; exact adaptation records | lexical/partition regressions exit 0 | Supported pinned scalar dialect only |
| Typed ACKs, admission, routes, losses | adapt.py, boundary.py; endpoint map | concrete edge regressions exit 0 | Replay is not timed model checking |
| Finite inputs, source age, observer/events | decisions.md; composition.json | age/deadline/sampling regressions exit 0 | APP placeholders, coalesced events, abstract bounds remain |
| Parameters, queries, provenance, rejection | inputs.py; composition.json | drift/integrity/mutation regressions and audit exit 0 | Only AGENTS.md is non-model context; all other pins strict |
| Behavioral/static and verifier diagnostics | new raw logs | 147 tests, compile-only exit 0 | No property verdict or model-checking license probe |
| CONTRIBUTING and scoped handoff | checks.json, SHA256SUMS; handoff-pr-body.md | all recorder commands and diff check exit 0 | Independent draft review still required |

## Historical diagnostics and limits

run-002 and recorder-blocked-003 preserve recorder failures. run-003 preserves
19 focused tests/static audit exit 0, full suite with MCP timeout and WSL interop
failure. unrestricted-004 preserves the later AGENTS.md pin rejection.
These immutable records describe their source checkpoints; do not rerun a newer
generator over them and expect implementation/context metadata to match.

Read [decisions.md](decisions.md) for semantic review obligations. This remains
an abstract single-BS/single-UAV/controller/service envelope, with uncalibrated
time units, finite samples, APP Crit/Agg placeholders, unimplemented application
reconfiguration and coalesced observer events. P1/P2 acceptance and Gate 1 remain
pending; P3/P4 are not unblocked by software tests or compile-only diagnostics.
