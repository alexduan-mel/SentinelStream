-- ============================================================
-- SentinelStream - M1 Schema (PostgreSQL / TimescaleDB)
-- Includes: tables + indexes + comments
-- ============================================================

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ----------------------------
-- 1) Tickers (dimension table)
-- ----------------------------
CREATE TABLE IF NOT EXISTS tickers (
  ticker_id      SERIAL PRIMARY KEY,
  symbol         TEXT NOT NULL UNIQUE,   -- e.g., 'AAPL'
  name           TEXT,                   -- e.g., 'Apple Inc.'
  exchange       TEXT,                   -- e.g., 'NASDAQ'
  created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE tickers IS 'Ticker dimension table (basic entity registry)';
COMMENT ON COLUMN tickers.symbol IS 'Ticker symbol, e.g., AAPL';
COMMENT ON COLUMN tickers.name IS 'Company name (optional)';
COMMENT ON COLUMN tickers.exchange IS 'Exchange (optional)';

-- ------------------------------------------------------
-- 2) News events (append-only event table, normalized)
-- ------------------------------------------------------
CREATE TABLE IF NOT EXISTS news_events (
  news_id         TEXT PRIMARY KEY,
  trace_id        UUID NOT NULL,          -- correlation ID per pipeline run
  source          TEXT NOT NULL,          -- e.g., finnhub / polygon / rss
  source_event_id TEXT,                  -- provider-specific ID if available

  published_at    TIMESTAMPTZ NOT NULL,   -- from provider (point-in-time context)
  ingested_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),  -- system ingestion time

  title           TEXT NOT NULL,
  url             TEXT NOT NULL,
  content         TEXT,                   -- optional full text if available

  tickers         TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],  -- MVP linkage

  raw_payload     JSONB,                  -- raw provider payload for debugging/replay

  CONSTRAINT uq_news_source_url UNIQUE (source, url)
);

COMMENT ON TABLE news_events IS 'Normalized news events ingested from external sources';
COMMENT ON COLUMN news_events.news_id IS 'Deterministic unique ID (recommended: sha256(source|url))';
COMMENT ON COLUMN news_events.trace_id IS 'Correlation ID for a single pipeline run';
COMMENT ON COLUMN news_events.source IS 'News provider name';
COMMENT ON COLUMN news_events.source_event_id IS 'Provider-specific event ID if available';
COMMENT ON COLUMN news_events.published_at IS 'Published time from provider (UTC)';
COMMENT ON COLUMN news_events.ingested_at IS 'Ingestion time in SentinelStream (UTC)';
COMMENT ON COLUMN news_events.tickers IS 'Tickers associated with this news event (MVP as TEXT[])';
COMMENT ON COLUMN news_events.raw_payload IS 'Raw provider payload stored for debugging/replay';

-- Indexes for dashboard queries
CREATE INDEX IF NOT EXISTS idx_news_published_at ON news_events (published_at DESC);
CREATE INDEX IF NOT EXISTS idx_news_source ON news_events (source);
CREATE INDEX IF NOT EXISTS idx_news_tickers_gin ON news_events USING GIN (tickers);

-- ------------------------------------------------------
-- 3) Raw news items (staging for replayable normalization)
-- ------------------------------------------------------
CREATE TABLE IF NOT EXISTS raw_news_items (
  raw_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  source       TEXT NOT NULL,                 -- provider name (e.g., finnhub)
  trace_id     UUID NOT NULL,                 -- correlation ID for the fetch run
  fetched_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(), -- time the raw payload was fetched

  published_at TIMESTAMPTZ NULL,              -- optional published time if available
  url          TEXT NULL,                     -- optional url if available
  title        TEXT NULL,                     -- optional title if available

  dedup_key    TEXT NOT NULL,                 -- deterministic key (e.g., sha256(source|url))
  status       TEXT NOT NULL DEFAULT 'fetched' CHECK (status IN ('fetched','normalized','failed')),
  attempts     INTEGER NOT NULL DEFAULT 0,    -- number of normalization attempts
  last_error   TEXT NULL,                     -- last error message if normalization failed

  raw_payload  JSONB NOT NULL,

  CONSTRAINT uq_raw_news_source_dedup UNIQUE (source, dedup_key)
);

COMMENT ON TABLE raw_news_items IS 'Raw news payloads staged for replayable normalization';
COMMENT ON COLUMN raw_news_items.raw_id IS 'Unique id for a raw news payload';
COMMENT ON COLUMN raw_news_items.source IS 'Provider name (e.g., finnhub)';
COMMENT ON COLUMN raw_news_items.trace_id IS 'Correlation id for a single fetch run';
COMMENT ON COLUMN raw_news_items.fetched_at IS 'Time the raw payload was fetched';
COMMENT ON COLUMN raw_news_items.published_at IS 'Published time from provider if available';
COMMENT ON COLUMN raw_news_items.url IS 'Article URL if available';
COMMENT ON COLUMN raw_news_items.title IS 'Article title if available';
COMMENT ON COLUMN raw_news_items.dedup_key IS 'Deterministic key for deduplication (e.g., sha256(source|url))';
COMMENT ON COLUMN raw_news_items.status IS 'Processing status: fetched | normalized | failed';
COMMENT ON COLUMN raw_news_items.attempts IS 'Number of normalization attempts';
COMMENT ON COLUMN raw_news_items.last_error IS 'Last error message for failed normalization';
COMMENT ON COLUMN raw_news_items.raw_payload IS 'Raw provider payload stored for replay/debugging';

CREATE INDEX IF NOT EXISTS idx_raw_news_status_fetched_at
  ON raw_news_items (status, fetched_at DESC);

CREATE INDEX IF NOT EXISTS idx_raw_news_fetched_at
  ON raw_news_items (fetched_at DESC);

CREATE INDEX IF NOT EXISTS idx_raw_news_payload_gin
  ON raw_news_items USING GIN (raw_payload);

-- ------------------------------------------------------
-- 4) Analysis jobs (DB-backed work queue)
-- ------------------------------------------------------
CREATE TABLE IF NOT EXISTS analysis_jobs (
  job_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  news_id     TEXT NOT NULL REFERENCES news_events(news_id) ON DELETE CASCADE,
  trace_id    UUID NOT NULL,
  job_type    TEXT NOT NULL, -- e.g., llm_analysis, fetch_content
  status      TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','running','done','failed')),
  attempts    INTEGER NOT NULL DEFAULT 0,
  next_run_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  locked_at   TIMESTAMPTZ NULL,
  locked_by   TEXT NULL,
  last_error  TEXT NULL,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  CONSTRAINT uq_analysis_jobs_news_type UNIQUE (news_id, job_type)
);

COMMENT ON TABLE analysis_jobs IS 'DB-backed job queue for async processing';
COMMENT ON COLUMN analysis_jobs.job_id IS 'Unique id for a job';
COMMENT ON COLUMN analysis_jobs.news_id IS 'News event id to process';
COMMENT ON COLUMN analysis_jobs.trace_id IS 'Correlation id for publishing this job';
COMMENT ON COLUMN analysis_jobs.job_type IS 'Job type (e.g., llm_analysis, fetch_content)';
COMMENT ON COLUMN analysis_jobs.status IS 'Job status: pending | running | done | failed';
COMMENT ON COLUMN analysis_jobs.attempts IS 'Number of processing attempts';
COMMENT ON COLUMN analysis_jobs.next_run_at IS 'Earliest time this job should be run';
COMMENT ON COLUMN analysis_jobs.locked_at IS 'Time the job was locked for processing';
COMMENT ON COLUMN analysis_jobs.locked_by IS 'Worker identifier holding the lock';
COMMENT ON COLUMN analysis_jobs.last_error IS 'Last error message from processing';
COMMENT ON COLUMN analysis_jobs.created_at IS 'Time the job was created';
COMMENT ON COLUMN analysis_jobs.updated_at IS 'Time the job was last updated';

CREATE INDEX IF NOT EXISTS idx_analysis_jobs_status_next_run
  ON analysis_jobs (status, next_run_at);

CREATE INDEX IF NOT EXISTS idx_analysis_jobs_created_at
  ON analysis_jobs (created_at);

-- ------------------------------------------------------
-- 5) LLM analyses (structured output + raw output)
-- ------------------------------------------------------
CREATE TABLE IF NOT EXISTS llm_analyses (
  analysis_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  news_id         TEXT NOT NULL REFERENCES news_events(news_id) ON DELETE CASCADE,
  trace_id        UUID NOT NULL,          -- same trace_id used in this processing run

  provider        TEXT NOT NULL,          -- openai / gemini
  model           TEXT NOT NULL,          -- exact model name
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  sentiment       TEXT NOT NULL CHECK (sentiment IN ('positive', 'negative', 'neutral')),
  confidence      DOUBLE PRECISION NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
  impact_score    DOUBLE PRECISION CHECK (impact_score IS NULL OR (impact_score >= 0 AND impact_score <= 1)),

  entities        JSONB NOT NULL DEFAULT '[]'::JSONB,  -- [{symbol,name?,confidence?},...]
  summary         TEXT NOT NULL,                       -- short summary
  rationale       TEXT,                                -- optional short reasoning

  raw_output      JSONB,                               -- raw model output

  CONSTRAINT uq_analysis_run UNIQUE (news_id, trace_id, provider, model)
);

COMMENT ON TABLE llm_analyses IS 'LLM analysis results (raw output + parsed fields)';
COMMENT ON COLUMN llm_analyses.news_id IS 'FK to news_events.news_id';
COMMENT ON COLUMN llm_analyses.trace_id IS 'Correlation ID for the processing run';
COMMENT ON COLUMN llm_analyses.provider IS 'LLM provider name';
COMMENT ON COLUMN llm_analyses.model IS 'Exact model identifier';
COMMENT ON COLUMN llm_analyses.sentiment IS 'positive | negative | neutral';
COMMENT ON COLUMN llm_analyses.confidence IS 'Overall confidence in [0,1]';
COMMENT ON COLUMN llm_analyses.impact_score IS 'Optional impact score in [0,1]';
COMMENT ON COLUMN llm_analyses.entities IS 'Extracted entities/tickers as JSON array';
COMMENT ON COLUMN llm_analyses.raw_output IS 'Raw model output for debugging/replay';

CREATE INDEX IF NOT EXISTS idx_analysis_news_id ON llm_analyses (news_id);
CREATE INDEX IF NOT EXISTS idx_analysis_created_at ON llm_analyses (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_analysis_sentiment ON llm_analyses (sentiment);
CREATE INDEX IF NOT EXISTS idx_analysis_entities_gin ON llm_analyses USING GIN (entities);
