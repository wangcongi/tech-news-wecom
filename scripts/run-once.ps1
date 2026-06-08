param(
    [string]$RepoRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$PythonPath = ''
)

$ErrorActionPreference = 'Stop'
Set-Location $RepoRoot

if ($PythonPath) {
    if (Test-Path $PythonPath) {
        $python = $PythonPath
    } else {
        throw "PythonPath does not exist: $PythonPath"
    }
} else {
    $pythonCandidates = @(
        (Join-Path $RepoRoot '.venv\Scripts\python.exe'),
        'python'
    )

    $python = $null
    foreach ($candidate in $pythonCandidates) {
        if ($candidate -and (Test-Path $candidate)) {
            $python = $candidate
            break
        }
        try {
            $resolved = (Get-Command $candidate -ErrorAction Stop).Source
            if ($resolved) {
                $python = $resolved
                break
            }
        } catch {
        }
    }
}

if (-not $python) {
    throw "Python not found. Install Python or create .venv first."
}

$logDir = Join-Path $RepoRoot 'logs'
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$logPath = Join-Path $logDir ("run-once-{0}.log" -f (Get-Date -Format 'yyyyMMdd'))

"[$(Get-Date -Format o)] Starting run-once" | Add-Content -Path $logPath
"Python=$python" | Add-Content -Path $logPath
$command = "`"$python`" -m tech_news_wecom.cli run-once >> `"$logPath`" 2>&1"
& cmd.exe /c $command
$exitCode = $LASTEXITCODE
"[$(Get-Date -Format o)] Finished run-once exit_code=$exitCode" | Add-Content -Path $logPath
exit $exitCode
