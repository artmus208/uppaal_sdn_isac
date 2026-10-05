# Persistent 8-hour / 7-GiB native campaign

User authorization: 2026-10-05, increase time to 8 hours and memory to 7 GiB.
Issue #116 records the protocol amendment; prior evidence remains unchanged.

One native Windows queue executes completion-safety then success sequentially.
Each formula has timeout 28800 seconds and sampled memory stop 7516192768
bytes (7168 MiB). Worst-case combined search time is 16 hours. Exact individual
query bytes and diagnostic XML are pinned in protocol.json and queue.json.
Native options remain -o 0 -t 0, with per-attempt trace output requested.

Task 001 maps to observer-erasure-116-20261005-completion-safety-04; task 002
maps to observer-erasure-116-20261005-success-04. The persistent hidden worker
advances automatically after success, timeout or memory_limit. Error or
monitor_error halts the queue; no blind restart of a reserved queue is allowed.
The earlier authorization to repair a recurring status-write failure remains
valid; any repaired attempt needs its own preserved inputs, source checkpoint
and new run ID. Do not overwrite failed evidence or resume this queue blindly.

Monitor append-only worker.stdout.log and immutable completed attempts. Do not
open hot status.json using PowerShell. The native manager samples aggregate
working set and CPU through its owned Windows job and terminates only its job.
Reservation.json records the execution commit and worker PID. The launcher
creates only the two append-only worker logs before the worker's clean-source
check. At completion the worker validates attempt file hashes and writes
results.json and worker-exit.json; unexpected exceptions go to worker-error.json.

Reproduction preparation (new run ID/directory required for a rerun):
python -B native_campaign_8h.py prepare
python -B native_campaign_8h.py worker

The direct scope is the 29-process diagnostic composition. A successful
explicit native verdict is needed to settle either query; transfer to the
51-process model remains conditional on independent proof acceptance.
