#!/usr/bin/env bash
# Start the backend (FastAPI + uvicorn) and the frontend (Vite dev server)
# together. Ctrl-C stops both.
set -euo pipefail
cd "$(dirname "$0")"

# Activate venv if present, otherwise assume system python has the deps
if [[ -d .venv ]]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi

: "${MUSIGEN_HOST:=127.0.0.1}"
: "${MUSIGEN_PORT:=8000}"

echo "▶ MusiGen: starting backend on $MUSIGEN_HOST:$MUSIGEN_PORT"
uvicorn backend.main:app --host "$MUSIGEN_HOST" --port "$MUSIGEN_PORT" &
BACK_PID=$!

trap 'echo "▶ stopping..."; kill $BACK_PID 2>/dev/null || true; kill $FRONT_PID 2>/dev/null || true; wait 2>/dev/null || true; exit 0' INT TERM

echo "▶ MusiGen: starting frontend on http://localhost:5173"
pushd frontend >/dev/null
npm run dev -- --host --port 5173 &
FRONT_PID=$!
popd >/dev/null

wait $BACK_PID $FRONT_PID
