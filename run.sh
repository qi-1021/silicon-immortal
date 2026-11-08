#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
export PYTHONUTF8=1
if [ -x ".venv/bin/python" ]; then
  exec .venv/bin/python tools/bootstrap.py "$@"
elif command -v python3.12 >/dev/null; then
  exec python3.12 tools/bootstrap.py "$@"
else
  exec python3 tools/bootstrap.py "$@"
fi
