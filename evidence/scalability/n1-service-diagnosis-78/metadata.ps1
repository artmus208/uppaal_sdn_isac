# Version/help only. Native PID ownership and timeout; no memory-sample requirement.
param([Parameter(Mandatory=$true)][string]$ConfigPath)
$ErrorActionPreference='Stop'
$ProgressPreference='SilentlyContinue'
$utf8=New-Object System.Text.UTF8Encoding($false)
$c=Get-Content -LiteralPath $ConfigPath -Raw -Encoding UTF8 | ConvertFrom-Json
function Save($v) { [IO.File]::WriteAllText($c.result,($v|ConvertTo-Json -Depth 12),$utf8) }
if ($c.timeout_seconds -ne 10) { throw 'Metadata timeout must be 10 seconds' }
$p=New-Object Diagnostics.Process
$i=New-Object Diagnostics.ProcessStartInfo
$i.FileName=$c.executable; $i.Arguments=$c.arguments_windows; $i.WorkingDirectory=$c.cwd
$i.UseShellExecute=$false; $i.CreateNoWindow=$true
$i.RedirectStandardOutput=$true; $i.RedirectStandardError=$true
foreach($k in @($i.EnvironmentVariables.Keys)) { if($k.StartsWith('UPPAAL_')){$i.EnvironmentVariables.Remove($k)} }
$p.StartInfo=$i
$r=[ordered]@{status='error';exit_code=$null;process_id=$null;process_reaped=$false;runtime_seconds=0;started_at_utc=[DateTime]::UtcNow.ToString('o');finished_at_utc=$null;error=$null}
$so=$null;$se=$null;$watch=[Diagnostics.Stopwatch]::StartNew()
try {
 $so=[IO.File]::Open($c.stdout,[IO.FileMode]::CreateNew)
 $se=[IO.File]::Open($c.stderr,[IO.FileMode]::CreateNew)
 if(-not $p.Start()){throw 'Start failed'}
 $r.process_id=$p.Id;Save $r
 $ot=$p.StandardOutput.BaseStream.CopyToAsync($so)
 $et=$p.StandardError.BaseStream.CopyToAsync($se)
 while(-not $p.WaitForExit(25)) { if($watch.Elapsed.TotalSeconds -ge 10){$r.status='timeout';break} }
 if($p.HasExited){$r.exit_code=$p.ExitCode;$r.status=if($p.ExitCode -eq 0){'success'}else{'error'}}
} catch {$r.error=$_.Exception.Message;$r.status='error'} finally {
 if($r.process_id -and -not $p.HasExited){
  try {& "$env:SystemRoot\System32\taskkill.exe" /PID $p.Id /T /F 2>&1 | Out-Null}catch{}
  if(-not $p.WaitForExit(2000)){$p.Kill()}
 }
 if($r.process_id){
  $r.process_reaped=$p.WaitForExit(2000)
  if($r.process_reaped){$r.exit_code=$p.ExitCode}
  foreach($t in @($ot,$et)){if($t -and -not $t.Wait(2000)){$r.status='error';$r.error='Output drain timeout'}}
  if(-not $r.process_reaped){$r.status='error';$r.error='Child not reaped'}
 }
 if($so){$so.Dispose()};if($se){$se.Dispose()}
 $r.runtime_seconds=$watch.Elapsed.TotalSeconds;$r.finished_at_utc=[DateTime]::UtcNow.ToString('o')
 Save $r;$p.Dispose()
}
if($r.status -ne 'success'){exit 2}
