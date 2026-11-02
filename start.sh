#!/usr/bin/env bash
# Genesis launcher — everything is handled by the service manager.
cd "$(dirname "$0")"
PY=""
if command -v python3 >/dev/null 2>&1; then PY=python3
elif command -v python >/dev/null 2>&1; then PY=python
else
  echo "  [X] Python 3.10+ not found. Install from https://python.org then re-run."
  exit 1
fi
exec "$PY" genesis.py "$@"
