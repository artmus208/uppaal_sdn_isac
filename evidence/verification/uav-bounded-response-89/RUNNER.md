# Runner artmus208: Linux handoff

Do not run verifyta (including -v/-h) before the explicit native decision in #89.
`proposed-decision.md` identifies the exact inputs. Supply hostname, persistent
clone path, ELF verifier path and SHA256 without executing verifyta. Confirm
Linux Python >=3.10 and a readable native /proc. Use your own account/credentials.
Current preparation has no native execution permission and no saved derived XML.

## Recover the accepted preparation

Replace PREPARATION_HEAD with the exact published handoff commit accepted in #89.
Use a persistent directory owned by Runner, not /tmp. The normal retrieval is:

```bash
git clone https://github.com/artmus208/uppaal_sdn_isac.git /absolute/persistent/issue89
cd /absolute/persistent/issue89
git fetch origin codex/vadimnbkg/89-uav-bounded-response
git switch -c codex/artmus208/89-uav-bounded-response-runs PREPARATION_HEAD
git status --short --branch
git rev-parse HEAD
git remote -v
```

If branch publication is unavailable, clone the complete Owner handoff bundle,
then set origin to the canonical URL above. Confirm the exact preparation SHA.
Set your real local Git identity. Runner may write only `execution/**` inside this
package, after the recorded sequential lease; do not edit the prepared sources.

## Offline setup before native session

These commands execute Python software controls only:

```bash
export PYTHONDONTWRITEBYTECODE=1
scope=evidence/verification/uav-bounded-response-89
python3 -B "$scope/prepare.py" --check
python3 -B "$scope/audit.py"
mkdir -p "$scope/execution"
python3 -B -m unittest discover -s "$scope" -p 'test_*.py' -v > "$scope/execution/native-software-tests.stdout.txt" 2> "$scope/execution/native-software-tests.stderr.txt"
hostname
python3 --version
sha256sum /absolute/path/to/verifyta
```

All software tests must succeed on the actual Runner host. They create only
synthetic Python children in temporary directories and do not consume query slots.
Read the test logs. If an offline check fails, stop and return it to Owner; no
native session has started. Do not run the proposal test that asserts model
absence after materialization; finish these controls first.

After artmus208 has posted the concrete decision, copy `approval-template.json`
to `execution/approval.json`, fill the exact accepted fields, set both approval
booleans true only to record the actual decision, and save its exact text at
`execution/decision.md`. The JSON is a local transcription, not an authentication
mechanism; Reviewer checks the actual GitHub decision and author/authority.

```bash
python3 -B "$scope/driver.py" materialize --approval "$scope/execution/approval.json"
git add -- "$scope/execution"
git commit -m 'P3: record approved host and materialize Hnom (#89)'
git status --short --branch
git log -1 --oneline --decorate
git remote -v
git push -u origin codex/artmus208/89-uav-bounded-response-runs
```

`materialize` is offline: it checks approval, ELF bytes/hash, host, preparation
seal and exact model bytes; it does not execute the verifier. Run from a clean
tree after the materialized inputs and decision are committed and durable.

## One native session only

Run in a dedicated terminal. Do not redirect console output into an uncommitted
file before launch, because the driver requires a clean source tree.

```bash
python3 -B "$scope/driver.py" run --approval "$scope/execution/approval.json"
```

There is no retry/resume command. Do not delete session claims or reuse consumed
slots. The driver refuses a prior session and checks for an existing native
verifyta process. Another verifier must not be started concurrently on this host.

Stop: Ctrl-C in that terminal (SIGINT), or `kill -TERM CONTROLLER_PID` for the
PID saved in `execution/session-claimed.json`. Do not use pkill/killall or signal
unowned processes. The watchdog holds its own monotonic deadlines and knows each
owned group through a pipe, independently of JSON readability. On any watchdog,
monitor, disk or checkpoint failure, halt the series and preserve available files.

The driver reserves each slot in the durable ledger and commits it before exec;
exports a complete-history bundle under `execution/recovery/`; then saves raw
logs/telemetry/traces and commits/exports the result. Recovery bundles are ignored
by Git to avoid recursively archiving themselves, but remain inside the allowed
execution scope in the persistent clone. Initial/source/result commits remain
reachable from the final branch. Never force-push or rewrite execution history.

## Durable return to Owner

```bash
python3 -B "$scope/audit.py" --output "$scope/execution/offline-audit.json"
git diff --check
git add -- "$scope/execution"
git commit -m 'P3: record native offline audit (#89)'
git status --short --branch
git log -1 --oneline --decorate
git remote -v
git push -u origin codex/artmus208/89-uav-bounded-response-runs
```

If push fails, export a final full bundle after those three pre-export checks:
`git bundle create "$scope/execution/recovery/final.bundle" codex/artmus208/89-uav-bounded-response-runs`.
Record bundle SHA256 and its persistent owner-accessible location. Verify it with
`git bundle verify`. Do not call a local-only temporary commit a durable handoff.

Post in #89: exact Runner HEAD, accepted preparation/execution base, clean/dirty,
each slot's status/verdict/model/query hashes, actual tool version/binary hash,
budget/stop deviations, raw evidence paths, branch or bundle retrieval, and
explicit return of the execution write lease to Owner. This reports production;
it is not independent scientific acceptance. Do not open a competing final PR.
