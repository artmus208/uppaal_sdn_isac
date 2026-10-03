# Native Windows execution design and preparation evidence

The user correction recorded in [#89](https://github.com/artmus208/uppaal_sdn_isac/issues/89#issuecomment-5968685095)
supersedes Linux selection. Linux preparation commit
`9e4743bfcca06416c112693d8644ecec004a0a8f` remains an ancestor. This correction
is authorization to prepare and test synthetic processes, not to execute UPPAAL.

## Bindings checked before any native campaign command

`windows_native.identity()` rejects non-Windows Python. Approval binds computer
name, SHA256 of Windows MachineGuid (not its raw value), Python absolute path,
PE SHA256 and exact Python version. `driver.verify_native_inputs()` also binds
the persistent local-drive checkout and rejects UNC/WSL/temp locations. Native
identity was observed on Windows 10 build 19045, DESKTOP-Q3CKGDN, Python 3.11.3
AMD64. See `checks/windows-004/record.json` for exact hardware/RAM/identity.

The user-selected verifier is
`C:\Program Files (x86)\UPPAAL-5.0.0\bin\verifyta.exe`, SHA256
`4c8af2716ff61f3cf35c6d1dc408ccf306d44bb22478e104548a8f0f7a3febe5`.
Read-only inspection checks MZ, PE signature, executable/not-DLL characteristic,
x86/x64 machine and matching PE32/PE32+ header, then hashes every byte. No `-v`,
`-h` or query has been executed. Historical expected UPPAAL identity still needs
actual observation after approval.

Windows text reads explicitly use UTF-8. Scope `.gitattributes` disables byte
conversion; the native clone additionally disables core.autocrlf before checkout
so upstream pinned inputs retain their original bytes. The initial Windows generic
suite exposed three codepage errors; their raw failure log remains in
`checks/windows-001`. Final tests repeat both generic and Windows suites.

## Ownership and stopping

Each attempt gets a fresh unnamed Job Object, whose sole non-inheritable handle
belongs to the independent multiprocessing-spawn watchdog. The limit is
KILL_ON_JOB_CLOSE with no breakaway allowance. `CreateProcessW` uses STARTUPINFOEX
JOB_LIST to assign membership atomically at creation, CREATE_SUSPENDED and an
explicit HANDLE_LIST containing only stdin/stdout/stderr. Thus there is no
unowned launch/AssignProcess interval. After the controller acknowledges the
owned PID, the watchdog checks its monotonic deadline and resumes the thread.

Children and grandchildren stay in the job, including children using a different
process group. A completed console leader may leave its owned conhost briefly alive. A 250 ms
natural-exit grace stays inside the existing command deadline; surviving children
still cause error and cleanup. No executable name is exempted. The synthetic
probe confirmed conhost in `checks/windows-003/fast-exit-probe2.jsonl`.

Normal stop/deadline/memory/monitor errors call TerminateJobObject
and check ActiveProcesses=0. Watchdog death closes the last job handle, which
kills owned processes even before ResumeThread. Controller death is detected
using a retained process handle (no PID-reuse lookup), or pipe EOF. No process
name, external status file or Linux process group controls termination.

The watchdog ignores terminal Ctrl-C; the controller handles it and requests
stop. A blocked/dead controller cannot stop deadline monitoring. No telemetry
filesystem writes or large pipe sends occur while children are running. At most
one sample per 50 ms is buffered, bounded by the 1800-second session. The full
sample list is sent only after cleanup; controller fsync/write errors halt the
series. Abrupt watchdog death may lose that attempt's metrics; the controller
records an error/unknown cleanup, never fabricates confirmation or a verdict.

Both per-attempt and whole-session deadlines reserve two seconds for production
cleanup. Windows scheduling/OS/API stalls are not a hard realtime guarantee;
measured overruns remain errors and stop further slots. Kill-on-close protects
ownership during crashes, but does not promise log durability or a verdict.

## Native measurements

GlobalMemoryStatusEx supplies physical RAM. The memory threshold remains
floor(min(RAM/2,8 GiB)/MiB) MiB. Toolhelp enumerates pre-existing verifyta names
for refusal only. QueryInformationJobObject enumerates owned PIDs; retained
OpenProcess handles plus IsProcessInJob avoid counting a reused foreign PID.
GetProcessMemoryInfo supplies working sets; their sampled sum controls memory
stop. CPU comes from cumulative job accounting, including exited descendants.

`peak_rss_bytes` is max(sampled sum of working sets, retained leader's kernel peak
working set). It can miss short-lived descendant peaks and may double-count shared
pages. `peak_job_private_commit_bytes` is Windows job peak private commit,
reported separately, never relabeled RSS. Sampling is not a hard allocation cap.
Failure to monitor a live owned process halts and cleans the job.

JSON writes flush/fsync the temporary file and use MoveFileExW with
REPLACE_EXISTING | WRITE_THROUGH. Failures preserve the old record and halt;
watchdog deadlines do not depend on the JSON files being readable or writable.

## Windows software checks and primary references

`run_windows_checks.py` executes all scoped tests on real native Windows and
records exact Python/host/PE/source hashes, source commit, counts and raw unittest
log. There is no verifier invocation. Tests cover three-generation cleanup and
unrelated-process survival, limits/stop, leader exit with live children, denied
breakaway, controller EOF/death/blockage, watchdog death both before resume and
with live descendants, monitor/telemetry failures, paths with spaces/quotes,
native approval identity, PE format, atomic write failure and unchanged models,
restrictions, formulas and fail-closed parsing. Linux skips are never substituted
for a Windows test result.

Implementation contracts: Microsoft [Job Objects](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects),
[process attributes (JOB_LIST/HANDLE_LIST)](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-updateprocthreadattribute),
[job queries](https://learn.microsoft.com/en-us/windows/win32/api/jobapi2/nf-jobapi2-queryinformationjobobject),
[extended job limits](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_extended_limit_information),
[process memory](https://learn.microsoft.com/en-us/windows/win32/api/psapi/nf-psapi-getprocessmemoryinfo)
and [physical RAM](https://learn.microsoft.com/en-us/windows/win32/api/sysinfoapi/nf-sysinfoapi-globalmemorystatusex).
