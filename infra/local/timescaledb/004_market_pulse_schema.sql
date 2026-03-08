-- MarketPulse V1 schema (topics + mentions + asset links)

CREATE TABLE IF NOT EXISTS market_pulse_topics (
  id                BIGSERIAL PRIMARY KEY,
  topic_key         TEXT NOT NULL,
  display_name      TEXT,
  topic_type        TEXT,
  direction         TEXT,
  summary           TEXT,
  intensity_score   DOUBLE PRECISION,
  confidence_score  DOUBLE PRECISION,
  evidence_count    INTEGER NOT NULL DEFAULT 0,
  status            TEXT CHECK (status IN ('new','ongoing','strengthening')),
  first_seen_at     TIMESTAMPTZ,
  last_seen_at      TIMESTAMPTZ,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conname = 'uq_market_pulse_topics_topic_key'
  ) THEN
    ALTER TABLE market_pulse_topics
      ADD CONSTRAINT uq_market_pulse_topics_topic_key UNIQUE (topic_key);
  END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_market_pulse_topics_topic_key
  ON market_pulse_topics (topic_key);
CREATE INDEX IF NOT EXISTS idx_market_pulse_topics_last_seen_at
  ON market_pulse_topics (last_seen_at);

CREATE TABLE IF NOT EXISTS market_pulse_topic_mentions (
  id                BIGSERIAL PRIMARY KEY,
  topic_id          BIGINT REFERENCES market_pulse_topics(id) ON DELETE CASCADE,
  news_event_id     BIGINT REFERENCES news_events(id) ON DELETE CASCADE,
  relevance_score   DOUBLE PRECISION,
  reasoning_summary TEXT,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_market_pulse_topic_mentions_topic_id
  ON market_pulse_topic_mentions (topic_id);
CREATE INDEX IF NOT EXISTS idx_market_pulse_topic_mentions_news_event_id
  ON market_pulse_topic_mentions (news_event_id);

CREATE TABLE IF NOT EXISTS market_pulse_asset_links (
  id               BIGSERIAL PRIMARY KEY,
  topic_id         BIGINT REFERENCES market_pulse_topics(id) ON DELETE CASCADE,
  asset_symbol     TEXT,
  asset_type       TEXT,
  relation_type    TEXT,
  confidence_score DOUBLE PRECISION,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_market_pulse_asset_links_topic_id
  ON market_pulse_asset_links (topic_id);
CREATE INDEX IF NOT EXISTS idx_market_pulse_asset_links_asset_symbol
  ON market_pulse_asset_links (asset_symbol);
