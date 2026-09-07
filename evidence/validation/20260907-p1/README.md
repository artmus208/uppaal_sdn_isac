# P1 review handoff — 2026-09-07

Issue [#15](https://github.com/artmus208/uppaal_sdn_isac/issues/15), owner artmus208,
branch `codex/artmus208/15-validation-parameters`, target `read`.
Base/input commit: `f2f714a26d6b9d9f538ef1a16b53c3e060768a11`.
Baseline `reviewer-r1-candidate` remains unfrozen. Independent reviewer/integrator
assignment and scientific acceptance are pending; V01–V05 are not closed.

Start with [validation-report.md](validation-report.md), then
[parameter-table.md](parameter-table.md) and [sources.md](sources.md).
[inventory.json](inventory.json) contains exact source hashes/line references,
all three built-in profiles, declaration/clock-constraint inventories and the
raw eight-boundary Python observations. `SHA256SUMS` hashes all package files
except itself.

Delivered: 43 timing parameters, 59 finite domains, calibration methods including
symbolic estimator inputs, automaton/composition adequacy obligations and a proposed
external-trace exchange procedure. Demonstrated: deterministic source inventory
and the mismatch between worse-class metadata and eight equality outcomes.
Not demonstrated: physical calibration, simulator integration, empirical adequacy,
integrated model verification or a licensed model-checking run.

## Reproduction

Use the PR checkout. The inventory requires only Python ≥3.10 and reads its local
repository sources. It does not invoke UPPAAL or write shared generated models.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 evidence/validation/20260907-p1/inventory.py --check
cd evidence/validation/20260907-p1
sha256sum -c SHA256SUMS
```

From repository root, create an isolated environment and a new checks directory:

```bash
python3 -m venv /tmp/uppaal-p1-review-venv
/tmp/uppaal-p1-review-venv/bin/python -m pip install . PyYAML
/tmp/uppaal-p1-review-venv/bin/python evidence/validation/20260907-p1/checks.py \
  --output /tmp/uppaal-p1-review-checks
```

The output directory must not already exist. On WSL with a real UPPAAL installation,
optionally append `--verifyta-cwd '/mnt/c/Program Files (x86)/UPPAAL-5.0.0/bin'`
to record the version diagnostic. Set `UPPAAL_VERIFYTA_PATH` for another installation.
This runs only `--version`, not model checking. Review diagnostic exit codes in
`checks.json` even if the overall software-check command returns zero.

`inventory.py` without `--check` regenerates the two inventory artifacts in this
package. Review differences before accepting changed sources; it does not update
or freeze the baseline manifest. New model/profile/mode inputs need a new review.

## Recorded checks

Environment: Python 3.12.3, WSL2 Linux, MCP 1.30.0, PyYAML 6.0.3.
Exact commands, cwd, durations, package versions and raw log hashes are in
`checks/checks.json` (restricted sandbox) and `checks-host/checks.json` (host run
outside the execution sandbox). Sources were unchanged between these runs.

| Check | Restricted sandbox | Host run |
|---|---|---|
| Inventory regeneration comparison | exit 0; 43 timings, 59 domains, 8 policy mismatches | same |
| Coordination structure | exit 0 | exit 0 |
| Unit suite | 126 tests, one error: MCP stdio initialization timeout; exit 1 | 126 tests, zero failures/errors/skips; exit 0, 32.012 s |
| MCP construction / built-in example listing | both exit 0 | both exit 0 |
| Historical baseline hash audit | exit 1; 9/20 file hashes and generator aggregate mismatch | same |
| verifyta version | CLI exit 2; WSL socket permission error | CLI exit 2; 15 s timeout with empty output |

The initial dependency installation in the restricted sandbox failed while fetching
setuptools (`Operation not permitted` / proxy connection). Retrying with network
access succeeded; `install.log` records the successful isolated installation.
The current verifier version was **not obtained**. An earlier healthcheck's version
must not be substituted for this run, and no license or verification claim follows.

The host unit result resolves the sandbox-specific test failure without a source
change. It does not resolve physical/model adequacy, baseline drift or verifier
availability. No licensed/model tests were silently skipped: this deliverable's
declared verification requirement is “no”.

## Scope and next handoff

All changes are under `evidence/validation/20260907-p1/**`. Models, generators,
manifests, manuscript and the user's original dirty checkout are untouched.
P2 can use the documented decisions on boundaries, missing data, freshness,
units, D_cmd and cross-layer timing. No additional workstream is accepted or
unblocked by the author. The independent reviewer must assess the P1 method and
decide the required abstract versus physically calibrated claim scope before
Gate 1; P3/P4 still require their accepted frozen baseline.
