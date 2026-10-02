param([Parameter(Mandatory=$true)][string]$Root)
$ErrorActionPreference='Stop'
foreach($file in @(Get-ChildItem -LiteralPath $Root -Recurse -Filter '*owned.json')) {
    foreach($entry in @(Get-Content -Raw -LiteralPath $file.FullName | ConvertFrom-Json)) {
        $proc=Get-Process -Id ([int]$entry.id) -ErrorAction SilentlyContinue
        if($proc -and $proc.StartTime.ToUniversalTime().ToString('o') -eq $entry.start) {
            & taskkill.exe /PID $proc.Id /T /F 2>$null | Out-Null
            if(-not $proc.WaitForExit(5000)) { throw 'Owned process not reaped during watchdog cleanup' }
        }
    }
}
'Owned process identities cleaned'
