# Async Pipeline (M1)

## Overview

In M1, "publishing" means writing a row into the `analysis_jobs` table in Postgres/TimescaleDB. Jobs use an auto-increment `analysis_jobs.id` as the primary key and a `job_uuid` for stable tracking, and reference `news_events.id` via `news_event_id` (the surrogate PK). `news_id` remains a unique business identifier for deduplication. Workers claim jobs with `SELECT ... FOR UPDATE SKIP LOCKED`, so multiple workers can safely run in parallel without processing the same job.

## Run locally

1) Run ingestion (publishes jobs):

```bash
PYTHONPATH=services/python-ai/app \
  python -m workers.company_news_worker --minutes-back 60 --process-limit 200
```

2) Run a worker (processes jobs):

```bash
PYTHONPATH=services/python-ai/app \
  python -m jobs.worker --batch-size 10
```

Use `--once` to process the current queue and exit:

```bash
PYTHONPATH=services/python-ai/app \
  python -m jobs.worker --batch-size 10 --once
```

## Scale workers

Start multiple worker processes. Each worker uses row-level locks with `SKIP LOCKED`, so jobs are only processed once even under concurrency.
