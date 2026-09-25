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

Execution source, actual version, native hardware, complete command, query hash,
limits, stdout/stderr and any trace will be retained with the run. This checkpoint
prepares the execution; it does not claim a model-checking result. No automatic
retry, resource increase, baseline change or P3 acceptance.
