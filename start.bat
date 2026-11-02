@echo off
setlocal
title Genesis
cd /d "%~dp0"

echo.
echo   ============================================================
echo    GENESIS  -  one-click launcher
echo   ============================================================
echo.

REM ---------- prerequisites ----------
set "PY="
py -3 --version >nul 2>&1 && set "PY=py -3"
if not defined PY python --version >nul 2>&1 && set "PY=python"
if not defined PY (
  echo   [X] Python 3.10+ not found. Install from https://python.org then re-run.
  pause
  exit /b 1
)

node --version >nul 2>&1
if errorlevel 1 (
  echo   [X] Node.js 18+ not found. Install from https://nodejs.org then re-run.
  pause
  exit /b 1
)

REM ---------- backend environment (first run only) ----------
if exist "backend\.venv\Scripts\python.exe" (
  echo   [OK] backend environment found
  goto frontend_deps
)
echo   [*] First run: creating backend environment (1-2 min)...
%PY% -m venv "backend\.venv"
if errorlevel 1 goto fail_venv
"backend\.venv\Scripts\python.exe" -m pip install --disable-pip-version-check -q -r "backend\requirements.txt"
if errorlevel 1 goto fail_pip
echo   [OK] backend environment created

:frontend_deps
if exist "frontend\node_modules" (
  echo   [OK] frontend packages found
  goto launch
)
echo   [*] First run: installing frontend packages (1-3 min)...
pushd frontend
call npm install --no-audit --no-fund
if errorlevel 1 (popd & goto fail_npm)
popd
echo   [OK] frontend packages installed

:launch
echo.
echo   [*] Starting API server on port 8000 ...
start "Genesis API" /D "%~dp0backend" cmd /k ".venv\Scripts\python.exe -m uvicorn app.main:app --port 8000"

echo   [*] Starting web app on port 3000 ...
start "Genesis Web" /D "%~dp0frontend" cmd /k "npm run dev"

echo   [*] Waiting for servers to boot ...
timeout /t 8 /nobreak >nul

start "" http://localhost:3000

echo.
echo   ============================================================
echo    [OK] GENESIS IS RUNNING
echo.
echo     Web app :  http://localhost:3000
echo     API     :  http://127.0.0.1:8000/docs
echo.
echo    Stop = close the two "Genesis API/Web" windows.
echo   ============================================================
echo.
pause
exit /b 0

:fail_venv
echo   [X] Could not create the Python environment.
echo       Re-run after installing Python from https://python.org
goto stop

:fail_pip
echo   [X] pip install failed - check your internet connection.
goto stop

:fail_npm
echo   [X] npm install failed - check your internet connection.
goto stop

:stop
pause
exit /b 1
