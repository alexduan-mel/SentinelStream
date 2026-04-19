#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY_APP_DIR="$ROOT_DIR/services/python-ai/app"
PYTHON_BIN="${PYTHON_BIN:-python3}"

export PYTHONPATH="$PY_APP_DIR${PYTHONPATH:+:$PYTHONPATH}"

echo "==> market_news_worker --once"
"$PYTHON_BIN" -m workers.market_news_worker --once

echo "==> market_worker (llm_analysis_market)"
echo "==> init redis quota llm_rate_limit:market=10"
"$PYTHON_BIN" - <<'PY'
import os
import redis

host = os.getenv("REDIS_HOST", "redis")
port = int(os.getenv("REDIS_PORT", "6379"))
db = int(os.getenv("REDIS_DB", "0"))
password = os.getenv("REDIS_PASSWORD")
client = redis.Redis(host=host, port=port, db=db, password=password, decode_responses=True)
client.set("llm_rate_limit:market", 10)
PY

MAX_LOOPS="${MARKET_WORKER_MAX_LOOPS:-50}"
BATCH_SIZE="${MARKET_WORKER_BATCH_SIZE:-10}"

for ((i = 0; i < MAX_LOOPS; i++)); do
  pending="$("$PYTHON_BIN" - <<'PY'
import os
import psycopg2

def _connect():
    host = os.getenv("POSTGRES_HOST")
    port = int(os.getenv("POSTGRES_PORT", "5432"))
    name = os.getenv("POSTGRES_DB")
    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    if not all([host, name, user, password]):
        raise SystemExit("POSTGRES_* env vars not set")
    return psycopg2.connect(host=host, port=port, dbname=name, user=user, password=password)

with _connect() as conn:
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'analysis_jobs' AND column_name IN ('run_after', 'next_run_at')"
        )
        cols = {row[0] for row in cursor.fetchall()}
        run_col = "run_after" if "run_after" in cols else "next_run_at" if "next_run_at" in cols else None
        if run_col is None:
            raise SystemExit("analysis_jobs missing run_after/next_run_at column")
        cursor.execute(
            f\"SELECT COUNT(*) FROM analysis_jobs WHERE status = 'pending' AND job_type = 'llm_analysis_market' AND {run_col} <= NOW()\"
        )
        print(cursor.fetchone()[0])
PY
)"
  if [[ "$pending" -eq 0 ]]; then
    break
  fi
  "$PYTHON_BIN" -m jobs.market_analysis_worker --once --batch-size "$BATCH_SIZE"
done

echo "==> market_aggregation_worker --once"
"$PYTHON_BIN" -m workers.market_aggregation_worker --once
