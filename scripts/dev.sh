#!/usr/bin/env bash
# Linux / macOS : ./scripts/dev.sh install | api | seed | test | demo
set -euo pipefail
PY=.venv/bin/python
case "${1:-api}" in
  install) python3 -m venv .venv; $PY -m pip install -r requirements.txt; $PY -m pip install -e agents; [ -f .env ] || cp .env.example .env ;;
  api)  $PY web/build.py; (cd api && ../$PY -m uvicorn app.main:app --reload --port 8000) ;;
  seed) $PY scripts/seed.py ;;
  demo) $PY -m ideomes_agents.cli demo ;;
  test) (cd agents && ../$PY -m pytest -q); (cd api && ../$PY -m pytest -q) ;;
  *) echo "Cibles : install, api, seed, demo, test" ;;
esac
