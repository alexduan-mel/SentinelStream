#!/usr/bin/env sh
set -eu

usage() {
  echo "Usage: $0 <up|down|down-v|logs|ps>" >&2
  exit 1
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
    docker compose down -v
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
