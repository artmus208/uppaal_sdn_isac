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
