# MarketPulse

## Overview
MarketPulse aggregates analyzed market news (scope = `market`) into persistent themes stored in `market_pulse_topics`. Each analysis becomes evidence (`market_pulse_topic_mentions`) and contributes related assets (`market_pulse_asset_links`). The aggregation is idempotent and safe to run repeatedly.

## Inputs
- `llm_analyses` where `status = 'succeeded'`
- `news_events` joined by `news_event_id` where `scope = 'market'`
- Topic fields are read from `llm_analyses.raw_output.normalized` (preferred), falling back to `raw_output.output_json`.

Required fields in raw output:
- `topic_key`
- `main_topic`
- `topic_type`
- `direction`
- `summary`

## Aggregation Flow
1. Load all successful market analyses.
2. Extract topic fields and group by `topic_key`.
3. Upsert `market_pulse_topics` using the latest `main_topic` as `display_name`.
4. Insert `market_pulse_topic_mentions` for each `(topic, news_event)` pair (deduped).
5. Upsert `market_pulse_asset_links` from `entities` (deduped by `(topic, symbol)`).
6. Recompute topic metrics:
   - `evidence_count`
   - `first_seen_at` / `last_seen_at`
   - `status`
   - `intensity_score`

## Status Logic (V1)
- `new`: first seen within 24h and low evidence count (<=3)
- `strengthening`: mentions in last 24h > previous 24h baseline
- `ongoing`: otherwise

## Intensity Logic (V1)
A simple weighted score capped to `[0,1]`:
- 70% recent mention count (scaled by 5)
- 30% average `impact_score` from last 24h

## Idempotency
- Mentions are only inserted if `(topic_id, news_event_id)` does not already exist.
- Asset links are upserted by `(topic_id, asset_symbol)` and keep the max confidence.
- Topics are upserted by `topic_key`.

market_pulse_topics
        │
        │ topic_id
        ▼
market_pulse_topic_mentions
        │
        │ news_event_id
        ▼
news_events

market_pulse_topics
        │
        ▼
market_pulse_asset_links
        │
        ▼
symbol (MU, SMH, NVDA...)

## Worker
### llm analysis worker
Run in python-ai container:
```bash
docker compose run --rm python-ai python -m jobs.market_worker --once --batch-size 10
```
### aggregation worker

Run once:
```bash
docker compose run --rm analysis-worker-market python -m workers.market_aggregation_worker --once

docker compose run --rm python-ai python -m workers.market_aggregation_worker --once

```

Continuous:
```bash
docker compose run --rm analysis-worker-market python -m workers.market_aggregation_worker
```

Config:
- `MARKET_PULSE_POLL_SECONDS` (default 300)
- `LOG_LEVEL`

Redis rate-limit keys (Docker):
```bash
docker compose exec redis redis-cli SET llm_rate_limit:market 5
docker compose exec redis redis-cli SET llm_rate_limit:company 0
```
