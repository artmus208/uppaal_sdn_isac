# Handoff — Issue #108

Deliverable: proof of truthful UAV completion, stable receipt records and causal
receipt history, with fixed-model premise checker, mutation controls, historical
evidence reconciliation and proposed English article/reviewer text.

Owner/account: vadimnbkg. Independent Reviewer/Integrator: artmus208.
Branch: codex/vadimnbkg/108-completion-safety-proof.
Target: read.
Base: f0fcd770e3e6b93f99868b9116e4f0929f60d0fa.
Checked proof/checker source checkpoint:
d330219ad4554b4d1307235d9ac2443b0180aa5a.
The final published delivery HEAD is recorded in the #108 handoff comment
and PR after this file is committed; obtain it with git rev-parse HEAD.
Only evidence/verification/20261004-completion-safety-proof/** changes.

## Scientific result and scope

Theorem 1 gives Completed -> (all 26 accepted query conjuncts and inactive)
by initialization, entry, discrete preservation and delay induction.
Theorem 2 establishes the ordered actual event history and receipt-time bounds:
sample age <5 from acquisition completion, request age <=40 from actual send.
One request/result, no ID reuse, N=1/51 processes, exact hashes.
This is mathematical_argument supported by static_validation, with independent
acceptance pending. It is not a new native verdict or universal progress result.

All production code, models, generators, manifests, prior evidence and manuscript
are unchanged. #101 shared-capacity and #89 native bounded-response work are
independent. No native executable/version probe/engine run was launched.

## Validation disposition

- 27/27 scoped tests pass, including premise-breaking controls below the outer
  hash gate and positive controls; checks-final/scoped-tests.stderr.txt.
- Exact XML/query/manifest checks and deterministic certificate reproduction pass.
- Historical trace/status audit reproduces. The saved replay has 100 transitions;
  causal flags first occur at states 4, 62, 84, 85, 96, 99 and 100.
- Original #87 completion-safety attempt remains timeout/null (600.5930649 s).
  Query hash f3cfb3800063b21045d94625f616950944663fcba61956a3498aba62ca32edf9.
- Coordination passes; 57 baseline file hashes and aggregates have no mismatch.
- MCP build and CLI module smoke pass. Both CLI console tests pass after actual
  package entry-point installation (checks-followup/).
- Full Windows suite: 209 tests, 5 failures, 1 error, 2 skipped in the isolated
  run. Two failures were missing CLI entry points and pass in the targeted
  follow-up. Four repository tests remain unresolved: three failures and one
  error. There is no single green full-suite run.
- git diff --check passes with scoped attributes recognizing CRLF in raw Windows
  output. Logs are preserved byte-for-byte; code/prose whitespace is still checked.

Remaining full-suite failures (unchanged tests/src/scripts relative to base):

| Test | Observed result / disposition |
|---|---|
| test_coordination.HashAuditTests.test_exact_bytes_and_committed_manifest | Fixture expects match but returns mismatch. Related Windows fixture work: #99 / PR #102. The real 57-file baseline audit passes separately. |
| test_family_baseline.FamilyBaselineTests.test_paths_and_symlink_escape_rejected | WinError 1314 creating a symlink; related portability work #100 / PR #103. |
| test_sdn_layer.IntegratedRecorderTests.test_windows_compile_only_forwards_flag_and_translates_paths | Backslash versus slash expectation in wslpath input; related #100 / PR #103. |
| test_verification_manager.ManagerTests.test_memory_limit_measures_real_child | Synthetic worker returns success (0), expected memory stop (2). The host monitor test remains unresolved; no verifier was run and no monitor code was changed. |

Initial checks/ additionally retains a cp1251/old-editable-environment run and
the first failing byte-gate control. checks/initial-environment.md explains the
correction. checks-final/ records isolated Python 3.12.14, MCP 1.30.0,
PyYAML 6.0.2, PYTHONUTF8=1, commands, dependencies and results. The task-local
ignored .venv has installed package console launchers and a source .pth entry
pointing at this worktree's unchanged src. Package staging remained inside
that ignored environment. No environment from another task was changed.

## Reproduction and independent review

Run the three stdlib commands in README.md. For repository checks, install the
project and PyYAML in a clean environment and run CONTRIBUTING-v2 commands.
On Windows preserve UTF-8 mode; report the platform-specific failures rather
than modifying model or unrelated tests in this Issue.
Check artifact-hashes.json for package byte integrity (it excludes itself and
ignored environment/cache files).

Review proof.md, especially the binary sender/receiver update order,
late-cancellation identity, closed writer inventory and unique clock resets.
Review premises.json as a human-audited fixed-input capsule, not an independent
oracle. The checker deliberately rejects changed premises; it is neither a
general UPPAAL interpreter nor a proof-assistant kernel.
Inspect the event graph and historical raw references separately from the
universal argument.

Publication on the canonical branch makes this result durable. Reviewer
artmus208 must independently decide scientific acceptance; repository test
failures need disposition before merge. The author has not merged, closed
#108/P3/requirements, or accepted a gate. The manuscript integration snippet
is a proposal for P9, not an applied manuscript change.
