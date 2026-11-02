@echo off
setlocal
cd /d "%~dp0"
title Genesis

set "PY="
py -3 --version >nul 2>&1 && set "PY=py -3"
if not defined PY python --version >nul 2>&1 && set "PY=python"
if not defined PY (
  echo   [X] Python 3.10+ not found. Install from https://python.org then re-run.
  pause
  exit /b 1
)

%PY% genesis.py %*
if errorlevel 1 pause
