# C02: one BFS retry with a 600-second limit

Issue #39, continuation of PR #50. User authorized this retry on 2026-09-24.
Owner/runner: vadimnbkg. No independent acceptance or P3 closure is implied.
Continuation base: `31bc321dcc61f805b75a12a323285a8008a7c439`.
Original task base: `adea99b05195191eec115621613d4190eba06bf0`.

## Latest result: C02 still inconclusive after 600 seconds

After the user installed the license, run
`p3-20260924-c02-600-002-01-C02-ack-elapsed` reached actual verification but
stopped at **600.1356183 seconds**: `status=timeout`, `verdict=null`, native
exit code -1. No formula verdict or diagnostic trace was emitted. Licensing
preflight succeeded and query stderr was empty; the previous license blocker
was not reproduced. No 1800-second attempt was made.

Peak native working set: **1,144,475,648 bytes (1.066 GiB)**, below the sampled
2 GiB stop threshold. Sampled peak private bytes: 1,195,937,792. The stop reason
was time, not memory. Raw progress ends with `Load: 5816615 states`; that is not
a final explored-state count or a completion percentage, so `states_explored`
remains null. The tenfold time allowance did not yield a C02 verdict.

Source: clean published commit `984d104d744b1da7d6e2def6e49f17f2d999915f`.
Hardware: Intel Core i5-8300H, 4 cores/8 logical processors, 17,033,019,392 bytes
visible RAM, Windows 10 version 10.0.19045; WSL orchestration. This is a
different host from the original September 23 runs, not a controlled scaling
benchmark. Actual UPPAAL version, original formula, model/query hashes and
complete parameters/vector are recorded in `result-002.json` and
`../p3-20260923/p3-20260924-c02-600-002/{run.json,run.yaml,results.json}`.

Raw archive: `evidence/verification/runs/p3-20260924-c02-600-002.tar.xz`;
SHA256 in the corresponding `archive.json`. Baseline hash identity and the
saved-evidence audit pass. These are consistency checks, not a positive C02
verification result. The failed attempt 001 below remains preserved.

```bash
mkdir -p /tmp/c02-review
tar -xJf evidence/verification/runs/p3-20260924-c02-600-002.tar.xz -C /tmp/c02-review
python -B evidence/verification/p3-20260923/audit.py /tmp/c02-review/p3-20260924-c02-600-002
```

The completed attempt used the command below with run ID ending `-002`.
Any further attempt needs a new ID and an explicit resource/strategy decision;
do not overwrite old evidence or silently alter the frozen model/formula.

Final checks after attempt 002: **180 project tests OK**, **2 focused runner
tests OK**, baseline 57 file hashes and 2 aggregate hashes match, coordination,
dependency check, FastMCP construction and example listing succeed. Re-extracted
archive matches the published summaries; native measurements/config/raw output
agree with JSON/YAML records. Logs: `checks-002.txt`, `software-tests-002.log`,
`baseline-audit-002.json`. These checks do not turn the C02 timeout into a verdict.

Frozen baseline `reviewer-r1-gate1-20260923`, its complete model, parameter set,
instance vector and selected query set remain unchanged. Run only the original
`C02-ack-elapsed` formula; retain the sampled 2 GiB working-set stop threshold.
The first attempt is limited to 600 seconds. No automatic 30-minute retry.

The existing runner now accepts `--timeout-seconds` (positive integer, default
60) and `--verifyta` (default retains the prior D: installation). The native
process receives the requested limit; its outer wrapper receives 30 additional
seconds for shutdown and output. Native working directory follows the chosen
executable. No system environment or license configuration is changed.

Run from a clean committed checkout with an available licensed Windows verifier:

```bash
python -B evidence/verification/p3-20260923/run.py \
  --run-id p3-20260924-c02-600-001 \
  --ids C02-ack-elapsed --search-order 0 --trace-kind 0 \
  --timeout-seconds 600 \
  --verifyta '/mnt/c/Program Files (x86)/UPPAAL-5.0.0/bin/verifyta.exe'
```

Use a fresh run ID if the directory already exists. Exact version is checked
against the frozen baseline; hardware and operating environment are captured per
run. A license error or timeout is inconclusive, never a satisfied property.

Focused software checks (mocked native boundary, no verifier verdict):

```bash
python -B evidence/verification/p3-20260924-c02/test_runner.py -v
```

## Historical attempt 001: license-blocked, no C02 verdict

The requested attempt ran from clean published source commit
`313733cf8382644b27a2df7f23ce2ede2ccb4e82` with BFS, some diagnostic trace,
600-second native limit and 630-second wrapper limit. The verifier exited with
code 1 after 2.6518174 seconds and emitted exactly:

```text
License does not cover verifier.
```

Run ID: `p3-20260924-c02-600-001-01-C02-ack-elapsed`.
Recorded status: `error`; verdict: `null`. This is diagnostic evidence, not
model checking success and not a new timeout. The orchestration exit code 0
means that the failed native attempt was recorded; it does not override the
native error. The version preflight also recorded a host-resolution error and
`Failed to retrieve licensee.` The reason for license unavailability has not
been established; no licensing or global network settings were modified.

The executable reports UPPAAL 5.0.0 (rev. 714BA9DB36F49691), June 2023.
Complete actual output, hardware and query provenance: `result.json` and
`../p3-20260923/p3-20260924-c02-600-001/{run.json,run.yaml,results.json}`.
The source/model/generator/parameter/vector hashes match the accepted baseline.
Model SHA256: `592678ed678ce8f70cf278f542e48bd2bb739969b53a962423d3e63f91e3e1e2`.
C02 query SHA256: `cec919bc6e2d960160976799d3d52ff4f25eea9f136f7b0231c02cec13f162db`.

Raw archive: `evidence/verification/runs/p3-20260924-c02-600-001.tar.xz`.
Archive hash is recorded in
`../p3-20260923/p3-20260924-c02-600-001/archive.json`.
To inspect the preserved attempt without a verifier:

```bash
mkdir -p /tmp/c02-review
tar -xJf evidence/verification/runs/p3-20260924-c02-600-001.tar.xz -C /tmp/c02-review
python -B evidence/verification/p3-20260923/audit.py /tmp/c02-review/p3-20260924-c02-600-001
```

Two focused software tests passed (default 60 seconds, requested 600 seconds,
outer-wrapper allowance, selected executable path, unchanged formula and
timeout-without-verdict propagation). Baseline audit: 57 hashes, zero file or
aggregate mismatches. The complete raw-evidence audit passed for the one failed
attempt; this only checks evidence consistency.

The licensing prerequisite was resolved for attempt 002 above. C02 and P3
remain unaccepted. Historical run records were not changed.
