# PHY artifact cache integrity — #104

Issue: <https://github.com/artmus208/uppaal_sdn_isac/issues/104>.
Process: P0 software reliability. Atomic IDs: N/A — coordination-only.
Owner: vadimnbkg. Integrator: artmus208. Independent reviewer: unassigned.

An exported `satisfied` result could be returned as a cache hit for a later
`timeout`, because result, model, contract, trace and command did not all
participate in the cache key. On Windows, newline translation also made the
exported model bytes disagree with `model_hash`. Directory existence alone
previously counted as a cache hit, including partial exports without metadata.

The new key covers all material inputs and distinguishes missing optional
content from empty content. A separate format version leaves historical cache
directories untouched. UTF-8 text is written without newline translation.
Repeated inputs reuse a bundle only after checking its file inventory, actual
file hashes, input hashes and matching metadata. A damaged cache raises a
descriptive error and remains unchanged; `force=True` explicitly rebuilds it.

## Scope and revisions

- Base: `origin/read`, `f0fcd770e3e6b93f99868b9116e4f0929f60d0fa`.
- Branch: `codex/vadimnbkg/104-phy-artifact-cache`; target: `read`.
- Final tested source: `4efe53eb5b8f302fb3b82318d90c71cc12a4aebf`.
- Final packaging HEAD and publication status: Issue #104 / its linked PR.
- Exact write scope: `src/uppaal_mcp/phy/artifacts.py`,
  `tests/test_phy_artifacts.py`, `docs/phy_layer_usage.md`,
  `evidence/healthcheck/20261004-phy-artifact-cache/**`.
- Dependencies: existing merged exporter and
  [v2 activation](https://github.com/artmus208/uppaal_sdn_isac/issues/64#issuecomment-5878071165).
  No pending workstream is consumed.
- Baseline: `manifests/baselines/reviewer-r1.yaml`, ID
  `reviewer-r1-gate1-20260923`, SHA256
  `d542e617148169361b96126d55bba91079fe5c8ac3cfe6d67e27755fae3a46f7`.

Existing public tool signatures and metadata fields remain compatible. The
internal metadata helper gains an optional trace input; the new private
`artifact_checksums.json` indexes all exported files, including reports and
metadata. Text hashes describe exact UTF-8 bytes; JSON hashes retain the existing
canonical-object meaning. The index additionally hashes formatted JSON bytes.
Extra user files are preserved but are not returned as part of the bundle.
Bundle/file symlinks are rejected, including with force.

## Validation and evidence

`final-checks/checks.json` records the final commands, source hashes, environment,
exit codes, durations and raw log hashes. `summary.json` compares the final
full-suite failures to six targeted tests on a separate exact-base checkout and
checks that saved logs and tested sources retain their recorded hashes.

- Final focused checks cover 13 new cache regressions plus 42 existing PHY tests.
  All 55 pass with no skips.
- Final native Windows full suite: 222 tests, 214 passed, 3 failures, 3 errors,
  2 skipped; exit 1. All six failure/error IDs also fail on the exact base.
  Coordination, 57 baseline hashes/both aggregates, static PHY benchmarks,
  FastMCP construction, CLI examples and pip check each return 0.
- Tests cover each cache input, timeout after success, public wrapper behavior,
  optional content, raw mixed LF/CRLF and Cyrillic text, missing/corrupt files and
  metadata, altered checksum indexes, interrupted writes, explicit repair and
  unchanged unrelated files. Synthetic results do not invoke a licensed verifier.
- Full-suite, structural coordination, committed baseline hash audit, static PHY
  benchmarks, FastMCP construction, CLI examples and dependency checks are
  recorded separately. A failing full suite is not presented as successful.
- The exact-base comparison retains the known Windows problems: coordination
  encoding (two), Git fixture line endings, symlink privilege, emulated WSL paths
  and verification-manager memory limit. Pending fixes #99/#102 and #100/#103
  are separate branches and were not copied into this task.

The earlier `before-focused.*` records show the first 11 regressions against
unchanged production code (43 failing subtests, two errors). `checks/**` is an
intermediate 12-test checkpoint, preserved with its recorded hashes. The final
13-test source is also run against the exact base in
`final-checks/baseline-regressions.log`; failures there are expected reproduction,
not failures of the repaired implementation. Missing-index errors on the base
reflect that its exporter did not yet produce an integrity index.

Raw diagnostic logs retain original line endings and trailing spaces; only
these logs have whitespace checking disabled by scoped Git attributes. Source
and documentation still use ordinary diff checks. `baseline-audit.json` reads
committed Git blobs and checks 57 baseline file hashes and both aggregates.

## Reproduction

Use a fresh output directory. On Windows, from the repository root:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -e . PyYAML
.venv\Scripts\python.exe -B evidence/healthcheck/20261004-phy-artifact-cache/run_checks.py --output .venv/phy-cache-review
git diff --check f0fcd770e3e6b93f99868b9116e4f0929f60d0fa...HEAD
```

For before/after reproduction, create an independent checkout at the exact base
above and add `--baseline-root <base-checkout>`. The runner loads production code
from that checkout and the new tests from this task for `baseline-regressions`;
`baseline-failures` uses only the base's own six existing tests. Both working
directories and PYTHONPATH values are recorded. On POSIX, use the native virtual
environment interpreter instead of `.venv\Scripts\python.exe`.

The runner returns 1 when any recorded test command fails, including deliberately
reproduced failures on the base. Read each command's exit code and log. No native
verifier/version probe, simulation or model checking is required or performed.

## Handoff

Retrieve the published branch from the canonical repository and use the exact
final HEAD recorded in the PR. The next step is independent software review and
integration into `read`. The implementation changes export caching only; it does
not establish a model-checking verdict or accept a scientific requirement/gate.
