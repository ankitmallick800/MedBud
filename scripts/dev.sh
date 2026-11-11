#!/usr/bin/env bash
# Start the prediction API and the Vite app together.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ ! -d "$ROOT/backend/.venv" ]]; then
  (cd "$ROOT/backend" && uv sync --python 3.12)
fi

if [[ ! -d "$ROOT/frontend/node_modules" ]]; then
  (cd "$ROOT/frontend" && npm install)
fi

pids=()
cleanup() {
  for pid in "${pids[@]}"; do
    kill "$pid" 2>/dev/null || true
  done
}
trap cleanup EXIT INT TERM

(cd "$ROOT/backend" && uv run uvicorn app.main:app --host 127.0.0.1 --port 8000) &
pids+=("$!")

(cd "$ROOT/frontend" && npm run dev -- --host 127.0.0.1 --port 5173) &
pids+=("$!")

wait
