# Native Windows process accounting. The limit is a sampled stop threshold,
# not a kernel allocation cap; measured overshoot and sample gaps are retained.
param([Parameter(Mandatory=$true)][string]$ConfigPath)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
$utf8 = New-Object System.Text.UTF8Encoding($false)
$c = Get-Content -LiteralPath $ConfigPath -Raw -Encoding UTF8 | ConvertFrom-Json
function Save-Json($value, [string]$path) {
    [IO.File]::WriteAllText($path, ($value | ConvertTo-Json -Depth 16), $utf8)
}
function Read-Memory($process) {
    $process.Refresh()
    [ordered]@{
        private_bytes = [long]$process.PrivateMemorySize64
        working_set_bytes = [long]$process.WorkingSet64
        peak_working_set_bytes = [long]$process.PeakWorkingSet64
    }
}
# This probe must succeed before any verifier process is created.
$self = [Diagnostics.Process]::GetCurrentProcess()
$probe = Read-Memory $self
if ($probe.private_bytes -le 0 -or $probe.working_set_bytes -le 0) {
    throw 'Native Windows process memory accounting unavailable; refusing launch'
}
if ($c.mode -eq 'probe') {
    $os = Get-CimInstance Win32_OperatingSystem
    $cpu = @(Get-CimInstance Win32_Processor)
    Save-Json ([ordered]@{
        os = $os.Caption; os_version = $os.Version; os_build = $os.BuildNumber
        total_physical_ram_bytes = [long]$os.TotalVisibleMemorySize * 1024
        available_physical_ram_bytes = [long]$os.FreePhysicalMemory * 1024
        cpu_models = @($cpu | ForEach-Object { $_.Name })
        logical_cpu_count = ($cpu | Measure-Object NumberOfLogicalProcessors -Sum).Sum
        powershell_version = $PSVersionTable.PSVersion.ToString()
        dotnet_version = [Environment]::Version.ToString()
        measured_at_utc = [DateTime]::UtcNow.ToString('o')
        memory_probe = $probe
        memory_measure = 'max(PrivateMemorySize64, WorkingSet64, PeakWorkingSet64), native Windows target process'
    }) $c.result
    exit 0
}
if ($c.mode -ne 'run') { throw 'Unknown monitor mode' }
if ($c.timeout_seconds -le 0 -or $c.timeout_seconds -gt 60) { throw 'Timeout outside (0,60]' }
if ($c.memory_limit_bytes -le 0 -or $c.memory_limit_bytes -gt 2147483648) { throw 'Memory threshold outside (0,2GiB]' }
if ($c.sample_interval_ms -lt 1 -or $c.sample_interval_ms -gt 50) { throw 'Sample interval outside [1,50]ms' }
$info = New-Object Diagnostics.ProcessStartInfo
$info.FileName = $c.executable
$info.Arguments = $c.arguments_windows
$info.WorkingDirectory = $c.cwd
$info.UseShellExecute = $false
$info.CreateNoWindow = $true
$info.RedirectStandardOutput = $true
$info.RedirectStandardError = $true
# Refuse inherited UPPAAL feature switches that would silently alter the model/search.
foreach ($key in @($info.EnvironmentVariables.Keys)) {
    if ($key.StartsWith('UPPAAL_')) { $info.EnvironmentVariables.Remove($key) }
}
if ($c.compile_only) { $info.EnvironmentVariables['UPPAAL_COMPILE_ONLY'] = '1' }
$p = New-Object Diagnostics.Process
$p.StartInfo = $info
$result = [ordered]@{
    status = 'monitor_error'; exit_code = $null; process_id = $null
    started_at_utc = $null; finished_at_utc = $null; runtime_seconds = 0
    timeout_seconds = [double]$c.timeout_seconds
    memory_limit_bytes = [long]$c.memory_limit_bytes
    sample_interval_ms = [int]$c.sample_interval_ms
    memory_measure = 'max(PrivateMemorySize64, WorkingSet64, PeakWorkingSet64)'
    enforcement = 'sampled stop threshold, not a hard allocation cap; target process only'
    samples = 0; maximum_sample_gap_seconds = 0.0
    peak_private_bytes = 0; peak_working_set_bytes = 0; peak_reported_working_set_bytes = 0
    cpu_seconds = $null; measured_memory_overshoot_bytes = 0
    kill_tree_requested = $false; process_reaped = $false
    error = $null; command = @($c.executable) + @($c.arguments)
    cwd = $c.cwd; compile_only = [bool]$c.compile_only
}
$so = $null; $se = $null; $samples = $null; $watch = $null
try {
    $so = [IO.File]::Open($c.stdout, [IO.FileMode]::CreateNew)
    $se = [IO.File]::Open($c.stderr, [IO.FileMode]::CreateNew)
    $samples = New-Object IO.StreamWriter($c.samples, $false, $utf8)
    $samples.WriteLine('elapsed_seconds,private_bytes,working_set_bytes,peak_working_set_bytes')
    $result.started_at_utc = [DateTime]::UtcNow.ToString('o')
    $watch = [Diagnostics.Stopwatch]::StartNew()
    if (-not $p.Start()) { throw 'Process did not start' }
    $result.process_id = $p.Id
    Save-Json $result $c.result  # PID survives a monitor/driver watchdog failure.
    # Drain both byte streams concurrently to files; no pipe deadlock or large buffer.
    $stdoutTask = $p.StandardOutput.BaseStream.CopyToAsync($so)
    $stderrTask = $p.StandardError.BaseStream.CopyToAsync($se)
    $lastSample = 0.0
    while (-not $p.HasExited) {
        try { $memory = Read-Memory $p } catch {
            if ($p.HasExited) { break }
            throw
        }
        $elapsed = $watch.Elapsed.TotalSeconds
        $result.maximum_sample_gap_seconds = [Math]::Max([double]$result.maximum_sample_gap_seconds, [double]($elapsed - $lastSample))
        $lastSample = $elapsed
        $result.samples++
        $result.peak_private_bytes = [Math]::Max([long]$result.peak_private_bytes, [long]$memory.private_bytes)
        $result.peak_working_set_bytes = [Math]::Max([long]$result.peak_working_set_bytes, [long]$memory.working_set_bytes)
        $result.peak_reported_working_set_bytes = [Math]::Max([long]$result.peak_reported_working_set_bytes, [long]$memory.peak_working_set_bytes)
        $samples.WriteLine(('{0},{1},{2},{3}' -f $elapsed.ToString('F6', [Globalization.CultureInfo]::InvariantCulture), $memory.private_bytes, $memory.working_set_bytes, $memory.peak_working_set_bytes))
        $samples.Flush()
        $measured = [Math]::Max([long]$memory.private_bytes, [Math]::Max([long]$memory.working_set_bytes, [long]$memory.peak_working_set_bytes))
        if ($measured -ge $c.memory_limit_bytes) {
            $result.status = 'memory_limit'
            $result.measured_memory_overshoot_bytes = $measured - $c.memory_limit_bytes
            break
        }
        if ($elapsed -ge $c.timeout_seconds) { $result.status = 'timeout'; break }
        Start-Sleep -Milliseconds $c.sample_interval_ms
    }
    if ($p.HasExited -and $result.status -eq 'monitor_error') {
        $result.exit_code = $p.ExitCode
        $result.status = if ($p.ExitCode -eq 0) { 'success' } else { 'error' }
    }
} catch {
    $result.status = 'monitor_error'
    $result.error = $_.Exception.Message
} finally {
    if ($result.process_id -and -not $p.HasExited) {
        $result.kill_tree_requested = $true
        # taskkill terminates descendants as well; Kill is a fallback for the root.
        try { & "$env:SystemRoot\System32\taskkill.exe" /PID $p.Id /T /F 2>&1 | Out-Null } catch {}
        if (-not $p.WaitForExit(2000)) { $p.Kill() }
    }
    if ($result.process_id) {
        $result.process_reaped = $p.WaitForExit(2000)
        if (-not $result.process_reaped) { $result.status = 'monitor_error'; $result.error = 'Process not reaped' }
        if ($result.process_reaped) {
            $result.exit_code = $p.ExitCode
            try { $result.cpu_seconds = $p.TotalProcessorTime.TotalSeconds } catch {}
        }
    }
    if ($watch) { $result.runtime_seconds = $watch.Elapsed.TotalSeconds }
    $result.finished_at_utc = [DateTime]::UtcNow.ToString('o')
    if ($result.process_id) {
        foreach ($task in @($stdoutTask, $stderrTask)) {
            if ($task -and -not $task.Wait(2000)) { $result.status = 'monitor_error'; $result.error = 'Output drain did not finish' }
        }
    }
    if ($so) { $so.Dispose() }; if ($se) { $se.Dispose() }; if ($samples) { $samples.Dispose() }
    if ($result.samples -eq 0 -or $result.peak_private_bytes -le 0 -or $result.peak_reported_working_set_bytes -le 0) {
        $result.status = 'monitor_error'
        $result.error = 'No valid target-process memory measurement; verdict unusable'
    }
    Save-Json $result $c.result
    $p.Dispose()
}
if ($result.status -eq 'monitor_error') { exit 2 }
exit 0
