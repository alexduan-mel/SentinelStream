#!/usr/bin/env sh
set -eu

usage() {
  echo "Usage: $0 <up|down|down-v|restart|restart-v|logs|ps>" >&2
  echo "  Destructive commands (down-v, restart-v) require WIPE_VOLUMES=1." >&2
  exit 1
}

require_wipe_confirmation() {
  if [ "${WIPE_VOLUMES:-0}" != "1" ]; then
    echo "Refusing to wipe Docker volumes without explicit confirmation." >&2
    echo "Run with WIPE_VOLUMES=1 $0 $cmd" >&2
    exit 2
  fi
}

cmd="${1:-}"
case "$cmd" in
  up)
    docker compose up --build -d
    ;;
  down)
    docker compose down
    ;;
  down-v)
    require_wipe_confirmation
    docker compose down -v
    ;;
  restart)
    docker compose down
    docker compose up --build -d
    ;;
  restart-v)
    require_wipe_confirmation
    docker compose down -v
    docker compose up --build -d
    ;;
  logs)
    docker compose logs -f
    ;;
  ps)
    docker compose ps
    ;;
  *)
    usage
    ;;
esac
