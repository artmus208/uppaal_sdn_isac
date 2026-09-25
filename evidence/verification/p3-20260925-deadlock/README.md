# C01: alternate full-model deadlock search — Issue #39

Owner vadimnbkg; branch `codex/vadimnbkg/39-deadlock-search`; target `read`.
Base commit `66c0f1f706993170ff3165c77188fe00eb1e700b` (accepted PR #55 merge).
Gate 1 baseline `reviewer-r1-gate1-20260923` remains unchanged.

## Scope and rationale

The user accepted PR #55's concrete recovery invariant argument for attempt
bounds and recorder protocol discipline. This does not establish global deadlock
freedom. The original full-model deadlock query previously timed out with BFS at
60 seconds and DFS at 60/300 seconds. This continuation changes search strategy,
without increasing the last resource budget or altering model behavior.

One run, `p3-20260925-deadlock-001`, original `C01-deadlock` formula
`A[] not deadlock`, randomized DFS order (`-o 2`), symbolic exploration
(`--exploration 0`), explicit seed (`-r 20260925`), exact DBM representation
(`--state-representation 0`), some trace (`-t 0`), 300 seconds and the existing
sampled 2 GiB working-set stop. The threshold is polled every 50 ms, not a hard
allocation cap. Random search order does not select concrete randomized
exploration or bit-state hashing. Any result still requires an explicit native
verdict; a timeout/error establishes neither satisfaction nor violation.

Search-option support is confined to the evidence runner. Existing BFS/DFS
defaults are preserved; randomized DFS requires an explicit seed and only exact
state representations 0/1 are selectable. Supported flags were obtained from
the installed tool's help retained in the prior C01 structure package.

## Reproduction

From a clean published source checkout and using a fresh run ID:

```sh
python3 -B evidence/verification/p3-20260923/run.py \
  --run-id NEW-UNIQUE-RUN-ID --ids C01-deadlock \
  --search-order 2 --trace-kind 0 --seed 20260925 \
  --state-representation 0 --timeout-seconds 300 \
  --verifyta /mnt/d/UPPAAL/app/bin/verifyta.exe
```

Frozen full model SHA256:
`592678ed678ce8f70cf278f542e48bd2bb739969b53a962423d3e63f91e3e1e2`.
Frozen selected-query pack SHA256:
`3027dedb1a68d21fce84efc532e3490602eade5306c5dafc9652d38cc4e2eb18`.

## Observed result

Execution source: `ebfe0a63d2b7842bfac195e6d541118ce3a89d91` (clean published checkpoint).
Run ID: `p3-20260925-deadlock-001-01-C01-deadlock`.
Status **error**, verdict **null**. Native exit code `-1073741819`
(unsigned hexadecimal `0xc0000005`), after 15.8519758 seconds;
peak working set 186265600 bytes. The process exited before
300 seconds and below the 2 GiB stop threshold. Native stderr is empty; stdout
contains search progress but no formula verdict. No trace was produced.
This is a tool/process failure, not a deadlock counterexample or proof of freedom.
The crash cause is not established by these files. No automatic retry performed.

Native wrapper termination="completed" means the process exited on its own;
its nonzero exit and absent formula result correctly produce status=error.
Raw options banner confirms random DFS, the explicit seed and DBM representation.
The full argument vector also explicitly selects symbolic exploration 0.

Query SHA256: `a53c752ecabf84d28dc0ea1567c0589ffb632777a5ad7178f70be0d2d99e5334`.
Tool: UPPAAL 5.0.0 (rev. 714BA9DB36F49691), June 2023 (complete captured version in records).
Full model/query/parameter/vector identities are unchanged.

## Evidence and validation

- [Complete raw archive](../runs/p3-20260925-deadlock-001.tar.xz).
- [Run metadata](../p3-20260923/p3-20260925-deadlock-001/run.yaml),
  [per-query result](../p3-20260923/p3-20260925-deadlock-001/results.json),
  [archive SHA256](../p3-20260923/p3-20260925-deadlock-001/archive.json).
- Native hardware, actual version, complete command, limits and stdout/stderr
  are inside the archive. `audit.json` records archive/copy/option/result checks.
- `options-check.json`: legacy defaults preserved, unseeded random DFS,
  negative seed, approximation representations 2/3 and zero timeout rejected.
- `checks.txt` and `software-tests.log` record final validation separately from
  model checking. Software success does not turn this error into a query verdict.

Extract the archive separately and run:

```sh
python3 -B evidence/verification/p3-20260923/audit.py /PATH/p3-20260925-deadlock-001
```

The original timeout records remain unchanged. The accepted PR #55 direct
attempt/protocol argument and PR #53 scoped C02 argument remain separate.
C01 global deadlock is still inconclusive. Review the tool failure before any
further run; no resource increase, model repair, baseline change or P3 acceptance
is inferred. Exact published HEAD and PR reference are recorded in Issue #39.
