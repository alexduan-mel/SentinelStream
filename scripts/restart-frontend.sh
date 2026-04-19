#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
START_SCRIPT="$SCRIPT_DIR/start-frontend.sh"
PORT="${FRONTEND_PORT:-5173}"
FORCE_RESTART="${FORCE_FRONTEND_RESTART:-0}"

if [ ! -x "$START_SCRIPT" ]; then
  echo "Start script not found or not executable: $START_SCRIPT" >&2
  exit 1
fi

if ! [[ "$PORT" =~ ^[0-9]+$ ]]; then
  echo "Invalid FRONTEND_PORT: $PORT" >&2
  exit 1
fi

LISTEN_PIDS="$(lsof -tiTCP:"$PORT" -sTCP:LISTEN 2>/dev/null || true)"

if [ -n "$LISTEN_PIDS" ]; then
  SAFE_PIDS=()
  for pid in $LISTEN_PIDS; do
    cmd="$(ps -p "$pid" -o command= 2>/dev/null || true)"
    if [[ "$cmd" == *vite* ]] || [[ "$cmd" == *"npm run dev"* ]] || [ "$FORCE_RESTART" = "1" ]; then
      SAFE_PIDS+=("$pid")
      continue
    fi
    echo "Port $PORT is occupied by PID $pid, not recognized as frontend dev server." >&2
    echo "Command: $cmd" >&2
    echo "Set FORCE_FRONTEND_RESTART=1 to force-kill this process." >&2
    exit 1
  done

  if [ "${#SAFE_PIDS[@]}" -gt 0 ]; then
    echo "Stopping existing frontend process on port $PORT (PID(s): ${SAFE_PIDS[*]})..."
    kill "${SAFE_PIDS[@]}" || true
    sleep 1

    REMAINING="$(lsof -tiTCP:"$PORT" -sTCP:LISTEN 2>/dev/null || true)"
    if [ -n "$REMAINING" ]; then
      echo "Process still listening on port $PORT. Force stopping PID(s): $REMAINING"
      kill -9 $REMAINING || true
    fi
  fi
else
  echo "No running frontend process found on port $PORT."
fi

echo "Starting frontend..."
exec "$START_SCRIPT"
