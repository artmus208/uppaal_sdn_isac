# P2 integrated single-UAV candidate — Issue #19

Owner: `carwasher`, after the user-authorized handoff from `artmus208` recorded in
[Issue #19](https://github.com/artmus208/uppaal_sdn_isac/issues/19).
Continuation branch: `codex/carwasher/19-integrated-evidence`; PR target: `read`.
Base: `dc7eeb05f1fd3f2a4775428b1cd250363893128d`.
Specification/source audit: [Issue #17 package](../20260907-p2-scope/README.md),
input commit `7baa86e8d0d9eb2fc2df8d728a360c6b7cfb91bb`.
Atomic requirements: R01/R02/R05/R06, implementation continuation; independent
scientific acceptance and overall P2 completion remain pending.

The generator composes the pinned default PHY/MAC/SDN models and stored APP XML,
retaining 20 core processes and 22 observers and replacing ten standalone
environment/stub instances with eight boundary processes. It emits one XML,
candidate queries and a machine-readable composition map. Existing layer
generators, the specification, manuscripts and manifests are read-only inputs.

Implementation: `src/uppaal_mcp/integrated/`. Read [decisions.md](decisions.md)
before interpreting the candidate. `tests/test_sdn_layer.py` contains the
`IntegratedCandidateTests` software regressions. `replay.py` executes selected
concrete edges for those tests; it is not an UPPAAL interpreter or model checker.

## Reproduction

Use Python 3.10+ in a checkout containing the pinned specification and source
files. Source/specification changes are rejected; new populations/profiles are
unsupported, rather than silently treated as this candidate. On native Windows:

```text
py -3.14 -m venv .venv
.venv/Scripts/python.exe -m pip install -e . PyYAML
.venv/Scripts/python.exe -B -m uppaal_mcp.integrated.generator --output evidence/instantiation/20260908-p2-integrated/reviewer-generated-new
.venv/Scripts/python.exe -B -m unittest discover -s tests -p test_sdn_layer.py -k IntegratedCandidateTests -v
```

Output directories must be new: generation and check recording refuse to
overwrite existing directories. On Unix substitute `.venv/bin/python`.
For the full evidence recorder, begin with a clean committed tree:

```text
py -3.14 -B evidence/instantiation/20260908-p2-integrated/checks.py --output evidence/instantiation/20260908-p2-integrated/reviewer-run-new --python .venv/Scripts/python.exe --install --verifyta D:/UPPAAL/app/bin/verifyta.exe
```

Omit `--verifyta` if unavailable; that limitation is recorded explicitly.
The recorder sets `UPPAAL_COMPILE_ONLY=1` only for the compiler invocation. It
saves the tool's actual version/help output, exact commands, source commit,
environment, hardware, timestamps, exit codes and stdout/stderr hashes.
Compilation does not execute the candidate queries. No property verdict, runtime
scaling result or verification claim follows from a successful compilation.

The full software suite uses process-only `core.autocrlf=false`, matching the
documented exact-byte fixture requirement in the input package. Repository and
global Git settings are not changed. The recorder also sets `PYTHONUTF8=1` and
`PYTHONDONTWRITEBYTECODE=1` and clears an inherited `PYTHONPATH`.

## Artifacts and checks

No completed final run is present. [reviewer-run-002](reviewer-run-002/README.md)
records the historical loss of the venv interpreter; the subsequent
[recorder regression attempt](reviewer-recorder-blocked-003/README.md) stopped
on a new test harness error. The formerly referenced `checks-native-01` does not
exist. A future successful run must supply `checks.json`, raw logs and
`generated/model.xml`, `queries.q`, `composition.json` and its hash index.
`composition.json` records input hashes, implementation hashes,
the generator-hash construction, entity/process vector, ordering, parameters,
channel endpoints, candidate query mapping and exact before/after XML for every
adapted retained template/declaration. Source commit identifies the implementation
commit that produced the output; later evidence-only commits do not change its
model/query/generator hashes.

```text
.venv/Scripts/python.exe -B evidence/instantiation/20260908-p2-integrated/audit.py evidence/instantiation/20260908-p2-integrated/reviewer-run-new
```

The audit regenerates XML/query bytes, checks implementation/input hashes and all
raw-log hashes. It does not infer scientific acceptance. Development directories
`dev-*` are ignored, and are not acceptance evidence.

## Acceptance mapping

| Issue criterion | Reviewable evidence |
|---|---|
| Deterministic 20+8+22 composition | generator.py; generated model and system_order; partition/determinism tests |
| Remove stubs; namespace symbols and clocks | xmlutil.py; process/symbol maps; exact adaptation records; lexical shadowing tests |
| Typed ACKs, staged admission, command/policy routes, losses | adapt.py/boundary.py; concrete edge regressions; endpoint map |
| Finite inputs, source age, observer/event semantics | boundary.py; latch adaptation; age/deadline/sampling tests; decisions.md |
| Parameters, queries, provenance, unsupported input rejection | inputs.py; composition.json; mutation and query-reference tests |
| Behavioral/static checks and verifier diagnostics | software tests and recorded compile-only output, with exact tool version |
| CONTRIBUTING checks and handoff | checks.py, raw logs, audit.py and PR to read |

Independent review must evaluate the semantic changes and limitations below; this
checklist describes implementation evidence, not acceptance by the author.

## Limits

This is an abstract single-BS/single-UAV/controller/service candidate. Time units
are not calibrated; the finite sample domain includes physically inconsistent
tuples except the two explicitly excluded detection contradictions. APP Crit/Agg
remain zero-transition placeholders. Reconfiguration is recorded, not implemented
as an application lifecycle. Existing core zero-time cycles and policy
location/value disagreements remain visible. Oldest-outstanding event latches
coalesce repeated monitoring events; this is an observer adaptation requiring
review, not an abstraction-soundness proof.

P1/P2 scientific acceptance, baseline supersession and Gate 1 are pending. No
verification run is produced, and no query is reported as verified. P3/P4 remain
subject to the manifest gates.
