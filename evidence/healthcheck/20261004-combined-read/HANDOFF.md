# Combined read integration validation — #111

Owner: vadimnbkg. Independent Reviewer/Integrator: artmus208 / user-integrator.
Deliverable: reproducible software/static validation of nine merged PRs.
Branch: codex/vadimnbkg/111-combined-read-check. Target: read.
Base: 2f49676ad249fafa9fd36a245fc0340071ab623b.
Tested source checkpoint: 4ce4a03ee4b79d8eecd723acb1dc2ca0fd17956d.
Only this evidence directory differs from base; production, tests, models,
manifests, generators and manuscript are unchanged. Final publication HEAD is
recorded in Issue #111 and the PR. Checkpoint trees are preserved in a full
bundle at /mnt/d/uppaal_mcp/111-combined-read-check.bundle.

## Results

| Check | Result |
|---|---|
| Combined base GitHub CI, Ubuntu/Python 3.12 | completed/success; run 37187422354 |
| Linux/WSL Python 3.14.5 full suite outside sandbox | 242 tests, all successful, no skips; 94.459 seconds |
| Initial sandbox Linux suite | 242 tests, one error (MCP handshake timeout); 151.332 seconds |
| Linux MCP module follow-up outside sandbox | 6/6 successful; 3.670 seconds |
| Native Windows Python 3.14.5 full suite | 242 tests: 238 successful, one failure, three platform skips; 209.476 seconds |
| Completion proof controls on both platforms | 27/27 successful per platform |
| Capacity proof controls on both platforms | 27/27 successful per platform |
| Completion/history/capacity premise and artifact reproduction | exit 0 on both platforms |
| Coordination, dependency consistency, MCP construction, CLI examples | exit 0 on both platforms |
| Frozen hash audit | 57 file hashes, zero file/aggregate mismatches on both platforms |

These are software/static results, not licensed verifier runs, new mathematical
acceptance decisions or model-checking verdicts. Historical timeout/null results
remain unchanged. No native verifier/version/help probe was executed.

## Windows finding for integrator triage

The remaining failure is unchanged
test_verification_manager.ManagerTests.test_memory_limit_measures_real_child:
run_queue() returns 0, while the expected memory-stop exit code is 2.
The child fixture allocates 64 MiB and sleeps for three seconds; the stop
threshold is 32 MiB. All merged Windows portability/report/cache regressions
complete successfully. Skips are the two POSIX-only tests and the symlink
privilege-dependent check.

A controlled follow-up uses memory_control.py to run this exact unchanged test
with the base Windows Python versus the virtual-environment interpreter.
The base Python succeeds (exit 0); the venv interpreter reproduces the failure
(exit 1). Each outcome is recorded in its separate raw log.
The manager samples the directly launched process handle, not a descendant
tree. A venv redirector/child distinction is therefore the leading explanation;
the comparison alone is not a complete process-tree audit or a production
verifier test. Do not weaken the assertion or claim general Windows memory
enforcement from the passing base-interpreter control. A separately scoped
decision is needed for a regression/monitor correction.

## Reproduction and provenance

Create a clean clone at the base above, install the project and PyYAML into a
fresh environment, then execute run_checks.py using that environment's Python.
Each platform output directory must be absent before a new run (the hash audit
refuses overwrite). To rerun, use another clone or preserve/rename the old
evidence first; do not overwrite the submitted raw files.
The recorder saves commands, UTC start, durations, exit codes and byte-preserved
stdout/stderr. Linux and Windows checks.json include sys.executable and source
commit. environment/dependencies logs pin Python, OS and package versions.
Linux fresh setup used get-pip because system ensurepip was unavailable.
Windows installation used Start-Process -Wait after an asynchronous direct
PowerShell invocation did not provide a reliable completion observation.

Linux follow-ups: same installed environment, PYTHONDONTWRITEBYTECODE=1 and
PYTHONUTF8=1; python -m unittest discover -s tests -p test_mcp_startup.py -v,
then python -m unittest discover -s tests -v, both outside sandbox.
Their raw stdout/stderr and recorded subprocess exit codes are retained.
Windows ran from a detached read-only clone on D: under native Python, launched
by PowerShell Start-Process -Wait. The Linux owner clone is under /tmp.
Source checkpoint adds only the recorder to the exact integration base.

Raw logs retain CRLF and emitted spaces under narrowly scoped .gitattributes;
code/prose whitespace checks remain strict. artifact-hashes.json binds all
packet files except itself. Scope check: git diff --name-only BASE...HEAD must
contain only evidence/healthcheck/20261004-combined-read/**.
Shell Git push lacks credentials; canonical publication uses the authenticated
GitHub connector. Local and publication commit IDs differ; final tree equality
is checked after fetching the published branch. Original local history is also
preserved in the owner-accessible complete bundle.

Next: independent review of #111, decide the Windows memory-monitor follow-up,
then resume article integration/scientific dispositions in their own tasks.
No merge to main or scientific Gate 2 acceptance is asserted.
