# Ingestion

## Finnhub news worker

Environment variables can live in `.env` (auto-loaded) or be passed explicitly:
- Finnhub token: `FINNHUB_TOKEN`
- DB connection: `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`

### Run with Docker (one-shot and replay)

```bash
# Start TimescaleDB once
docker compose up -d timescaledb

# Build the python-ai image (installs deps + app)
docker compose build python-ai

# One-shot: fetch -> stage raw -> normalize -> insert (uses tickers from DB)
docker compose run --rm python-ai \
  python -m ingestion.run --minutes-back 60 --process-limit 200

# Replay-only: skip fetch and reprocess raw_news_items
docker compose run --rm python-ai \
  python -m ingestion.run --replay-only --process-limit 200
```

### Run locally (outside Docker)

```bash
pip install -r services/python-ai/requirements.txt
PYTHONPATH=services/python-ai/app \
  POSTGRES_HOST=localhost POSTGRES_PORT=5433 \
  python -m ingestion.run --tickers AAPL MSFT --minutes-back 60 --process-limit 200
```

Notes:
- If `--tickers` is omitted, the worker loads all symbols from the `tickers` table.
- `--replay-only` skips fetching and only processes staged rows in `raw_news_items`.
- News IDs are derived from a canonicalized URL (lowercased scheme/host, tracking params removed, stable query ordering, and normalized trailing slash) so that tracking variations resolve to the same `news_id`.
