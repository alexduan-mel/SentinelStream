-- ============================================================
-- SentinelStream - Ingestion run history
-- ============================================================

CREATE TABLE IF NOT EXISTS ingestion_runs (
  id BIGSERIAL PRIMARY KEY,
  job_name TEXT NOT NULL,
  trace_id UUID NOT NULL,
  started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  finished_at TIMESTAMPTZ,
  status TEXT NOT NULL CHECK (status IN ('running','succeeded','failed')),
  tickers JSONB NOT NULL DEFAULT '[]'::jsonb,
  window_from TIMESTAMPTZ,
  window_to TIMESTAMPTZ,
  fetched_count INT NOT NULL DEFAULT 0,
  inserted_count INT NOT NULL DEFAULT 0,
  deduped_count INT NOT NULL DEFAULT 0,
  error_message TEXT,
  meta JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_ingestion_runs_job_started
  ON ingestion_runs (job_name, started_at DESC);

CREATE INDEX IF NOT EXISTS idx_ingestion_runs_status_started
  ON ingestion_runs (status, started_at DESC);
