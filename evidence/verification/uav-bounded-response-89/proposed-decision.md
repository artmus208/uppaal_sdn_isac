# Proposed decision for artmus208 — NOT APPROVED

Post only after review; replace the preparation and native-host fields with actual values. The Owner does not approve this text.

```text
I, artmus208, approve the Issue #89 preparation at exact HEAD: <PREPARATION_HEAD>.
I approve the nominal-input diagnostic restrictions, materialization and their limited scientific scope as described in PROTOCOL.md; this is not a sufficient-success assumption or a frozen baseline.
Hnom prospective SHA256: 3d29abc8a19aa743fa5e83bde7c83e3c45de36f166ea2b74315443156b073e03
Exact proposed patch SHA256: b0d8e07da9401af0b64ec0224f9241456e1d8e408817c9f3432da0a868504742
Original full M SHA256: b8ab50e112b71491f8242789cc7906497baf8440c473d7a5a4d5214840187e02
Config SHA256: 44b26d2213e8450ebcc39043fb0342d88d6a407a44ab18976a2b79761c415c81

Six ordered query SHA256 values:
Q1 (Hnom, 180 s): c599715a482970ae4b72e6fc1384cb1d05cd1631b166f4a9beb4f2a9507413d2
Q2 (Hnom, 180 s): ff797cc96cc6d018f9e6a2fa8921e81a21c7ec4fc86638b96fdfbe6adf9c11de
Q3 (Hnom, 180 s): 9a4dc76aca31e0cd333d27ab3fab461e42128896929e2b6afa62df88b37701e9
Q4 (Hnom, 600 s): 9b89f698bcb9031e939ac9b653480a2c164ff8cb5fc8956d2b8f947e1da4bcaf
Q5 (Hnom, 180 s): 2507c2c36030471676705b6589d8d783b419bbf3bd96ef4171caedd4ae298dae
Q6 (M, 180 s): 16b39342f932f42136802ec92947eaf2b2f102ce34e0013b7727e76fb11f7871

Native execution IS AUTHORIZED for Runner artmus208 only on:
Windows hostname: DESKTOP-Q3CKGDN; persistent local-drive checkout: <ABSOLUTE_WINDOWS_PATH>.
MachineGuid SHA256: 0a8584d7b2bebec97e47538eb32d6a04fdb5b396e953c8090759a2a99b208398
Native Python: C:\Users\musta\AppData\Local\Programs\Python\Python311\python.exe
Python SHA256: ff9b669828a66882f3d43ed2f9192ea9d8a08f80b8ffbc2186ee946823394418
Python version: 3.11.3 (tags/v3.11.3:f3909b8, Apr  4 2023, 23:49:59) [MSC v.1934 64 bit (AMD64)]
Windows PE verifyta: C:\Program Files (x86)\UPPAAL-5.0.0\bin\verifyta.exe
Executable SHA256: 4c8af2716ff61f3cf35c6d1dc408ccf306d44bb22478e104548a8f0f7a3febe5
Expected identity: UPPAAL 5.0.0 rev. 714BA9DB36F49691; capture actual full version and help once at session preflight. Mismatch halts without query.

Budget/method: six attempts maximum, no repeats, one native verifier, symbolic DFS -o 1 -t 0 -X <prefix> only after actual help confirms it; caps 180/180/180/600/180/180 s, total search allocation 1500 s, whole session 1800 s including preflight and cleanup. Memory floor(min(50% measured physical RAM,8 GiB)/MiB), using sampled sum of owned working sets; private commit is a separate reported metric.
Approve the independent monotonic Windows Job Object watchdog (atomic creation membership and KILL_ON_JOB_CLOSE), two-second cleanup margins, no status.json dependency, consumed interrupted reservations and stop policy in PROTOCOL.md.
Timeout/memory_limit has null verdict; continue only the next authorized slot within remaining budget. Error, monitor/watchdog/version/help mismatch, stop or overrun halts; remaining slots are not_executed. No extra native replay, simulation, smoke/control query or model/query change.

I delegate ONLY evidence/verification/uav-bounded-response-89/execution/** to Runner on codex/artmus208/89-uav-bounded-response-runs, including the exact approved execution/model.xml materialization. Its base is the exact approved preparation HEAD. Owner vadimnbkg suspends writes there until the durable Runner handoff returns the lease.
I acknowledge that my participation as Runner makes my evidence review producer review, not independent scientific acceptance. Independent acceptance remains pending a separate reviewer or explicitly recorded disposition; no person is invented.
No C02/P3/C06/Gate 2/R07 closure or manuscript edit is authorized.
```

If the scientific diagnostic-domain rationale is rejected, do not materialize or execute. Keep this proposal and all six null verdicts. A different restriction or budget needs a new explicit decision.
