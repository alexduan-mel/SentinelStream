-- ============================================================
-- SentinelStream - M1 Schema (PostgreSQL / TimescaleDB)
-- Includes: tables + indexes + comments
-- ============================================================

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ----------------------------
-- 1) Tickers (dimension table)
-- ----------------------------
CREATE TABLE IF NOT EXISTS tickers (
  id             BIGSERIAL PRIMARY KEY,
  ticker_key     INTEGER,                 -- legacy surrogate id
  symbol         TEXT NOT NULL UNIQUE,   -- e.g., 'AAPL'
  name           TEXT,                   -- e.g., 'Apple Inc.'
  exchange       TEXT,                   -- e.g., 'NASDAQ'
  created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE tickers IS 'Ticker dimension table (basic entity registry)';
COMMENT ON COLUMN tickers.id IS 'Surrogate primary key';
COMMENT ON COLUMN tickers.ticker_key IS 'Legacy ticker id (former primary key)';
COMMENT ON COLUMN tickers.symbol IS 'Ticker symbol, e.g., AAPL';
COMMENT ON COLUMN tickers.name IS 'Company name (optional)';
COMMENT ON COLUMN tickers.exchange IS 'Exchange (optional)';
CREATE UNIQUE INDEX IF NOT EXISTS uq_tickers_ticker_key ON tickers (ticker_key);

-- ------------------------------------------------------
-- 2) News events (append-only event table, normalized)
-- ------------------------------------------------------
CREATE TABLE IF NOT EXISTS news_events (
  id              BIGSERIAL PRIMARY KEY,
  news_id         CHAR(64) NOT NULL,
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

  CONSTRAINT uq_news_events_news_id UNIQUE (news_id),
  CONSTRAINT uq_news_source_url UNIQUE (source, url)
);

COMMENT ON TABLE news_events IS 'Normalized news events ingested from external sources';
COMMENT ON COLUMN news_events.id IS 'Surrogate primary key';
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
CREATE INDEX IF NOT EXISTS idx_news_news_id ON news_events (news_id);

-- ------------------------------------------------------
-- 3) Raw news items (staging for replayable normalization)
-- ------------------------------------------------------
CREATE TABLE IF NOT EXISTS raw_news_items (
  id           BIGSERIAL PRIMARY KEY,
  raw_uuid     UUID NOT NULL DEFAULT gen_random_uuid(),
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

  CONSTRAINT uq_raw_news_raw_uuid UNIQUE (raw_uuid),
  CONSTRAINT uq_raw_news_source_dedup UNIQUE (source, dedup_key)
);

COMMENT ON TABLE raw_news_items IS 'Raw news payloads staged for replayable normalization';
COMMENT ON COLUMN raw_news_items.id IS 'Surrogate primary key';
COMMENT ON COLUMN raw_news_items.raw_uuid IS 'Stable UUID for a raw news payload';
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
  id          BIGSERIAL PRIMARY KEY,
  job_uuid    UUID NOT NULL DEFAULT gen_random_uuid(),
  news_event_id BIGINT NOT NULL REFERENCES news_events(id) ON DELETE CASCADE,
  trace_id    UUID NOT NULL,
  job_type    TEXT NOT NULL, -- e.g., llm_analysis, fetch_content
  status      TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','running','done','failed')),
  attempts    INTEGER NOT NULL DEFAULT 0,
  run_after  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  locked_at   TIMESTAMPTZ NULL,
  locked_by   TEXT NULL,
  last_error  TEXT NULL,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  CONSTRAINT uq_analysis_jobs_job_uuid UNIQUE (job_uuid),
  CONSTRAINT uq_analysis_jobs_news_type UNIQUE (news_event_id, job_type)
);

COMMENT ON TABLE analysis_jobs IS 'DB-backed job queue for async processing';
COMMENT ON COLUMN analysis_jobs.id IS 'Surrogate primary key';
COMMENT ON COLUMN analysis_jobs.job_uuid IS 'Stable UUID for a job';
COMMENT ON COLUMN analysis_jobs.news_event_id IS 'News event id to process';
COMMENT ON COLUMN analysis_jobs.trace_id IS 'Correlation id for publishing this job';
COMMENT ON COLUMN analysis_jobs.job_type IS 'Job type (e.g., llm_analysis, fetch_content)';
COMMENT ON COLUMN analysis_jobs.status IS 'Job status: pending | running | done | failed';
COMMENT ON COLUMN analysis_jobs.attempts IS 'Number of processing attempts';
COMMENT ON COLUMN analysis_jobs.run_after IS 'Earliest time this job should be run';
COMMENT ON COLUMN analysis_jobs.locked_at IS 'Time the job was locked for processing';
COMMENT ON COLUMN analysis_jobs.locked_by IS 'Worker identifier holding the lock';
COMMENT ON COLUMN analysis_jobs.last_error IS 'Last error message from processing';
COMMENT ON COLUMN analysis_jobs.created_at IS 'Time the job was created';
COMMENT ON COLUMN analysis_jobs.updated_at IS 'Time the job was last updated';

CREATE INDEX IF NOT EXISTS idx_analysis_jobs_status_next_run
  ON analysis_jobs (status, run_after);

CREATE INDEX IF NOT EXISTS idx_analysis_jobs_created_at
  ON analysis_jobs (created_at);

CREATE INDEX IF NOT EXISTS idx_analysis_jobs_job_uuid
  ON analysis_jobs (job_uuid);

-- ------------------------------------------------------
-- 5) LLM analyses (structured output + raw output)
-- ------------------------------------------------------
CREATE TABLE IF NOT EXISTS llm_analyses (
  id              BIGSERIAL PRIMARY KEY,
  analysis_uuid   UUID NOT NULL DEFAULT gen_random_uuid(),

  news_event_id   BIGINT NOT NULL REFERENCES news_events(id) ON DELETE CASCADE,
  trace_id        UUID NOT NULL,          -- same trace_id used in this processing run

  provider        TEXT NOT NULL,          -- openai / gemini
  model           TEXT NOT NULL,          -- exact model name
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  status          TEXT NOT NULL DEFAULT 'pending'
                  CHECK (status IN ('pending','succeeded','failed')),
  error_message   TEXT,                   -- error summary when failed

  sentiment       TEXT CHECK (sentiment IN ('positive', 'negative', 'neutral')),
  confidence      DOUBLE PRECISION CHECK (confidence >= 0 AND confidence <= 1),
  impact_score    DOUBLE PRECISION CHECK (impact_score IS NULL OR (impact_score >= 0 AND impact_score <= 1)),

  entities        JSONB NOT NULL DEFAULT '[]'::JSONB,  -- [{symbol,name?,confidence?},...]
  summary         TEXT,                                -- reasoning summary (<= 280 chars)
  rationale       TEXT,                                -- optional short reasoning

  raw_output      JSONB,                               -- raw model output

  CONSTRAINT uq_analysis_uuid UNIQUE (analysis_uuid),
  CONSTRAINT uq_analysis_news_event UNIQUE (news_event_id)
);

COMMENT ON TABLE llm_analyses IS 'LLM analysis results (raw output + parsed fields)';
COMMENT ON COLUMN llm_analyses.id IS 'Surrogate primary key';
COMMENT ON COLUMN llm_analyses.analysis_uuid IS 'Stable UUID for an analysis row';
COMMENT ON COLUMN llm_analyses.news_event_id IS 'FK to news_events.id';
COMMENT ON COLUMN llm_analyses.trace_id IS 'Correlation ID for the processing run';
COMMENT ON COLUMN llm_analyses.provider IS 'LLM provider name';
COMMENT ON COLUMN llm_analyses.model IS 'Exact model identifier';
COMMENT ON COLUMN llm_analyses.status IS 'pending | succeeded | failed';
COMMENT ON COLUMN llm_analyses.error_message IS 'Last error message for failed analysis';
COMMENT ON COLUMN llm_analyses.sentiment IS 'positive | negative | neutral';
COMMENT ON COLUMN llm_analyses.confidence IS 'Overall confidence in [0,1]';
COMMENT ON COLUMN llm_analyses.impact_score IS 'Optional impact score in [0,1]';
COMMENT ON COLUMN llm_analyses.entities IS 'Extracted entities/tickers as JSON array';
COMMENT ON COLUMN llm_analyses.raw_output IS 'Raw model output for debugging/replay';

CREATE INDEX IF NOT EXISTS idx_analysis_news_event_id ON llm_analyses (news_event_id);
CREATE INDEX IF NOT EXISTS idx_analysis_created_at ON llm_analyses (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_analysis_sentiment ON llm_analyses (sentiment);
CREATE INDEX IF NOT EXISTS idx_analysis_entities_gin ON llm_analyses USING GIN (entities);

-- ------------------------------------------------------
-- 6) Analysis tickers (join table)
-- ------------------------------------------------------
CREATE TABLE IF NOT EXISTS analysis_tickers (
  id          BIGSERIAL PRIMARY KEY,
  analysis_id BIGINT NOT NULL REFERENCES llm_analyses(id) ON DELETE CASCADE,
  ticker      TEXT NOT NULL
);

COMMENT ON TABLE analysis_tickers IS 'Tickers extracted per analysis row';
COMMENT ON COLUMN analysis_tickers.analysis_id IS 'FK to llm_analyses.id';
COMMENT ON COLUMN analysis_tickers.ticker IS 'Extracted ticker symbol';

CREATE UNIQUE INDEX IF NOT EXISTS uq_analysis_tickers
  ON analysis_tickers (analysis_id, ticker);
