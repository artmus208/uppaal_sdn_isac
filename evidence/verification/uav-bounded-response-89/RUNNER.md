# Runner artmus208: native Windows handoff

Preparation only. Do not execute verifyta, including `-v` or `-h`, until artmus208
posts the explicit decision for the NEW preparation HEAD in #89. The Linux
preparation at `9e4743bfcca06416c112693d8644ecec004a0a8f` is historical; it is not
the execution checkpoint. Current Hnom is still an unmaterialized proposal.

Use Windows 10+ x64, Windows PowerShell, native Git for Windows and the recorded
Windows Python 3.11.3. WSL/Linux Python and UNC/WSL campaign checkouts are rejected.
Synthetic tests were launched from WSL using native Windows Python; all tested
children and Job Objects were native Windows, with Windows temporary directories.
The campaign itself must use a persistent local Windows drive clone.

## Recover the exact accepted preparation

Use your own credentials and Git identity. Replace the two placeholders before
running; the checkout path must be persistent, dedicated and initially absent.

```powershell
$Preparation = '<EXACT_NEW_PREPARATION_HEAD_ACCEPTED_IN_89>'
$Checkout = 'C:\Users\musta\source\uppaal-issue89'
$Python = 'C:\Users\musta\AppData\Local\Programs\Python\Python311\python.exe'
$Verifier = 'C:\Program Files (x86)\UPPAAL-5.0.0\bin\verifyta.exe'
$Scope = 'evidence/verification/uav-bounded-response-89'
$env:PYTHONDONTWRITEBYTECODE = '1'
git -c core.autocrlf=false clone --no-checkout https://github.com/artmus208/uppaal_sdn_isac.git $Checkout
Set-Location $Checkout
git config core.autocrlf false
git fetch origin codex/vadimnbkg/89-uav-bounded-response
git switch -c codex/artmus208/89-uav-bounded-response-runs $Preparation
git status --short --branch
git rev-parse HEAD
git remote -v
```

Stop after any failed command; PowerShell does not automatically stop on native
nonzero exit codes. Confirm exact HEAD and canonical origin. A full published
Owner bundle can replace the clone/fetch; restore canonical origin afterwards.
Disabling CRLF conversion before checkout preserves historical input hashes.
Scope `.gitattributes` additionally preserves exact preparation/evidence bytes.

## Approval, lease and offline controls

Read `PROTOCOL.md`, `WINDOWS.md`, `proposed-decision.md` and the saved Windows test
record. Approve Hnom restrictions/materialization separately from native execution
in the same explicit Issue decision. Fill the accepted preparation HEAD and actual
persistent checkout path; all host/Python/binary bindings are in
`approval-template.json`. A changed binding requires a new concrete decision.

Only the decision activates Runner's sequential write lease for `execution/**`.
Owner suspends writes there. The following controls are offline and consume no
query slots, but run them before materialization (one test checks its absence):

```powershell
& $Python -B "$Scope/windows_native.py"
Get-FileHash -Algorithm SHA256 -LiteralPath $Verifier
& $Python -B "$Scope/prepare.py" --check
& $Python -B "$Scope/audit.py"
& $Python -B "$Scope/run_windows_checks.py" --output "$Scope/execution/software-controls" --source-commit (git rev-parse HEAD)
```

Require zero failures, zero errors and zero skips; inspect `record.json` and
`unittest.txt`. The process tests run synthetic Python children only. The test
runner reads PE bytes/hash and host identity without invoking verifyta. On any
failure, preserve logs and return to Owner before any campaign launch.

Copy `approval-template.json` to `execution/approval.json`. Record the actual
Issue decision URL/accepted HEAD/checkout and set both approval booleans true
only to transcribe that decision. Save its exact text at `execution/decision.md`.
JSON is not authentication: Reviewer checks the actual GitHub author and decision.
No verifier version is inferred from its hash; the version remains unobserved.

```powershell
& $Python -B "$Scope/driver.py" materialize --approval "$Scope/execution/approval.json"
git add -- "$Scope/execution"
git commit -m 'P3: record approved Windows host and materialize Hnom (#89)'
git status --short --branch
git log -1 --oneline --decorate
git remote -v
git push -u origin codex/artmus208/89-uav-bounded-response-runs
```

Materialization is offline and validates the approval, native host/Python identity,
PE format/path/hash, preparation seal and exact derived model. Publish this clean
checkpoint or export/verify its full bundle in persistent `execution/recovery/`
before starting. Do not launch from uncommitted inputs.

## One authorized native session

Run in a dedicated terminal. The driver requires a clean tree; do not redirect
its console to an uncommitted file inside the checkout before launch.

```powershell
& $Python -B "$Scope/driver.py" run --approval "$Scope/execution/approval.json"
```

There is no retry/resume. Do not delete session claims, reclaim interrupted slots
or change formulas. Do not start another verifier on this host. Existing native
verifyta processes are detected through Toolhelp and cause refusal; never kill them.

Stop with Ctrl-C in the campaign terminal. If that controller is unresponsive,
terminate **only its recorded PID**, after confirming it is the campaign Python
process (use a separate PowerShell terminal):

```powershell
$Claim = Get-Content -Raw "$Scope/execution/session-claimed.json" | ConvertFrom-Json
$ControllerPid = [int]$Claim.pid
Get-Process -Id $ControllerPid
# Only after confirming that exact owned controller:
Stop-Process -Id $ControllerPid
```

Do not use PowerShell's reserved `$PID` as a variable or kill by process name.
The watchdog detects controller death through its retained process handle;
closing the controller pipe also stops the attempt. If the watchdog itself dies,
Windows closes its sole Job Object handle and terminates the entire owned tree.
The watchdog never reads `status.json`/claim JSON. These instructions use the
claim only to help the human select the correct controller.

Deadlines include cleanup margins: 180/180/180/600/180/180 seconds, 1500 total
search allocation, 1800 whole native session including -v/-h and cleanup.
Timeout/memory stop has null verdict; only later authorized slots may continue.
Error, monitor/watchdog/disk/checkpoint failure, explicit stop or budget overrun
halts the series. Preserve available logs; an abrupt stop may leave an interrupted
reservation and absent telemetry, which must stay unknown.

The controller commits each consumed reservation before starting it and saves a
full-history bundle in persistent `execution/recovery/`. Results get their own
checkpoint/bundle. Job CPU includes exited descendants; peak working-set memory
and private commit are distinct metrics. Telemetry is buffered by the independent
watchdog and written after owned cleanup, so disk/controller blockage cannot keep
a running verifier past the watchdog deadline. See `WINDOWS.md` for exact limits.

## Durable return to Owner

```powershell
& $Python -B "$Scope/audit.py" --output "$Scope/execution/offline-audit.json"
git diff --check
git add -- "$Scope/execution"
git commit -m 'P3: record native Windows offline audit (#89)'
git status --short --branch
git log -1 --oneline --decorate
git remote -v
git push -u origin codex/artmus208/89-uav-bounded-response-runs
```

On failed push, after those status/log/remote checks export a complete final bundle:
`git bundle create "$Scope/execution/recovery/final.bundle" codex/artmus208/89-uav-bounded-response-runs`.
Run `git bundle verify` and `Get-FileHash -Algorithm SHA256`; record its persistent
Owner-accessible location. Never force-push or erase execution commits.

Post in #89: exact Runner HEAD and accepted preparation base, clean/dirty state,
six statuses/verdicts/model/query hashes, actual version and executable hash,
budget/stop deviations, raw paths, durable retrieval and explicit return of the
write lease. Owner assembles results in the same PR #90. Runner's review is
producer review; independent scientific acceptance remains separate.
