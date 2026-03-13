#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
# try to activate venv if present
if [ -f ".venv/bin/activate" ]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate || true
fi
python3 gui.py "$@"