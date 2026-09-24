# C02: one BFS retry with a 600-second limit

Issue #39, continuation of PR #50. User authorized this retry on 2026-09-24.
Owner/runner: vadimnbkg. No independent acceptance or P3 closure is implied.
Continuation base: `31bc321dcc61f805b75a12a323285a8008a7c439`.
Original task base: `adea99b05195191eec115621613d4190eba06bf0`.

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

Raw results, source checkpoint, reproduction/audit outcomes and final status will
be recorded here after execution. Historical runs 001/002/003 are read-only.
