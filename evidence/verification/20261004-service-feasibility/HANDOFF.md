# Issue #115 — scientific handoff

Deliverable: one fixed-model proof package for FIFO freshness feasibility and
conditional terminal outcome. Owner: vadimnbkg. Independent Reviewer/Integrator:
artmus208/user-integrator. Evidence class: mathematical_argument supported by
static_validation; no new native engine run or model-checking verdict.

Base ref: read. Base commit: e5c299d0b426e57652cb8a78f37ae770949b53b1.
Local branch: codex/vadimnbkg/115-service-feasibility.
Target of a future PR: read. Exact final HEAD is recorded by the supplied Git
bundle ref (and final chat handoff), rather than a self-referential tracked field.
Scientific input commit: 61386aa358805082b705dcd00c8cbfde5fb98248.
Selected baseline: uav-service-completion-r1-20261002, N=1/51 processes.
Model hash: b8ab50e112b71491f8242789cc7906497baf8440c473d7a5a4d5214840187e02.
Manifest hash: 4b4bf71f55767123cc5934074024179289fa5ad3355fa4c0e37385e8261ef98d.
Dependencies and decisions: context.md. Write scope: this directory only.

## Review results

Read proof.md, then certificate.json and check.py. The mathematical result is:

- Success requires a token enqueued first, without a skipped counted service
  decision, and enqueue+phase+launch+transport latency below 5.
- Enqueue rank >=2 cannot yield fresh success in M, since successive serving
  decisions are 5 apart and receipt requires age strictly below 5. No claim of
  rank-2 reachability is made.
- Every time-divergent execution containing emission reaches an absorbing APP
  terminal by age 40. This includes unsuccessful terminals; it excludes finite
  maximal deadlocks and bounded-time infinite executions, without proving that
  any given prefix has a divergent continuation.

The existing #110 causal/safety certificate is independently reproduced. The
new audit scans 51 templates, 884 transitions and 77 global helpers, closes the
writer sites of nine timing/rank/queue variables, and checks graph/epoch/reset
premises. A fixed semantic capsule closes unsupported modifications; this is
specialized premise support for the human argument, not general proof automation.
All 26 premise mutations are rejected. Eight rational arithmetic tests and three
baseline/dependency tests complete the 37-test scoped suite.

The pre-existing successful engine replay was inspected separately: the queue
was empty at state 84, insertion at state 85 set rank 1, decision 96 dispatched,
attempt 99 and receipt 100 completed. This is consistent with the success filter;
no new replay, precise concrete timestamp reconstruction or universal verdict
is claimed. Original replay/run metadata remain in the accepted #110 package.

## Executed validation

Checked source: 4019325b019397dae70d8f266397fbcf76c8be79.
Environment: isolated native Windows venv, Python 3.12.14, MCP 1.30.0,
PyYAML 6.0.3. run_checks.py records all commands, exits and log hashes in
checks/windows-001/record.json. Every recorded command exited 0:

| Check | Result |
|---|---|
| New premise/certificate reproduction | exact match |
| Scoped suite | 37 passed, zero skips |
| Accepted causal proof reproduction | all 26 conjunct entry obligations reproduced |
| Coordination | passed |
| Frozen baseline audit | 57 file hashes, zero file/aggregate mismatches |
| pip check / FastMCP construction / CLI examples | passed |
| Full repository suite | 251 total: 247 passed, 4 skipped, zero failures/errors |

The four full-suite skips are retained in its stderr log (Windows symlink
privilege, Unix executable symlink, Linux terminal-metrics race injection and
POSIX flock failure injection). No Linux execution
is claimed by this new packet. No test success is interpreted as model checking.

Captured Windows logs retain their CRLF bytes and recorded hashes. The first
default whitespace audit flagged those CR bytes; the scoped .gitattributes marks
them as line terminators and binary-preserved text logs. The final default
git diff --check succeeds without changing historical captured output.

The first dependency reproduction failed because local cloning converted LF to
CRLF. In the clean isolated clone core.autocrlf was disabled and tracked files
were materialized from exact Git archive bytes. Reproduction then passed; the
index was refreshed and no tracked source/content changes outside scope remain.
The first isolated pip install failed due sandbox network denial; installation
completed under escalation, without changing a shared Python environment.

## Durability and publication

Complete-history checkpoint bundles were verified outside the temporary worktree
in the user's Desktop/pySources directory. The final bundle is
uppaal-115-service-feasibility-final2.bundle; exact final branch/HEAD and SHA256
are supplied in the final chat handoff. It contains every local checkpoint.

Shell push failed authentication. Creating the initial result tree was rejected
by automatic approval review: explicit consent for transmitting this package to
artmus208/uppaal_sdn_isac was required. No workaround publication was attempted.
On 2026-10-05 the user explicitly approved publication of this package in that
repository and creation of a PR to read. Publication uses the canonical GitHub
connector; the PR records the actual published HEAD and local/published tree
comparison. PR.md is the prepared description template, not a live status board.
The verified final2 bundle preserves the pre-publication local history; subsequent
publication metadata commits remain on the same isolated local branch.
Independent mathematical acceptance is still the reviewer/integrator's task.

UPPAAL was identified as an open Java window through computer-use. Screenshot
capture failed (`FrameArrived timed out`), and the permitted recovery reported
`Computer Use helper already has an active request`. No model was modified or
engine run performed. The scientific argument depends on frozen XML and official
semantics, not on GUI availability. ChatGPT chat context was read through app tools.

Reproduce using the three README commands; inspect article-snippet.md for proposed
P9 integration. Do not change model/query/manifests or historical statuses to make
these conclusions apply outside the exact baseline. No requirement or gate closed.
