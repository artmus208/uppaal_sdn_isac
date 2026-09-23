# Passive recovery attempts — Issue #45

Owner/runner: vadimnbkg. Base: `read` at
`6890960b3e0042b633887957052aabf45aee51d9` (accepted #44).
Execution source: `43306bd189ba6cf4464888d8d5867e80f8a2f224`, clean at start.
No new Issue was created. User explicitly authorized continuing #45 in the same
chat. Independent scientific acceptance and Gate 1 remain separate decisions.

## Contract and implementation

A new episode starts when A_REC receives link_failure/node_failure in StableConfig.
Its local success/failure ends the episode. Counters observe actual dispatches:
policy/flow requests are primary, rollback requests are rollback. Offers, ACKs
and reports are not attempts. Bounds per episode are primary <=1, rollback <=1,
total <=2. Direct rollback counts once; failure before dispatch counts zero.

The counter domains retain violations: primary/rollback saturate at 2, total at
3. `sdn_attempt_bad` and `sdn_attempt_protocol_error` remain sticky across episodes.
Only an accepted new start when inactive resets counts. Duplicate active starts
retain counts and record protocol misuse. Dispatch outside an episode and finish
without an active episode record protocol misuse. No functional edge, guard,
invariant, synchronization, clock or policy depends on these counters.

The instrumentation is applied after the accepted #35 recovery timing recorder.
An automated erasure check removes only the new declaration and calls and compares
the entire XML tree against archived accepted #44 bytes. It includes locations,
initial state, declarations, guards, invariants, synchronization and updates.
The existing recovery test's exact-edge comparison similarly erases only new
attempt calls; its timing/policy assertions are unchanged. All other source
files and the queue implementation remain unchanged.

Generator metadata identifies recorder version 1 and limits separately; the
functional configuration ID is retained because the erasure is exact. Six new
candidate queries cover count safety, protocol safety and nonvacuity of start,
primary, rollback and two dispatches. They have no full-composition verdict.

## Recorded results and limits

Run `recovery-attempts-20260923-001` used actual UPPAAL
`5.0.0 (rev. 714BA9DB36F49691), June 2023` through Windows interop from WSL.
All 24 recorded commands exited 0. The complete software suite ran 178 tests in
57.898 seconds, with no failures or skips. Coordination, MCP construction,
examples, dependency consistency and whitespace checks completed with exit 0.

There are 49 expected query results across 17 compositions:

| Cases | What is demonstrated in the saved diagnostic compositions |
|---|---|
| standby, reembed, direct | Actual A_REC with replacement peer: appropriate dispatch count and completed episode reachable |
| before-dispatch-failure | Local failure with zero dispatch remains reachable |
| primary-rollback | Both actual dispatches can occur in one episode |
| repeated-0, repeated-1 | Two actual episodes reset counts, including immediate completions; wrong/stale ACK offers remain in the peer |
| duplicate-primary, duplicate-rollback, third-total | Synthetic calls to actual recorder functions expose expected safety violations; trace retained |
| outside, duplicate-start, stale-finish | Synthetic protocol misuse is observable and never blocks the driver |
| sticky-reset, saturating, protocol-sticky | Violation history survives reset, counters saturate without integer-domain failure |
| integrated-parser | Full generated XML `E<> true` only: engine load, not full-composition attempts/deadlock/response verification |

The synthetic driver is explicitly a recorder unit harness; it is not a claim
that duplicate dispatches occur in production. The seven recovery-peer harnesses
retain actual A_REC and its timing observer but replace the rest of the network.
No claim of full-model C01/C02, P1/P2 acceptance or Gate 1 is made.

[results-index.json](results-index.json) provides per-case run_id/status,
source_commit/model_hash/query_hash/tool_version, query verdicts, exact commands,
timing and stdout/stderr paths. `status=success` means expected diagnostic
outcomes, including deliberate negative safety verdicts. Counterexamples for
negative universal queries are retained. [run.json](run.json) and
[composition.json](composition.json) pin source/generator hashes, parameters,
instance vector, environment and hardware. State count/peak memory are recorded
as not_available; no such measurements are inferred.

## Audit and reproduction

[publication.json](publication.json) pins the lossless archive containing all 113
raw files, including XML, queries, traces, logs and SHA256SUMS. Every archived
byte was compared with the original file before packaging. Four JSON summaries
are exact copies from the archive. The audit checks hashes, stdout verdicts,
metadata consistency, software results and negative safety traces; it does not
run UPPAAL.

```sh
python3 evidence/instantiation/20260923-recovery-attempts/audit.py
```

Extract the archive into a fresh directory to inspect original files:

```sh
mkdir /tmp/recovery-attempts-inspect
tar -xJf evidence/instantiation/20260923-recovery-attempts/runs/recovery-attempts-20260923-001.tar.xz -C /tmp/recovery-attempts-inspect
```

For a new execution use a clean committed tree, an isolated environment per
CONTRIBUTING and a unique run ID:

```sh
python -B evidence/instantiation/20260923-recovery-attempts/check.py --run-id recovery-attempts-REVIEW-NEW --verifyta /path/to/verifyta
```

The saved run used `/mnt/d/UPPAAL/app/bin/verifyta.exe` outside the sandbox;
exact command arrays and limits are in commands.json. Dependencies are captured
in dependencies.txt. No historical evidence was overwritten.

## Handoff

Branch: `codex/vadimnbkg/45-recovery-attempts`, target `read`.
Write scope: integrated/adapt.py, integrated/generator.py, new
`tests/test_integrated_recovery_attempts.py`, the explicitly authorized narrow
comparison change in `tests/test_integrated_recovery_contract.py`, and this directory.
Scope handoff is recorded in #19/#30/#35/#45. #36 stays deferred.
Next: review and accept this #45 deliverable, then final P1/P2 decisions and
baseline freeze through existing governance work. No additional tasks are opened.
