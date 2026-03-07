#!/bin/sh
set -eu

SCHEDULE="${INGEST_CRON_SCHEDULE:-*/10 * * * *}"
MARKET_NEWS_SCHEDULE="${MARKET_NEWS_CRON_SCHEDULE:-*/10 * * * *}"
TEMPLATE="/app/cron/crontab"
RENDERED="/tmp/ingest.crontab"

sed -e "s|__INGEST_CRON_SCHEDULE__|${SCHEDULE}|" \
  -e "s|__MARKET_NEWS_CRON_SCHEDULE__|${MARKET_NEWS_SCHEDULE}|" \
  "$TEMPLATE" > "$RENDERED"

exec /usr/local/bin/supercronic "$RENDERED"
