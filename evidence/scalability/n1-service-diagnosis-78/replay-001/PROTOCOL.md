# Directed timed replay — Issue #78

User authorization: «давай сделаем» on 2026-10-02, following the explicit
proposal to automate the saved XTR using the installed engine. This continues
the existing diagnostic deliverable. Exact contract is recorded in Issue #78.

Read-only baseline model SHA256:
5234cb087e5274798926d516dedc77d1f9542ea7df59cec39f83859771ce1385.
Read-only manual-001/05-service-before-overflow.xtr SHA256:
8186e1b68324ba288abe6249abdc73fa771400d95414d4bf77d2d1f9fdfbfcf7.
Parent input checkpoint: b403fd3903b1d9f925cb51382ba5433810612f99.

Only replay-001/** may change. Inputs and historical indexes remain unchanged.
Java API computes enabled symbolic successors from an engine initial state.
Saved discrete state and edge/select identities must match. Reachable zones
are intersected with saved zones, closed, and checked for emptiness before
continuing, so a later step cannot restart from an arbitrary imported state.
A nonempty intersection establishes one feasible execution through the stored
zones; it does not establish equality of all zones or a formal query verdict.

Native campaign: at most three engine invocations, replay and two fixed
negative controls; 60s/invocation, Java heap512MiB, sampled tree2GiB stop,
fresh free RAM3GiB. Total300s including metadata/probes/cleanup. No exhaustive
query, plain-DBM experiment, retry or strategy sweep. Error/timeout inconclusive.
Controls alter only an expected final integer or final clock zone, never XML.
Compile/parser/DBM unit checks invoke no engine.

## Readiness correction before timed replay

native-001 captured actual server version, then the old API URI loader dropped
the UNC host. No model compilation or transitions occurred (zero events).
The failure and cleanup are retained. Offline --model-test now loads all50
templates. native-002 is the first actual timed replay campaign; its300s native
execution allowance carries forward the2.2721119s readiness cost. Development
while the failed invocation is stopped is recorded separately from native
execution cost. Maximum3 actual replay/control invocations, no search retry.

Exact command: python3 -B evidence/scalability/n1-service-diagnosis-78/replay-001/run_replay.py --execute
The script records expanded Windows commands/configuration before each launch.
Each run uses installed JDK17 with -Xmx512m and -Djava.awt.headless=true;
TimedReplay SERVER MODEL TRACE OUTPUT MODE, MODE in replay/negative-discrete/
negative-clock. Java heap bound is separate from native sampled process-tree
memory threshold. The two controls replace only the final expected grant or
expected zone (shared_load.tick=1; the real service edge resets it to0).
