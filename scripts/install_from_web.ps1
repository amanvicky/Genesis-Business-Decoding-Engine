# Genesis one-paste web installer.
#
# The GitHub page shows ONE PowerShell line pointing at this file. The user
# pastes it once and Genesis takes it from there: it downloads itself from the
# repo link, extracts into the user folder, sets up shortcuts, and fires the
# same hidden first run the Setup.exe uses — private Python/Node, deps, build,
# services — and the dashboard window opens by itself when ready.
#
# No admin, no other steps, nothing outside the app folder is touched.

$ErrorActionPreference = "Stop"
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$repo = "https://github.com/amanvicky/Genesis-Business-Decoding-Engine"
$zipUrl = "$repo/archive/refs/heads/main.zip"
# hidden knob for automated tests; real users always get the standard folder
$app = if ($env:GENESIS_WEB_DIR) { $env:GENESIS_WEB_DIR } else { "$env:LOCALAPPDATA\Genesis" }
$tmp = Join-Path $env:TEMP ("genesis-web-install-" + (Get-Random))

Write-Host ""
Write-Host "  [*] downloading Genesis from the repo link..." -ForegroundColor Cyan
New-Item -ItemType Directory -Force -Path $tmp | Out-Null
Invoke-WebRequest -Uri $zipUrl -OutFile (Join-Path $tmp "genesis.zip") -UseBasicParsing

Write-Host "  [*] extracting into $app (nothing outside this folder is touched)..."
Expand-Archive -Path (Join-Path $tmp "genesis.zip") -DestinationPath (Join-Path $tmp "x") -Force
$src = (Get-ChildItem (Join-Path $tmp "x") -Directory | Select-Object -First 1).FullName
New-Item -ItemType Directory -Force -Path $app | Out-Null
# update-in-place: runtime\ (private python/node) and logs\ survive the copy
Copy-Item (Join-Path $src "*") $app -Recurse -Force

# shortcuts, same icon the Setup.exe uses
$ws = New-Object -ComObject WScript.Shell
$wscript = Join-Path $env:WINDIR "System32\wscript.exe"
$vbs = Join-Path $app "genesis-launch.vbs"
$icon = Join-Path $app "assets\genesis.ico"
$sm = [Environment]::GetFolderPath("Programs")
New-Item -ItemType Directory -Force -Path (Join-Path $sm "Genesis") | Out-Null
$lnk = $ws.CreateShortcut((Join-Path $sm "Genesis\Genesis.lnk"))
$lnk.TargetPath = $wscript
$lnk.Arguments = ('"' + $vbs + '"')
$lnk.WorkingDirectory = $app
$lnk.IconLocation = $icon
$lnk.Save()
$dt = [Environment]::GetFolderPath("Desktop")
$lnk2 = $ws.CreateShortcut((Join-Path $dt "Genesis.lnk"))
$lnk2.TargetPath = $wscript
$lnk2.Arguments = ('"' + $vbs + '"')
$lnk2.WorkingDirectory = $app
$lnk2.IconLocation = $icon
$lnk2.Save()

Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "  [*] firing the hidden first run (private Python/Node, deps, build)..."
Start-Process -FilePath $wscript -ArgumentList ('"' + (Join-Path $app "genesis-first-run.vbs") + '"')

Write-Host ""
Write-Host "  [OK] Genesis is preparing itself in the background." -ForegroundColor Green
Write-Host "       The dashboard opens by itself when ready (a few minutes, once)."
Write-Host "       Later: Start menu -> Genesis."
Write-Host "       Uninstall: delete $app (plus the shortcuts)."
Write-Host ""
