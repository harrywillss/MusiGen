#!/usr/bin/env bash
# Start the backend (FastAPI + uvicorn) first, wait for it to be ready, then
# start the frontend (Vite dev server). Ctrl-C stops both.
set -euo pipefail
cd "$(dirname "$0")"

# Activate venv if present, otherwise assume system python has the deps
if [[ -d .venv ]]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi

: "${MUSIGEN_HOST:=127.0.0.1}"
: "${MUSIGEN_PORT:=8000}"

BACK_PID=""
FRONT_PID=""

cleanup() {
  echo
  echo "▶ stopping..."
  [[ -n "$FRONT_PID" ]] && kill "$FRONT_PID" 2>/dev/null || true
  [[ -n "$BACK_PID"  ]] && kill "$BACK_PID"  2>/dev/null || true
  wait 2>/dev/null || true
  exit 0
}
trap cleanup INT TERM

echo "▶ MusiGen: starting backend on http://$MUSIGEN_HOST:$MUSIGEN_PORT"
uvicorn backend.main:app --host "$MUSIGEN_HOST" --port "$MUSIGEN_PORT" &
BACK_PID=$!

# Wait until the backend answers /api/health (up to ~30s), so the frontend
# doesn't spam ECONNREFUSED into the console on the first few polls.
echo -n "   waiting for backend"
for i in $(seq 1 60); do
  if curl -fsS "http://$MUSIGEN_HOST:$MUSIGEN_PORT/api/health" >/dev/null 2>&1; then
    echo " ✔"
    break
  fi
  # Backend died?
  if ! kill -0 "$BACK_PID" 2>/dev/null; then
    echo
    echo "✗ backend exited before becoming healthy" >&2
    exit 1
  fi
  echo -n "."
  sleep 0.5
done

echo "▶ MusiGen: starting frontend on http://localhost:5173"
( cd frontend && npm run dev ) &
FRONT_PID=$!

wait "$BACK_PID" "$FRONT_PID"
