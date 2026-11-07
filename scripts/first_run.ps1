# Genesis zero-touch first run.
#
# Runs HIDDEN and DETACHED (launched via genesis-first-run.vbs from the
# installer or the Start-menu shortcut). Installs everything missing strictly
# inside the app folder - private Python, private Node, dependencies, the
# first production build - then starts the services and opens the dashboard
# window. No console window exists to close, nothing outside the folder is
# touched, and progress lands in logs\first-run.log for diagnostics.

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
New-Item -ItemType Directory -Force -Path "$root\logs" | Out-Null
Start-Transcript -Path "$root\logs\first-run.log" -Append | Out-Null

try {
    Write-Output "=== Genesis first-run $(Get-Date -Format s) ==="

    # 1. resolve a Python: venv -> private portable -> system 3.10+ -> bootstrap one
    $pyExe = ""
    $pyArgs = @()
    if (Test-Path "$root\backend\.venv\Scripts\python.exe") {
        $pyExe = "$root\backend\.venv\Scripts\python.exe"
        Write-Output "python: existing venv"
    } elseif (Test-Path "$root\runtime\python\python.exe") {
        $pyExe = "$root\runtime\python\python.exe"
        Write-Output "python: existing private copy"
    } else {
        if (Get-Command py -ErrorAction SilentlyContinue) {
            $ok = (& py -3 -c "import sys;print(1 if sys.version_info>=(3,10) else 0)" 2>$null)
            if ("$ok".Trim() -eq "1") { $pyExe = "py"; $pyArgs = @("-3"); Write-Output "python: system (py launcher)" }
        }
        if (-not $pyExe -and (Get-Command python -ErrorAction SilentlyContinue)) {
            $ok = (& python -c "import sys;print(1 if sys.version_info>=(3,10) else 0)" 2>$null)
            if ("$ok".Trim() -eq "1") { $pyExe = "python"; Write-Output "python: system" }
        }
    }
    if (-not $pyExe) {
        Write-Output "python: none found - installing a private copy into runtime\python ..."
        & powershell -NoProfile -ExecutionPolicy Bypass -File "$root\scripts\bootstrap_python.ps1"
        if ($LASTEXITCODE -ne 0) { throw "private Python bootstrap failed (exit $LASTEXITCODE)" }
        $pyExe = "$root\runtime\python\python.exe"
        Write-Output "python: private copy installed"
    }

    # 2. everything else (private Node if needed, deps, build, services, window).
    #    setup_env.py ends by running `genesis.py up`, which is idempotent and
    #    holds the single-setup lock, so parallel launches converge safely.
    Write-Output "running setup_env (deps, build, services)..."
    & $pyExe @pyArgs "$root\scripts\setup_env.py"
    if ($LASTEXITCODE -ne 0) { throw "setup_env failed (exit $LASTEXITCODE)" }

    Write-Output "=== first-run finished OK $(Get-Date -Format s) ==="
    exit 0
} catch {
    Write-Output "!!! first-run FAILED: $_"
    $_ | Out-File "$root\logs\first-run-error.txt" -Encoding utf8
    Stop-Transcript | Out-Null
    exit 1
}
