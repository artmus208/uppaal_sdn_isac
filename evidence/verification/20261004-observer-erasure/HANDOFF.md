# Issue #116 handoff

Deliverable: the observer-erasure/transfer proof package, supporting P3
C01/C03/C04/C05 without changing ownership or claiming requirement closure.
Owner/account-id: vadimnbkg. Intended independent reviewer/integrator: artmus208.

Issue: https://github.com/artmus208/uppaal_sdn_isac/issues/116
Branch: codex/vadimnbkg/116-observer-erasure. Target: read.
Base commit: e5c299d0b426e57652cb8a78f37ae770949b53b1.
Scope: evidence/verification/20261004-observer-erasure/**.
Native execution commits are stored per run in reservation.json.
Acceptance remains pending independent review; no merge authorized.

Completed checks:

- Fixed-model audit: 51->29 processes, 22 erased observers, 77 helpers,
  74 observer transitions, eight ordinary broadcast receives, five committed
  observer locations with complementary update-free exits. No native verdict.
- Scoped mutation/semantic checks: final results and counts in checks-final.
- Repository suite: 251 tests run, four platform skips, no failures.
  Skips: Windows symlink privilege; Unix executable-symlink fixture;
  Linux terminal-metrics injection; POSIX flock failure injection.
- Coordination/hash audit: 57 file hashes, zero file/aggregate mismatches.
- Dependency check and MCP/CLI software smokes: exit zero.
- Original model/query/manifest hashes and diagnostic XML reproduction agree.
- Initial certificate reproduction failed due unordered committed-location
  iteration. The sorting fix and cross-hash-seed control are recorded in
  checks-final; the earlier failed record remains in checks/results.json.

Additional observed limitations:

- Computer-use found the open UPPAAL window but image state capture twice failed
  with `window capture timed out: timed out waiting on channel`. A minimal
  accessibility tree exposed only the window chrome. No GUI model inspection
  or verification succeeded; no native engine/version run was made.
- System Git 2.35.1 crashed on status with
  `BUG: refs/files-backend.c:465: returning non-zero -1, should have set myerr!`.
  Its owned sessions were stopped and its own stale index lock removed. Bundled
  Git 2.53.0.windows.3 handled the isolated clone. Use that Git for reproduction.
- The first clone used Windows autocrlf conversion, which failed the exact input
  byte gate. The isolated clone was restored from a Git archive of HEAD with
  autocrlf disabled. The final byte audit passes; the original Desktop checkout
  and its user modifications were never changed.
- The initially restricted pip setup was stopped while waiting. Dependencies
  were then installed into a separate observer-env with approved network access.
  The original user environment was not modified.

Native protocol: two single attempts, completion-safety then success,
600 seconds and 2048 MiB each. Results are retained under native/.
Exact executable, runtime and manager hashes are in native/protocol.json.
Draft PR: https://github.com/artmus208/uppaal_sdn_isac/pull/118.
Native campaign completed with no decisive verdict: completion-safety timeout
at 600.891 seconds; success stopped after 70.844 seconds with Windows
WinError 5 on atomic replacement of status.json. No trace and no retries.
See native-summary.md and native-results.json for exact bindings and raw paths.
Final integration audit reproduces the XML and certificate byte-for-byte.
Working tree is intended clean after the final checkpoint; exact HEAD is the
published branch tip, rather than a self-referential hash inside this file.
Remaining work: independent review and disposition of proof/experiment;
any runner repair or additional native budget requires a separate scoped task.

## User-authorized 30-minute rerun, 2026-10-05

The user extended timeout to 1800 seconds per formula and authorized a
conditional repair/rerun if the status-write error recurred. The scientific
inputs and 2048-MiB sampled memory stop were unchanged. Both runs ended on
memory_limit, with no native verdict: safety after 971.813 seconds, success
after 1064.141 seconds. The status-write error did not recur; no repair or
suffix-03 run was activated. Raw logs, exact bindings and integrity validation
are in native-30min/. Historical native/ evidence remains byte-for-byte intact.
Published branch remains codex/vadimnbkg/116-observer-erasure, draft PR #118;
independent acceptance remains pending. No active native worker remains.

## Completed 8-hour / 7-GiB campaign, 2026-10-05

Both planned sequential attempts finished; no active campaign worker remains.
Execution commit: 2a8b967e4899639c0e1b2ceb21b89a0ecc7a0e9c.
Native version: UPPAAL 5.0.0 (rev. 714BA9DB36F49691), June 2023.
Configured per formula: 28800 seconds, 7516192768-byte sampled memory stop.

- completion-safety-04: memory_limit, verdict=null, elapsed 6593.531 seconds,
  peak 7518007296 bytes; finished 2026-10-05T09:12:30.810712Z.
- success-04: memory_limit, verdict=null, elapsed 6762.453 seconds,
  peak 7517257728 bytes; finished 2026-10-05T11:05:13.391717Z.

The second formula began only after the first ended; one attempt per formula,
no duplicate, retry or budget increase. No status-write error or repair occurred.
Worker exit code 2 indicates incomplete verification, with two complete attempt
records. Neither property is proved or refuted. The memory stop ended each
attempt before its time budget; increasing only time does not remove it.

Evidence: native-8h/results.json, summary.md, validation.json, worker-exit.json,
raw attempt files and session version probes. Reproduce the read-only audit:
python -B evidence/verification/20261004-observer-erasure/summarize_8h.py
All 10 per-attempt inventory files, 82 historical/scientific inventory entries,
source model/manifest/query bytes, runtime pins, commands, result bindings,
sequential timestamps and telemetry reconcile. Historical evidence, XML and
certificate remain unchanged. artifact-hashes.json is now the final inventory.

Published branch: codex/vadimnbkg/116-observer-erasure; draft PR #118 to read.
Exact handoff HEAD is the published branch tip (avoids a self-referential hash).
Working tree clean after the final checkpoint; obtain via origin branch.
Base commit: e5c299d0b426e57652cb8a78f37ae770949b53b1.
Remaining step: independent proof/evidence review and disposition by artmus208;
no gate closure, scientific self-acceptance or merge. Direct model scope remains
29 processes; transfer to the 51-process original requires independent proof
acceptance. Completion heartbeat uppaal-8-7 is to be paused after publication.
