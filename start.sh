#!/usr/bin/env bash
# Genesis one-command launcher (macOS / Linux / Windows Git Bash)
set -e
cd "$(dirname "$0")"
ROOT="$(pwd)"

echo ""
echo "  ============================================================"
echo "   GENESIS  -  one-command launcher"
echo "  ============================================================"
echo ""

# ---------- prerequisites ----------
PY=""
if command -v python3 >/dev/null 2>&1; then PY=python3
elif command -v python >/dev/null 2>&1; then PY=python
else
  echo "  [X] Python 3.10+ not found. Install from https://python.org then re-run."
  exit 1
fi

if ! command -v node >/dev/null 2>&1; then
  echo "  [X] Node.js 18+ not found. Install from https://nodejs.org then re-run."
  exit 1
fi

# venv layout differs between platforms
VENV_PY="backend/.venv/bin/python"
case "$(uname -s)" in
  MINGW* | MSYS* | CYGWIN*) VENV_PY="backend/.venv/Scripts/python.exe" ;;
esac

# ---------- backend environment (first run only) ----------
if [ -f "$VENV_PY" ]; then
  echo "  [OK] backend environment found"
else
  echo "  [*] First run: creating backend environment (1-2 min)..."
  "$PY" -m venv backend/.venv
  "$VENV_PY" -m pip install --disable-pip-version-check -q -r backend/requirements.txt
  echo "  [OK] backend environment created"
fi

# ---------- frontend packages (first run only) ----------
if [ -d "frontend/node_modules" ]; then
  echo "  [OK] frontend packages found"
else
  echo "  [*] First run: installing frontend packages (1-3 min)..."
  (cd frontend && npm install --no-audit --no-fund)
  echo "  [OK] frontend packages installed"
fi

# ---------- launch ----------
echo ""
echo "  [*] Starting API server on port 8000 ..."
(cd backend && "$ROOT/$VENV_PY" -m uvicorn app.main:app --port 8000) &
API_PID=$!

echo "  [*] Starting web app on port 3000 ..."
(cd frontend && npm run dev) &
WEB_PID=$!

cleanup() { kill "$API_PID" "$WEB_PID" 2>/dev/null || true; }
trap cleanup EXIT INT TERM

echo "  [*] Waiting for servers to boot ..."
for _ in $(seq 1 15); do
  if command -v curl >/dev/null 2>&1; then
    curl -sf http://127.0.0.1:8000/api/health >/dev/null 2>&1 && break
  else
    sleep 3
    break
  fi
  sleep 2
done

(command -v xdg-open >/dev/null 2>&1 && xdg-open http://localhost:3000) || open http://localhost:3000 2>/dev/null || true

echo ""
echo "  ============================================================"
echo "   [OK] GENESIS IS RUNNING"
echo ""
echo "    Web app :  http://localhost:3000"
echo "    API     :  http://127.0.0.1:8000/docs"
echo ""
echo "   Stop = Ctrl+C here."
echo "  ============================================================"
echo ""

wait
