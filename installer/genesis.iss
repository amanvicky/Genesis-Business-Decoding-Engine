; Genesis — standard Windows installer (Inno Setup 6/7).
; Per-user install into %LOCALAPPDATA%\Genesis: no admin rights, no registry
; changes beyond the normal uninstall entry, files only inside the install
; folder. The heavy lifting (private Python/Node if missing, deps, build)
; happens on first launch via Genesis.bat -> scripts\setup_env.py.

#define MyAppName "Genesis"
#define MyAppVersion "1.7.0"
#define MyAppPublisher "Aman Vicky"
#define MyAppURL "https://github.com/amanvicky/Genesis-Business-Decoding-Engine"

[Setup]
AppId={{F3B9A2C1-5D47-4E88-9A61-2C8B0E7F4D55}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
DefaultDirName={localappdata}\{#MyAppName}
PrivilegesRequired=lowest
DisableProgramGroupPage=yes
LicenseFile=..\LICENSE
OutputDir=..\dist
OutputBaseFilename=Genesis-{#MyAppVersion}-Setup
SetupIconFile=..\assets\genesis.ico
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
UninstallDisplayName={#MyAppName}
UninstallDisplayIcon={app}\assets\genesis.ico
CloseApplications=no

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "torkit"; Description: "Privacy layer (Tor): download the official client into this folder (~10 MB, client-only)"; GroupDescription: "Optional extras:"

[Files]
Source: "..\genesis.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\Genesis.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\genesis-launch.vbs"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\assets\genesis.ico"; DestDir: "{app}\assets"; Flags: ignoreversion
Source: "..\scripts\*"; DestDir: "{app}\scripts"; Flags: ignoreversion recursesubdirs
Source: "..\backend\*"; DestDir: "{app}\backend"; Excludes: ".venv,__pycache__,*.pyc,.pytest_cache,logs"; Flags: ignoreversion recursesubdirs
Source: "..\frontend\*"; DestDir: "{app}\frontend"; Excludes: "node_modules,.next,.hallmark,.eslintcache"; Flags: ignoreversion recursesubdirs
Source: "..\README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\LICENSE"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\Genesis\Genesis"; Filename: "{app}\genesis-launch.vbs"; IconFilename: "{app}\assets\genesis.ico"; Comment: "Decode any company into an 18-tab intelligence brief"
Name: "{autodesktop}\Genesis"; Filename: "{app}\genesis-launch.vbs"; IconFilename: "{app}\assets\genesis.ico"; Tasks: desktopicon; Comment: "Decode any company into an 18-tab intelligence brief"

[Run]
Filename: "{app}\Genesis.bat"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent runasoriginaluser

[UninstallRun]
Filename: "{cmd}"; Parameters: "/C cd /d ""{app}"" && (if exist runtime\python\python.exe (runtime\python\python.exe genesis.py stop) else (python genesis.py stop))"; Flags: runhidden; RunOnceId: "StopGenesis"

; first-run creates the venv, node_modules, the production build and runtime
; state — a real uninstall removes them too, leaving nothing behind
[UninstallDelete]
Type: filesandordirs; Name: "{app}\backend\.venv"
Type: filesandordirs; Name: "{app}\frontend\node_modules"
Type: filesandordirs; Name: "{app}\frontend\.next"
Type: filesandordirs; Name: "{app}\runtime"
Type: filesandordirs; Name: "{app}\logs"

[Code]
procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
    if WizardIsTaskSelected('torkit') then begin
      ForceDirectories(ExpandConstant('{app}\runtime'));
      SaveStringToFile(ExpandConstant('{app}\runtime\tor-request.txt'), 'tor', False);
    end;
end;
