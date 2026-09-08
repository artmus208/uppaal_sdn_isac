# Gate 1 readiness — Issue #21

**Gate 1 remains blocked.** Candidate bytes reproduce; scientific P1/P2/interface
acceptance, accepted successor pins, query coverage/canonical-manuscript decisions
and a qualifying model-checking license check remain outstanding.

Issue [#21](https://github.com/artmus208/uppaal_sdn_isac/issues/21), P0 readiness
report, N/A — coordination-only. Owner artmus208; independent scientific
Reviewer/Integrator pending assignment. Branch `codex/artmus208/21-gate1-readiness`,
target `read`. Base `origin/read`: `bb5741b45480944630e1116fb7435effb2026655`.
Dependencies PR #16/#18/#20 are merged; this report does not infer scientific
acceptance from merge. Only this directory is writable.

Start with [decision-proposal.md](decision-proposal.md). The
[readiness matrix](readiness-matrix.json) covers all nine manifest Gate 1
requirements plus five v1/CONTRIBUTING obligations: six ready, seven blocked,
one not-demonstrated. Each row includes precise evidence/hash/commit, missing or
recorded independent decision, responsible role and next action.
[proposed-baseline.json](proposed-baseline.json) is an unfrozen proposal with
complete pins, parameter values, vector and 81-query mapping; it is not a manifest.

## Demonstrated evidence

New run [gate1-readiness-001-20260909](gate1-readiness-001-20260909/checks.json)
started clean at `fa23946ac2fe52e2c157751cf9e6fe88e6179220`; generated evidence
checkpoint `780ba277a78d0962d980a7baf9bcd88867569dc1`. The new execution commit
differs from the historical run; [comparison.json](gate1-readiness-001-20260909/comparison.json)
proves exact base input bytes and all historical metadata equality except that
execution commit. All later report changes leave model inputs unchanged.

- 20 core + eight boundary + 22 observers; 81 unique query IDs, none excluded.
- XML/query bytes match merged PR #20. Model SHA256
  `2b6928bda92bfb9bad5c74e91cf78c0b15beb4e7300bea401de8b4dc2cf592a4`;
  query SHA256 `af9bbd8e73b1bc73eb7e957a89b826d24e04f1c2f1eed2f1b1e5bb4a55cd25b9`.
- 47 input/implementation/context files match base Git blobs; 113 historical
  indexed artifact hashes match, including the complete compiler stdout.
- All 13 recorded commands exit 0. Full suite: 147 tests, no failures/errors/skips.
  Historical compile-only reused for identical bytes, not repeated.
- Actual `verifyta --version`: UPPAAL 5.0.0 rev. 714BA9DB36F49691 (June 2023).
  No model checking or model-checking license probe. Verification status: not_run.

The [GitHub snapshot](github-snapshot.json) includes Issue comments, PR reviews
and combined PR discussions. No independent scientific acceptance was found in
these inspected surfaces. [scope-audit.json](scope-audit.json) checks all ten
open Issues plus #21, finding no pairwise scope overlap at capture time.
The still-open #6 owns shared manifest paths: coordinate future supersession scope.

## Reproduction

Use a fresh clean checkout of this branch and an isolated Python environment:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -e . PyYAML
.venv/bin/python -B evidence/governance/20260908-gate1-readiness/audit.py --output evidence/governance/20260908-gate1-readiness/reviewer-NEW --verifyta '/mnt/c/Program Files (x86)/UPPAAL-5.0.0/bin/verifyta.exe'
```

Choose a new output directory within scope; do not overwrite this run. Omit
`--verifyta` if unavailable and record that limitation. The argument invokes only
`--version`. The recorder never requests compile-only or model checking.
Native Windows needs an adapted runner: this recorder captures Linux hardware
and the saved run used WSL, not native Windows Python.

`audit.py` records command arrays, exit codes, timings, selected environment
overrides, versions and raw-log hashes; checks.json and pip-freeze preserve the
actual resolution. The full suite was run outside sandbox to avoid the already
documented MCP stdio timeout. No global user settings were changed.

`build_report.py` deterministically rebuilds the JSON proposal/matrix/scope audit
from the saved run and GitHub snapshot. It is an authoring tool, not a live GitHub
recheck; run it only in a separate review copy when comparing outputs.
SHA256SUMS indexes the complete report package except itself. Validate from this
directory with `sha256sum -c SHA256SUMS`.

## Handoff and limits

The exact publication HEAD and draft PR URL are recorded in Issue #21/PR handoff;
the branch is the canonical transport once published. Before publication,
complete-history checkpoint bundles were verified under the original owner's
durable `evidence/governance/20260908-gate1-readiness/handoff/` directory. Those
transport bundles are outside the versioned report package. Git CLI HTTPS push
had no credentials; GitHub connector provides the authorized publication path.

Acceptance criteria delivered: complete requirement matrix; new reproducible
generation/static audit; scientific decision list; exact unfrozen successor
proposal; scoped evidence/checks and draft review handoff. Readiness-report
completion does not mean scientific Gate 1 completion. Independent Integrator
must assign scientific review, resolve the concrete decisions and separately
contract licensing and manifest-specific supersession. P3/P4 remain blocked.

Manifests, model implementation, historical runs and manuscript were unchanged;
the original dirty checkout was preserved. This task adds no empirical adequacy,
abstraction-soundness, timed-property, numerical capacity or scalability claim.
