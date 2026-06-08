param(
    [string]$TaskName = 'Tech News WeCom',
    [string]$RepoRoot = (Split-Path -Parent $PSScriptRoot),
    [string[]]$Times = @('08:57'),
    [switch]$Force
)

$ErrorActionPreference = 'Stop'

$runScript = Join-Path $PSScriptRoot 'run-once.ps1'
if (-not (Test-Path $runScript)) {
    throw "Missing run script: $runScript"
}

$pythonCandidates = @(
    (Join-Path $RepoRoot '.venv\Scripts\python.exe'),
    (Get-Command python -ErrorAction SilentlyContinue).Source,
    (Get-Command py -ErrorAction SilentlyContinue).Source
)

$pythonPath = $null
foreach ($candidate in $pythonCandidates) {
    if ($candidate -and (Test-Path $candidate)) {
        $pythonPath = (Resolve-Path $candidate).Path
        break
    }
}

if (-not $pythonPath) {
    throw "Python not found. Create .venv or install Python first."
}

$triggerTimes = foreach ($time in $Times) {
    try {
        $parsed = [TimeSpan]::Parse($time)
        [datetime]::Today.AddHours($parsed.Hours).AddMinutes($parsed.Minutes)
    } catch {
        throw "Invalid time value '$time'. Use HH:mm."
    }
}

if ($Force) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
}

$action = New-ScheduledTaskAction `
    -Execute 'powershell.exe' `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$runScript`" -RepoRoot `"$RepoRoot`" -PythonPath `"$pythonPath`""

$triggers = foreach ($time in $triggerTimes) {
    New-ScheduledTaskTrigger -Daily -At $time
}

$settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -MultipleInstances IgnoreNew

$userId = if ($env:USERDOMAIN -and $env:USERNAME) { "$env:USERDOMAIN\$env:USERNAME" } else { $env:USERNAME }
$principal = New-ScheduledTaskPrincipal -UserId $userId -LogonType Interactive -RunLevel Limited

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $action `
    -Trigger $triggers `
    -Settings $settings `
    -Principal $principal `
    -Description "Run tech-news-wecom locally at scheduled times."

Write-Host "Installed task '$TaskName' with triggers: $($Times -join ', ')"
Write-Host "Using Python: $pythonPath"
