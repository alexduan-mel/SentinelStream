#!/bin/sh
set -eu

SCHEDULE="${INGEST_CRON_SCHEDULE:?INGEST_CRON_SCHEDULE is required}"
TEMPLATE="/app/cron/crontab"
RENDERED="/tmp/ingest.crontab"

sed "s|__INGEST_CRON_SCHEDULE__|${SCHEDULE}|" "$TEMPLATE" > "$RENDERED"

exec /usr/local/bin/supercronic "$RENDERED"
