@echo off
setlocal
cd /d "%~dp0"
title Genesis

rem ---- daily launcher: starts Genesis (already installed = instant) and
rem ---- opens the dashboard as its own window. If setup was never run, point
rem ---- the user at "Genesis Setup.bat".

set "PY="
if exist "runtime\python\python.exe" set "PY=runtime\python\python.exe"
if not defined PY py -3 -c "import sys;sys.exit(0 if sys.version_info>=(3,10) else 1)" >nul 2>nul && set "PY=py -3"
if not defined PY python -c "import sys;sys.exit(0 if sys.version_info>=(3,10) else 1)" >nul 2>nul && set "PY=python"
if not defined PY (
    echo [!] Python 3.10+ not found - double-click "Genesis Setup.bat" first.
    pause
    exit /b 1
)

%PY% genesis.py up
if errorlevel 1 pause
