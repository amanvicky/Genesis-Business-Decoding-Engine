# Bootstrap a private Python 3.12 into runtime\python when the PC has no
# Python 3.10+ at all. Purely local: a zip downloaded into the project folder,
# extracted, site-packages enabled, pip installed. No PATH, no registry,
# no admin. Removing the folder removes every trace.
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Py = Join-Path $Root "runtime\python"

if (Test-Path (Join-Path $Py "python.exe")) {
    Write-Host "[OK] private Python already present in runtime\python"
    exit 0
}

$Url = "https://www.python.org/ftp/python/3.12.8/python-3.12.8-embed-amd64.zip"
$Tmp = Join-Path $env:TEMP "genesis-python-embed.zip"

Write-Host "[*] downloading a private Python 3.12 (~11 MB, python.org) ..."
Invoke-WebRequest -Uri $Url -OutFile $Tmp -UseBasicParsing

New-Item -ItemType Directory -Force -Path $Py | Out-Null
Expand-Archive -Path $Tmp -DestinationPath $Py -Force
Remove-Item $Tmp -Force

# The embeddable build locks sys.path with a ._pth file; enable site-packages
# using the new interpreter itself (core stdlib works before the fix).
& (Join-Path $Py "python.exe") (Join-Path $Root "scripts\fix_pth.py") $Py
if ($LASTEXITCODE -ne 0) { throw "fix_pth.py failed" }

Write-Host "[*] installing pip into the private Python ..."
$GetPip = Join-Path $Py "get-pip.py"
Invoke-WebRequest -Uri "https://bootstrap.pypa.io/get-pip.py" -OutFile $GetPip -UseBasicParsing
& (Join-Path $Py "python.exe") $GetPip --no-warn-script-location
if ($LASTEXITCODE -ne 0) { throw "get-pip failed" }
Remove-Item $GetPip -Force

Write-Host "[OK] private Python installed into runtime\python (the rest of this PC was not touched)"
