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

if [ -n "${FRONTEND_PORT:-}" ]; then
  npm run dev -- --host 0.0.0.0 --port "$FRONTEND_PORT"
else
  npm run dev -- --host 0.0.0.0
fi
