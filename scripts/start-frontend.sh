#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
FRONTEND_DIR="$REPO_ROOT/services/frontend"

if [ ! -f "$FRONTEND_DIR/package.json" ]; then
  echo "Frontend package.json not found at: $FRONTEND_DIR/package.json" >&2
  exit 1
fi

cd "$FRONTEND_DIR"

if [ ! -d node_modules ]; then
  npm install
fi

RUN_CMD=(npm run dev -- --host 0.0.0.0)
if [ -n "${FRONTEND_PORT:-}" ]; then
  RUN_CMD+=(--port "$FRONTEND_PORT")
fi

if [ "${FRONTEND_SILENT:-0}" = "1" ]; then
  LOG_FILE="${FRONTEND_LOG_FILE:-/tmp/sentinel-frontend.log}"
  nohup "${RUN_CMD[@]}" >"$LOG_FILE" 2>&1 &
  PID=$!
  echo "Frontend started in background. pid=$PID log=$LOG_FILE"
else
  exec "${RUN_CMD[@]}"
fi
