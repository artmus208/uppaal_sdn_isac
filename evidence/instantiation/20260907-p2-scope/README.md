# P2 model-scope specification — Issue #17

Owner: `carwasher`. Branch: `codex/carwasher/17-model-scope`; PR target: `read`.
Base/source commit: `7baa86e8d0d9eb2fc2df8d728a360c6b7cfb91bb`.
Write scope: `evidence/instantiation/20260907-p2-scope/**` only.
Atomic IDs: R01/R02/R05/R06, addressed as a specification; independent acceptance
and overall P2 completion remain pending.

The package distinguishes the four existing standalone projections from a
proposed single-BS/single-UAV/controller/service test composition. It reproduces
four channel-kind conflicts, documents absent MAC policy and PHY command peers,
identifies APP placeholders/stubs and gives a complete nine-edge scheduler
analysis. The proposed vector contains 20 core, eight new boundary and 22 observer
processes. The boundary templates and integrated XML are not implemented here.

Read [model-scope-specification.md](model-scope-specification.md), then
[interface-contract.md](interface-contract.md) and [decisions.md](decisions.md).
[inventory.md](inventory.md) gives current process counts and channel endpoints;
[inventory.json](inventory.json) pins 38 source-file hashes and 14 XML surfaces.
[instance-vector.json](instance-vector.json) records the candidate entity/process
counts, ordering and abstract parameter choices.
[scheduler-analysis.md](scheduler-analysis.md) explains the existing automaton;
[scheduler-edges.md](scheduler-edges.md) is generated directly from its edge records.

## Reproduction

Run from a checkout containing this package and its pinned base commit. Python
3.10+ is sufficient for the inventory/specification scripts; the recorded full
suite used Python 3.14 on native Windows.

```text
python -B evidence/instantiation/20260907-p2-scope/inventory.py --check
python -B evidence/instantiation/20260907-p2-scope/check_spec.py
python -B evidence/instantiation/20260907-p2-scope/integrity.py --check
```

For a fresh environment on Windows:

```text
py -3.14 -m venv .venv
py -3.14 -B evidence/instantiation/20260907-p2-scope/checks.py --output evidence/instantiation/20260907-p2-scope/reviewer-new --python .venv/Scripts/python.exe --install
```

On Linux/macOS use `python3 -m venv .venv` and `.venv/bin/python`. Choose a new
output directory for every run. The recorder refuses to overwrite prior logs;
the integrity check reads only the original indexed files, allowing new reviewer
logs alongside them. --write/--write-table/--write-index are initial-authoring
options, not required for review. Their existing outputs must not be overwritten.

## Recorded checks

`checks-native-01/checks.json` records exact command arrays, cwd, environment,
timestamps, durations, exit codes, and stdout/stderr hashes. Input artifacts at
the start of that check run are separately hashed. SHA256SUMS indexes the final
delivered package including the recorder, report, raw logs and check metadata;
the index excludes itself. Raw logs are marked `-text -diff` locally in this
scope to preserve their bytes in Git.

- Fresh editable install: exit 0; MCP 1.30.0, PyYAML 6.0.3; pip check exit 0.
- Inventory reproduction: exit 0; 38 pinned files, 14 XML surfaces, four
  cross-layer channel-kind conflicts reported without asserting compatibility.
- Vector/source partition and nine-edge table: exit 0; all 50 proposed process
  entries accounted for; three malformed-vector probes rejected.
- Coordination structure and YAML parse: exit 0, static checks only.
- Full unit suite: **126 tests, no failures/errors/skips**, 61.128 seconds,
  exit 0. Includes real MCP stdio initialization/list-tools regression.
- MCP construction, installed example listing and recorded diff check: exit 0.

The recorder sets `core.autocrlf=false` for its child Git processes to isolate
exact-byte hash-audit fixtures from the machine's `core.autocrlf=input` setting.
It does not change repository/global Git settings. This environment override is
part of the reproduction command contract; no claim is made that the full suite
was run here with every machine default unchanged. The recorded diff check ran
before initial staging; the final staged scope/whitespace checks are also reported
in the PR. No real verifyta invocation was needed or performed by this package.

## Acceptance coverage

| Issue criterion | Evidence |
|---|---|
| Actual templates/instances and entity interpretation | inventory.json/.md; R01 section of specification |
| Explicit candidate vector and construction contract | instance-vector.json; construction steps and boundary requirements |
| Interface ownership/kinds/indexing/initialization | interface-contract.md; channel endpoint inventory |
| Detailed automaton | scheduler-analysis.md and generated scheduler-edges.md |
| Finite abstractions and bounded claims | R06 section; no explored-state/scale claim |
| P1 dispositions and pending decisions | decisions.md; explicit unaccepted status |
| Reproduction, checks, provenance and limitations | scripts, checks-native-01, SHA256SUMS and this README |

## Limits and downstream handoff

This is a candidate specification and source audit. It does not implement an
integrated model, physically calibrate parameters, demonstrate simulator
integration, prove abstraction soundness or verify a query. New boundary process
behavior, APP lifecycle/timeouts, ACK correlation and observer adaptation require
a separately scoped P2 implementation and independent review. Reviewer assignment
is still pending. The historical candidate remains unfrozen; no P1 acceptance,
P2 process acceptance, Gate 1 or P3/P4 readiness is implied.

Official semantic references were read on 2026-09-07:
[UPPAAL semantics](https://docs.uppaal.org/language-reference/system-description/semantics/),
[edges](https://docs.uppaal.org/language-reference/system-description/templates/edges/),
[types](https://docs.uppaal.org/language-reference/system-description/declarations/types/).
These describe language rules, not evidence that the present candidate satisfies
any formal property. All source observations are tied to the pinned repository
files rather than to those general language references.
