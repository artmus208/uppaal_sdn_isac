# Agent technical review of the authorized Issue #89 checkpoint

Reviewed 2026-10-03, 15:26 Moscow (12:26 UTC). This is an agent technical review,
not independent scientific acceptance. No UPPAAL executable, including `-v`/`-h`,
was invoked; no Hnom XML, approval, session claim or query reservation was created.

**Disposition: the exact prepared checkpoint cannot execute under the truthful
current identity. Preserve the six unused slots and continue manuscript work.**
The user's START-CODEX.md authorizes the one bounded campaign after technical
review and supersedes the old requirement to obtain another manual approval.
The blocker is executable code at the expressly selected checkpoint, not absence
of a new manual acceptance.

## Exact checkout and current published state

- Preparation HEAD: `77c0431049e4b5d367d56e1eb5232ed2d330258e`.
- Scientific input: `61386aa358805082b705dcd00c8cbfde5fb98248`.
- Operational base: `452571598d4a5c1e070dace3a918ea737904e239`.
- Clean review clone: `C:\Users\musta\.codex\worktrees\3ac5\mcp_uppaal\runner-89`.
  Created by `git clone --no-hardlinks --no-checkout submission-work runner-89`;
  `core.autocrlf=false` was set before checkout. Branch:
  `codex/vadimnbkg/89-authorized-native-run`. No production file was edited.
- Live [PR #90](https://github.com/artmus208/uppaal_sdn_isac/pull/90) is open,
  draft, unmerged, and has that exact HEAD; target `read` is at the operational
  base. Live [Issue #89](https://github.com/artmus208/uppaal_sdn_isac/issues/89)
  has four comments, all preparation records. The latest is
  [5968879541](https://github.com/artmus208/uppaal_sdn_isac/issues/89#issuecomment-5968879541).
  It reports no execution lease or verifier run. A current branch search returned
  only `codex/vadimnbkg/89-uav-bounded-response` matching 89.
- Published query-ledger has six `planned` slots, each `attempt_consumed=false`,
  `status=not_executed`, `verdict=null`. No execution directory was found in the
  review clone or the inspected known Windows worktree/primary-checkout paths.
- Native Toolhelp reports zero existing verifyta processes. Read-only Windows
  process command lines show only the UPPAAL MCP Python parent/child (PIDs 7992,
  26568), both `-m uppaal_mcp`, and no native Python campaign controller. Initial
  sandbox CIM access was denied; the read-only escalated query succeeded.
  These are point-in-time native Windows checks, not a guarantee about all
  unpublished or remote sessions.

## Blocking code, reproduced without verifier invocation

All paths below are under `evidence/verification/uav-bounded-response-89/`.

1. `driver.py:90-91`: `verify_approval()` demands both `approver == 'artmus208'`
   and `runner == 'artmus208'`, otherwise raises
   `ValueError: Wrong decision authority or Runner`. A truthful record using
   `vadimnbkg` with both user-authorized booleans set true was passed directly to
   this function in memory. It failed at line 91, before native checks or writes.
2. `driver.py:19,114` fixes and enforces branch
   `codex/artmus208/89-uav-bounded-response-runs`; line 130 also writes the session
   producer as `artmus208`. The requested truthful `vadimnbkg` branch fails that
   guard as well. An Issue comment alone cannot change these comparisons.
3. `driver.py` is sealed; the audit validates all 43 sealed files, and approval
   validation binds `seal.json` to the approved preparation commit. Modifying,
   monkey-patching, or calling around these checks would cease to be execution
   of the exact authorized prepared runner. Entering `artmus208` merely to pass
   them would misrepresent producer/approval identity. Neither was done.

The user's instruction explicitly says to preserve a concrete blocker if this
checkpoint is technically unsuitable. No new scientific or resource inputs are
needed to explain this refusal. A future code revision must truthfully support
the assigned identity and receive its own applicable authorization; this review
does not authorize or implement such a revision.

## Integrity and protocol results

Executed using native
`C:\Users\musta\AppData\Local\Programs\Python\Python311\python.exe`:

```powershell
$Python = 'C:\Users\musta\AppData\Local\Programs\Python\Python311\python.exe'
$Scope = 'evidence/verification/uav-bounded-response-89'
& $Python -B "$Scope/prepare.py" --check
& $Python -B "$Scope/audit.py"
& $Python -B -m unittest discover -s $Scope -p test_protocol.py -v
```

All three commands exited 0. Current software tests: 8/8, zero failures/errors/
skips. The audit confirmed 16 scientific input hashes, 43 sealed files, exact
six formulas, 40 allowed external-element changes, and unchanged 51-process
composition. The existing native Windows `checks/windows-004/record.json` and
its source/raw-log hashes also validate: 26/26 synthetic controls, zero skips;
these 26 controls were not rerun after identifying the blocker. The meaningful
current eight controls cover tamper detection, allowed XML changes, receipt
boundaries, source drift, reproducible products, atomic-write failure and
fail-closed verdict parsing. They are software checks, not model checking.

M is retained exactly. Prospective Hnom remains restricted to nominal external
PHY choices, zero background arrival/resource classes and removal of injected
fault alternatives; internal measurement failure, service nonselection, loss,
cancel, timeout and waiting choices are preserved. Q1-Q5 share Hnom; Q6 uses M.
Q4 success and Q6 terminal response remain different obligations. No positive
success guarantee or fairness premise is supplied by this review.

Native host/Python identities match the template: DESKTOP-Q3CKGDN, Windows 10
build 19045, Python 3.11.3 AMD64. Physical RAM is 17,033,019,392 bytes, producing
the prescribed sampled stop threshold of 8,121 MiB = 8,515,485,696 bytes. The
verifier PE hash was reread successfully; its actual runtime version remains
unobserved.

The reviewed guard owns child Job Objects before execution, uses monotonic
deadlines and kill-on-close, and buffers telemetry until cleanup. Config retains
one verifier, no retries, caps 180/180/180/600/180/180 seconds, 1500 seconds total
search and 1800 seconds whole session. Timeout/memory stop yields null and may
proceed only to later slots; errors/monitor or watchdog failures stop the series.
These controls do not remove the identity blocker.

## Exact pins

| Artifact | SHA256 |
|---|---|
| Original M | `b8ab50e112b71491f8242789cc7906497baf8440c473d7a5a4d5214840187e02` |
| Prospective Hnom | `3d29abc8a19aa743fa5e83bde7c83e3c45de36f166ea2b74315443156b073e03` |
| Hnom patch | `b0d8e07da9401af0b64ec0224f9241456e1d8e408817c9f3432da0a868504742` |
| config.json | `44b26d2213e8450ebcc39043fb0342d88d6a407a44ab18976a2b79761c415c81` |
| seal.json | `f61648ca0d8bf920fd941b56ab24b7aca0d3eaceaed570a71354e82713a8360d` |
| driver.py | `a7f222384d6dbaf0d0d33e68cb45a33c462fca0fe587b10a133ff6f50ab4580e` |
| verifyta.exe | `4c8af2716ff61f3cf35c6d1dc408ccf306d44bb22478e104548a8f0f7a3febe5` |
| Q1 | `c599715a482970ae4b72e6fc1384cb1d05cd1631b166f4a9beb4f2a9507413d2` |
| Q2 | `ff797cc96cc6d018f9e6a2fa8921e81a21c7ec4fc86638b96fdfbe6adf9c11de` |
| Q3 | `9a4dc76aca31e0cd333d27ab3fab461e42128896929e2b6afa62df88b37701e9` |
| Q4 | `9b89f698bcb9031e939ac9b653480a2c164ff8cb5fc8956d2b8f947e1da4bcaf` |
| Q5 | `2507c2c36030471676705b6589d8d783b419bbf3bd96ef4171caedd4ae298dae` |
| Q6 | `16b39342f932f42136802ec92947eaf2b2f102ce34e0013b7727e76fb11f7871` |

## Execution command and unmet prerequisites

The documented command is
`& $Python -B "$Scope/driver.py" run --approval "$Scope/execution/approval.json"`.
It was not executed and must not be used from this review clone in its current
state. Before an applicable future run, the runner must accept a truthful
identity, an exact published decision URL, the intended branch and a clean
committed native-host/approval/Hnom checkpoint; its remote must be canonical,
fresh process/ledger checks must exclude an earlier or active campaign, native
synthetic controls must pass, and a full durable checkpoint/bundle must exist.
The review clone's origin intentionally remains its local source clone because
no run or publication was attempted. Correcting that remote alone cannot solve
the identity/branch gate.

Review handoff: zero attempts consumed, no execution lease acquired, no GitHub
comment posted by this reviewing agent. The lead agent may record the user's
decision and this exact technical disposition in #89 while continuing the
authorized submission package. No C02/P3/Gate 2/R07 acceptance is claimed.
