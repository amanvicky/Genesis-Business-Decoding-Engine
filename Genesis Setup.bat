@echo off
setlocal
cd /d "%~dp0"
title Genesis Setup

rem ---- one-click install: check what exists, install missing PRIVATELY,
rem ---- build, start everything, open the dashboard in its own window.

set "PY="
py -3 -c "import sys;sys.exit(0 if sys.version_info>=(3,10) else 1)" >nul 2>nul && set "PY=py -3"
if not defined PY python -c "import sys;sys.exit(0 if sys.version_info>=(3,10) else 1)" >nul 2>nul && set "PY=python"
if not defined PY if exist "runtime\python\python.exe" set "PY=runtime\python\python.exe"

if not defined PY (
    echo [*] Python 3.10+ not found on this PC - installing a private copy into runtime\python ...
    powershell -NoProfile -ExecutionPolicy Bypass -File "scripts\bootstrap_python.ps1"
    if errorlevel 1 goto failed
    set "PY=runtime\python\python.exe"
)
echo [*] using Python: %PY%

%PY% "scripts\setup_env.py"
if errorlevel 1 goto failed

echo.
echo [OK] done. From now on, just double-click "Genesis.bat".
timeout /t 5 >nul
exit /b 0

:failed
echo.
echo [X] setup failed - read the messages above, then run this file again.
pause
exit /b 1
