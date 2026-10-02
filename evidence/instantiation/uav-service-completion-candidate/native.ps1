param([Parameter(Mandatory=$true)][string]$ConfigPath)
$ErrorActionPreference = 'Stop'
$cfg = Get-Content -Raw -LiteralPath $ConfigPath | ConvertFrom-Json
$campaign = [Diagnostics.Stopwatch]::StartNew()
$prior = [double]$cfg.prior_native_wall_seconds
$records = @()
$utf8 = New-Object Text.UTF8Encoding($false)
function SaveJson($path, $value) {
    [IO.File]::WriteAllText($path, ($value | ConvertTo-Json -Depth 16), $utf8)
}
SaveJson (Join-Path (Split-Path $cfg.summary) 'wrapper-owned.json') @(@{ id=$PID; start=(Get-Process -Id $PID).StartTime.ToUniversalTime().ToString('o') })
foreach ($cell in $cfg.cells) {
    if (($campaign.Elapsed.TotalSeconds+$prior) -gt 510) { throw 'Insufficient total wall reserve' }
    $os = Get-CimInstance Win32_OperatingSystem
    $cpu = Get-CimInstance Win32_Processor
    $free = [long]$os.FreePhysicalMemory * 1024
    if ($free -lt 3221225472) { throw 'Insufficient fresh native free RAM' }
    $hardware = @{ measured_utc=[DateTime]::UtcNow.ToString('o'); available_ram_bytes=$free;
        total_visible_ram_bytes=([long]$os.TotalVisibleMemorySize*1024);
        os=$os.Caption; os_version=$os.Version; cpu=@($cpu.Name); logical_cpu=($cpu | Measure-Object NumberOfLogicalProcessors -Sum).Sum }
    SaveJson $cell.hardware $hardware
    $proc = New-Object Diagnostics.Process
    $proc.StartInfo = New-Object Diagnostics.ProcessStartInfo
    $proc.StartInfo.FileName = $cfg.java
    $proc.StartInfo.Arguments = $cell.argument_string
    $proc.StartInfo.WorkingDirectory = $cfg.cwd
    $proc.StartInfo.UseShellExecute = $false
    $proc.StartInfo.CreateNoWindow = $true
    $proc.StartInfo.RedirectStandardOutput = $true
    $proc.StartInfo.RedirectStandardError = $true
    foreach ($name in @($proc.StartInfo.EnvironmentVariables.Keys)) {
        if ($name -like 'UPPAAL*' -or $name -in @('JAVA_TOOL_OPTIONS','_JAVA_OPTIONS','JDK_JAVA_OPTIONS')) { $proc.StartInfo.EnvironmentVariables.Remove($name) }
    }
    $started = [DateTime]::UtcNow
    $timer = [Diagnostics.Stopwatch]::StartNew()
    $owned = @{}
    $status = 'success'
    $peak = [long]0
    $samples = New-Object IO.StreamWriter($cell.memory, $false, $utf8)
    $samples.WriteLine('elapsed_seconds,pid,private_bytes,working_set_bytes,peak_working_set_bytes,tree_sample_bytes,cpu_seconds')
    try {
        if (-not $proc.Start()) { throw 'Java process did not start' }
        $owned[[int]$proc.Id] = $proc.StartTime.ToUniversalTime().ToString('o')
        SaveJson $cell.owned @(@{ id=$proc.Id; start=$owned[[int]$proc.Id] })
        $stdoutTask = $proc.StandardOutput.ReadToEndAsync()
        $stderrTask = $proc.StandardError.ReadToEndAsync()
        while (-not $proc.HasExited) {
            $all = @(Get-CimInstance Win32_Process | Select-Object ProcessId,ParentProcessId)
            # Discover descendants transitively; never inspect/kill unrelated processes.
            do {
                $added = $false
                foreach ($entry in $all) {
                    $id = [int]$entry.ProcessId
                    if ($owned.ContainsKey([int]$entry.ParentProcessId) -and -not $owned.ContainsKey($id)) {
                        $child = Get-Process -Id $id -ErrorAction SilentlyContinue
                        if ($child) { $owned[$id]=$child.StartTime.ToUniversalTime().ToString('o'); $added=$true }
                    }
                }
            } while ($added)
            $identities=@(); foreach($id in @($owned.Keys)) { $identities+=@{ id=$id; start=$owned[$id] } }
            SaveJson $cell.owned $identities
            $rows = @(); $tree = [long]0
            foreach ($id in @($owned.Keys)) {
                $child = Get-Process -Id $id -ErrorAction SilentlyContinue
                if ($child -and $child.StartTime.ToUniversalTime().ToString('o') -eq $owned[$id]) {
                    $measure=[Math]::Max($child.PrivateMemorySize64,[Math]::Max($child.WorkingSet64,$child.PeakWorkingSet64))
                    $tree += $measure
                    $rows += ,@($id,$child.PrivateMemorySize64,$child.WorkingSet64,$child.PeakWorkingSet64,$child.TotalProcessorTime.TotalSeconds)
                }
            }
            $peak=[Math]::Max($peak,$tree)
            foreach ($row in $rows) { $samples.WriteLine(('{0},{1},{2},{3},{4},{5},{6}' -f $timer.Elapsed.TotalSeconds.ToString('R',[Globalization.CultureInfo]::InvariantCulture),$row[0],$row[1],$row[2],$row[3],$tree,$row[4].ToString('R',[Globalization.CultureInfo]::InvariantCulture))) }
            $samples.Flush()
            if ($tree -ge 2147483648) { $status='memory_limit'; break }
            if ($timer.Elapsed.TotalSeconds -ge 60 -or ($campaign.Elapsed.TotalSeconds+$prior) -ge 585) { $status='timeout'; break }
            Start-Sleep -Milliseconds 100
            $proc.Refresh()
        }
    } finally {
        $samples.Dispose()
        if (-not $proc.HasExited) { & taskkill.exe /PID $proc.Id /T /F 2>$null | Out-Null }
        if (-not $proc.WaitForExit(5000)) { throw 'Java process not reaped' }
        # Identity checks avoid killing a reused PID.
        foreach ($id in @($owned.Keys)) {
            $child=Get-Process -Id $id -ErrorAction SilentlyContinue
            if ($child -and $child.StartTime.ToUniversalTime().ToString('o') -eq $owned[$id]) {
                Stop-Process -Id $id -Force
                if (-not $child.WaitForExit(5000)) { throw 'Engine descendant not reaped' }
            }
        }
    }
    [IO.File]::WriteAllText($cell.stdout, $stdoutTask.GetAwaiter().GetResult(), $utf8)
    [IO.File]::WriteAllText($cell.stderr, $stderrTask.GetAwaiter().GetResult(), $utf8)
    $row = @{ run_id=$cell.run_id; mode=$cell.mode; native_status=$status; exit_code=$proc.ExitCode;
        started_utc=$started.ToString('o'); finished_utc=[DateTime]::UtcNow.ToString('o'); runtime_seconds=$timer.Elapsed.TotalSeconds;
        peak_tree_sample_bytes=$peak; owned_process_identities=$identities; process_tree_reaped=$true;
        timeout_seconds=60; memory_limit_bytes=2147483648; requested_sleep_ms=100; command=$cell.command }
    SaveJson $cell.monitor $row
    $records += $row
    SaveJson $cfg.summary @{ cells=$records; total_wall_seconds=($campaign.Elapsed.TotalSeconds+$prior); prior_native_wall_seconds=$prior; total_limit_seconds=600 }
    if ($status -ne 'success' -or $proc.ExitCode -notin @(0,1)) { break }
    $outcome=Get-Content -Raw -LiteralPath $cell.result | ConvertFrom-Json
    if ($cell.mode -eq 'replay' -and $outcome.status -ne 'replay_complete') { break }
    if ($cell.mode -like 'negative-*' -and -not $outcome.control_expected_rejection) { break }
}
if (($campaign.Elapsed.TotalSeconds+$prior) -gt 600) { throw 'Total native campaign wall exceeded' }
