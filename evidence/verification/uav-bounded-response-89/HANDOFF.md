# Issue #89 preparation handoff

Deliverable: one reviewable UAV service-boundary protocol/evidence package,
currently prepared for an exact domain/materialization and native-execution
decision. Owner vadimnbkg; protocol reviewer/integrator artmus208. Runner is the actual
account explicitly declared in execution/approval.json.
Independent scientific acceptance is separate and not assigned here.

- Owner branch: `codex/vadimnbkg/89-uav-bounded-response`.
- Runner branch to create: `codex/<runner>/89-uav-bounded-response-runs`.
- Operational base: `452571598d4a5c1e070dace3a918ea737904e239`, actual #88 merge.
- Scientific input commit: `61386aa358805082b705dcd00c8cbfde5fb98248`.
- Previous proposal base: `46bf268c66d6ec2c106ae4ce8e8d5f893315ad91`.
- Target: `read`; sole scope `evidence/verification/uav-bounded-response-89/**`.
- Exact preparation HEAD is the immutable published checkpoint in the Issue/PR
  handoff and in the externally stored publication record, avoiding a self-hash
  inside its own commit. Verify it using `git rev-parse HEAD` before beginning.
- Final preparation working tree: clean after checkpoints; the original shared
  checkout only receives explicitly scoped durable recovery bundles.

All six results: Q1–Q5 on proposed Hnom and Q6 on M are not_executed / null.
No #89 model-checking or version probe has been run. Production M remains
byte-identical. The current Issue requires approval before Hnom materialization;
the exact patch, prospective model hash and 40-element change list are available
for that decision. This is a conditional execution handoff, not an accepted run.

Read `WINDOWS.md`, `PROTOCOL.md`, `RUNNER.md`, `proposed-decision.md`, `approval-template.json`,
`input-pins.json`, `query-inventory.json` and `query-ledger.json`. `prepare.py
--check` reproduces the patch and formulas without saving Hnom. `audit.py` is
entirely offline. `checks/check-results.json` records commands, exit codes and
log hashes; `checks/initial-findings.json` preserves earlier limitations/failure.

Before native work, the execution record must identify authorization for the
exact preparation HEAD, Hnom
patch/hash, six query hashes, method/config/budget/stop policy and actual Windows
host/tool. Observed host/Python bindings and exact verifier path/hash are recorded
in approval-template.json; Runner must declare its persistent Windows clone path. A separate explicit Issue decision activates the proposed
execution-only write lease; Owner does not write there while Runner owns it.

Runner begins from the accepted preparation HEAD, records actual preflight and
reserved attempt commits, and returns a durable branch/bundle plus exact HEAD.
Owner then merges the Runner history, audits all raw files and budgets, inspects
the traces offline, updates `results.json`, report/coverage/English fragments and
the same final PR to read. No rebase may erase execution commits. Account
identity alone grants no native permission; use the recorded user
authorization and delegation without inventing another account's signature.

Durable retrieval: canonical Owner branch when published, with a full-history
bundle fallback in the persistent owner repository under this scope's
`handoff/`. The external publication record pins exact branch/HEAD/base and
bundle hashes. The original local preparation checkpoints are retained there
even if GitHub API publication uses equivalent tree commits.

Next execution step: record the actual decision accounts, current preparation
HEAD and native bindings. See inputs/identity-correction.json and RUNNER.md. Native
results and independent scientific acceptance remain pending. Do not close #89,
C02, full P3, C06, Gate 2 or R07 on the strength of this preparation alone.

Current validation: `checks/launch-windows-20261004-001/record.json` records
33/33 scoped native Windows tests with zero failures/errors/skips.
`checks/windows-check-results.json` selects this record by SHA256; the offline
audit checks its raw log and current Python source hashes. The earlier 26-test
Windows records remain historical evidence for the preceding source.
Current config.json SHA256:
`ee0ab52bfdc6ae3298defac8106a5cf074df968de0f51d13af0d5bd95bdd593e`.
M, prospective Hnom, restriction patch and all six formula hashes are unchanged.
The Windows binary hash was read and confirmed; its runtime version remains null.
The original Linux commit 9e4743bf is retained in the published branch ancestry.

The new preparation HEAD/seal hash, durable bundle/hash and clean working-tree
confirmation are published together in the #89/#90 Windows handoff. That exact
HEAD supersedes the prior Linux handoff for the upcoming decision. No execution
lease is activated by this code correction alone. The prior user
authorization is recorded in #89 comment 5969141901; the driver now accepts the
actual declared accounts instead of requiring artmus208. Historical preparation
records below checks/ remain unchanged; current test pointers select new records.

The full repository suite was attempted on native Windows: 209 tests, 3 failures,
3 errors and 2 platform skips. Logs are in `checks/identity-static-20261004-001/`.
Failures concern historical fixture hashes, WSL path expectations, memory
monitoring, Windows text decoding and symlink privilege. The three candidate /
operational generation checks also fail on Windows-only path serialization in
parameters.json; `generation-drift-analysis.json` proves the generator is
unchanged and model XML / queries reproduce exactly. These failures are retained,
not reported as successful checks. Scope, coordination, historical hash audit,
MCP/CLI smoke, dependency and #89 offline integrity checks passed.

Launch preparation on 2026-10-04 found and corrected stripping of the leading
Git porcelain status column before scope checking. The new regression exercises
a modified tracked execution ledger through the real Git-output helper. No
model, query, budget or watchdog semantics changed; 33 native controls pass.
