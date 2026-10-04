# P4 / R04 scientific handoff — Issue #101

Issue: https://github.com/artmus208/uppaal_sdn_isac/issues/101

Deliverable: a primary-source applicability analysis and a worked, auditable
projection proof of the accepted family's recorded shared-service capacity.
Owner account: `vadimnbkg`. Integrator: `artmus208`.
Independent scientific reviewer: not yet appointed; acceptance remains pending.

Branch: `codex/vadimnbkg/101-r04-compositional-proof`.
Base: `read` / `f0fcd770e3e6b93f99868b9116e4f0929f60d0fa`.
Target: `read`. Remote: `git@github.com:artmus208/uppaal_sdn_isac.git`.
Write scope: `evidence/scalability/20261004-r04-compositional-proof/**` only.
The PR body records the exact final head and final CI outcome; this avoids a
self-referential commit hash inside its own tree.

## Scientific result and dependencies

The grant/server relation implies the existing shared-capacity predicate for
each of N=1,2,3,4 under the audited premises. The full-to-abstract forward
simulation preserves that safety assertion; it does not transfer abstract
existential witnesses back to the concrete model. The algebraic lemma for any
finite N is explicitly conditional and does not extend the generator's domain.

The Glonina comparison distinguishes component verification, composition and
timed-diagram determinism from configuration execution. It gives theorem-specific
cutoff hypotheses and explains why no unbounded UAV claim can currently be
imported. The English integration material is a proposal; the manuscript and its
bibliography have not been changed.

Dependencies and accepted input decisions:

- Operational v2 activation: [#64 decision](https://github.com/artmus208/uppaal_sdn_isac/issues/64#issuecomment-5878071165).
- P1/P2 A/B limited abstract applicability: [#73 decision](https://github.com/artmus208/uppaal_sdn_isac/pull/73#issuecomment-5890790922).
- Family Gate 1 / activation: [#75 decision](https://github.com/artmus208/uppaal_sdn_isac/pull/75#issuecomment-5891123461), merge `c6b07b252f7d25e4879d49b9cb32bf381e9555fb`.
- Input manifest: `uav-family-r1-20260929`, SHA256 `5480bef5b00020735259f10eb43bdd9bc79ebc364a3bbcacad34c78fd0552cbf`.
- Historical #76 campaign: `campaign-002`, run-source commit `877fa69a29e1732db2b4047eebdd99591b185c77`; twelve selected native attempts remain `timeout` with null property verdicts.

The original manifest's pending-activation text is historical metadata; the
independent activation decision above and explicit Issue selection supply the
workstream context. This package does not edit that metadata or declare a gate.

## Validation records

Full command arrays, raw stdout/stderr hashes, runtimes and exact source commit
are saved in `checks/windows/results.json` and `checks/linux/results.json`.
They refer to scientific implementation checkpoint
`3702f123568fac0942381af17c54a89060e0dc09`; subsequent delivery documentation
does not change the checked algorithm or frozen inputs.

| Check | Result |
|---|---|
| Scoped premise/artifact reproduction, Windows Python 3.11.3 | Exit 0 |
| Scoped adversarial tests, Windows | 27 tests, all successful, no skips; exit 0 |
| Same proof and tests, Ubuntu/WSL Python 3.12.3 | Exit 0; 27 tests, all successful, no skips |
| Full repository suite on native Windows | 209 tests; 3 failures, 4 error events, 2 skips; exit 1 |
| Replay of every failing Windows method on exact base commit | Six methods reproduce the same 3 failures and 4 error events; exit 1 |
| Coordination contract | Exit 0 |
| Coordination hash audit | 57 hashes, zero file or aggregate mismatches; exit 0 |
| Finite-family audit including Git history | 4 models, 30 queries, 106 current and 107 historical input hashes; exit 0 |
| Installed dependency consistency | `pip check`, exit 0 |
| MCP construction and CLI example listing | Both exit 0 |
| Repository version-only smoke probe | Exit 0; raw result saved separately; not model checking |

Windows regression-control details are in `checks/windows/base-control.json`
and its raw logs. The exact base is an isolated clone, and `PYTHONPATH` points
to its own `src`. No production or test file outside the Issue scope changed.
The failing cases are:

1. Two missing-tool CLI methods produce three error events because UTF-8 parent
   decoding meets localized CP1251 child output. The test's reader thread fails
   and `json.loads` receives `None`; this is not a changed CLI result.
2. The symlink containment fixture lacks Windows symlink privileges (WinError 1314).
3. A hash-audit fixture has Git line-ending conversion mismatch.
4. A WSL path-translation fixture expects POSIX paths when run natively on Windows.
5. The real-child memory-limit fixture returns 0 where the test expects 2.

These are inherited test/environment findings, not silently waived successes.
Issues #99/#100 already cover neighboring Windows/coordination work; this package
does not take over their write scopes. The PR CI result provides a separate
Linux check of the repository suite. CI does not execute the scoped proof tests;
their explicit Windows and Linux records remain necessary.

**Process deviation:** the repository-required `uppaal-verifyta version` smoke
command was executed even though Issue #101's out-of-scope wording excluded real
verifier probes. The exact command was `verifyta.exe --version`; it had no model
or query argument and performed no model checking. Its raw output is retained
in `checks/windows/version-probe.stdout.txt`. It is not used as evidence for the
mathematical result or substituted for a historical run's measured tool version.
No further native verifier invocation is required for this deliverable.

## Reviewer reproduction and acceptance boundary

1. Fetch the published branch and confirm the exact PR head. Check that its diff
   against the stated base contains only the Issue directory.
2. Run the two commands in `README.md`. Inspect the mutation controls, especially
   alias exposure, selector mutation, split writes and query/input drift.
3. Review O1–O7 and all three transition cases in `PROOF.md`. Confirm that the
   projection is an overapproximation and transfer is only in the stated direction.
4. Compare the Glonina propositions and their hypotheses with the cited primary
   pages and concrete XML selectors; check the distinction between Proposition 7
   and its observer corollary.
5. Inspect the original historical records through `generated/historical-runs.json`;
   no timeout is reclassified and no nonvacuity witness is invented.
6. Decide whether the mathematical claim and proposed R04 response are acceptable
   for integration. Record that decision independently before requirement closure.

Artifact identity is provided by the source ledger, per-model certificate,
original-run index, test-log hashes and published Git commit. The PR supplies
the final head and CI link. Remaining next step is independent scientific review
and, if accepted, integration by the manuscript owner. No R04, R03, C06, P3 or
final manuscript gate is self-accepted by the author.
