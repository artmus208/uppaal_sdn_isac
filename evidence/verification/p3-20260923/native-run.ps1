param([Parameter(Mandatory=$true)][string]$Config)
$ErrorActionPreference='Stop'
$c=Get-Content -Raw -LiteralPath $Config | ConvertFrom-Json
$info=New-Object System.Diagnostics.ProcessStartInfo
$info.FileName=$c.executable
$info.Arguments=($c.arguments | ForEach-Object { '"'+($_ -replace '"','\"')+'"' }) -join ' '
$info.WorkingDirectory=Split-Path -Path $c.executable -Parent
$info.UseShellExecute=$false
$info.RedirectStandardOutput=$true
$info.RedirectStandardError=$true
foreach($key in @($info.EnvironmentVariables.Keys)) { if($key -like 'UPPAAL_*') {$info.EnvironmentVariables.Remove($key)} }
$p=New-Object System.Diagnostics.Process
$p.StartInfo=$info
$watch=[Diagnostics.Stopwatch]::StartNew()
$started=[DateTime]::UtcNow.ToString('o')
[void]$p.Start()
$out=$p.StandardOutput.ReadToEndAsync();$err=$p.StandardError.ReadToEndAsync()
$peak=0L;$privatePeak=0L;$reason='completed'
while(-not $p.WaitForExit(50)) {
 $p.Refresh()
 $peak=[Math]::Max($peak,$p.PeakWorkingSet64)
 $privatePeak=[Math]::Max($privatePeak,$p.PrivateMemorySize64)
 if($watch.Elapsed.TotalSeconds -ge $c.timeout_seconds) {$reason='timeout';$p.Kill();break}
 if($p.WorkingSet64 -gt $c.memory_stop_bytes) {$reason='memory_limit';$p.Kill();break}
}
$p.WaitForExit();$watch.Stop()
try {$p.Refresh();$peak=[Math]::Max($peak,$p.PeakWorkingSet64)} catch {}
$encoding=New-Object System.Text.UTF8Encoding($false)
[IO.File]::WriteAllText($c.stdout,$out.GetAwaiter().GetResult(),$encoding)
[IO.File]::WriteAllText($c.stderr,$err.GetAwaiter().GetResult(),$encoding)
$r=@{started_at_utc=$started;finished_at_utc=[DateTime]::UtcNow.ToString('o');runtime_seconds=$watch.Elapsed.TotalSeconds;exit_code=$p.ExitCode;termination=$reason;peak_working_set_bytes=$peak;sampled_peak_private_bytes=$privatePeak;native_process_id=$p.Id;timeout_seconds=$c.timeout_seconds;memory_stop_bytes=$c.memory_stop_bytes;memory_measurement='Windows Process.PeakWorkingSet64, observed every 50ms; private bytes sampled. Stop threshold is not a hard allocation cap.'}
[IO.File]::WriteAllText($c.result,($r|ConvertTo-Json -Depth 5),$encoding)
