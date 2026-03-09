-- MarketPulse V2 schema (candidates + topics + mentions + asset links)

CREATE TABLE IF NOT EXISTS market_pulse_topics (
  id                BIGSERIAL PRIMARY KEY,
  topic_uuid        UUID NOT NULL DEFAULT gen_random_uuid(),
  topic_key         TEXT NOT NULL,
  display_name      TEXT NOT NULL,
  topic_family      TEXT NOT NULL DEFAULT 'other',
  topic_type        TEXT,
  summary           TEXT,
  direction         TEXT,
  status            TEXT NOT NULL DEFAULT 'active',
  strength_score    DOUBLE PRECISION,
  novelty_score     DOUBLE PRECISION,
  confidence_score  DOUBLE PRECISION,
  evidence_count    INTEGER NOT NULL DEFAULT 0,
  first_seen_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  last_seen_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  last_clustered_at TIMESTAMPTZ,
  source_candidate_id BIGINT NULL,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS market_pulse_candidates (
  id                BIGSERIAL PRIMARY KEY,
  candidate_uuid    UUID NOT NULL DEFAULT gen_random_uuid(),
  topic_family      TEXT NOT NULL DEFAULT 'other',
  candidate_key     TEXT NOT NULL,
  candidate_label   TEXT NOT NULL,
  representative_subtopic TEXT,
  summary           TEXT,
  status            TEXT NOT NULL DEFAULT 'candidate',
  evidence_count    INTEGER NOT NULL DEFAULT 0,
  avg_relevance_score DOUBLE PRECISION,
  centroid_embedding JSONB,
  first_seen_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  last_seen_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  promoted_topic_id BIGINT NULL,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS market_pulse_topic_mentions (
  id                BIGSERIAL PRIMARY KEY,
  mention_uuid      UUID NOT NULL DEFAULT gen_random_uuid(),
  topic_id          BIGINT NULL REFERENCES market_pulse_topics(id) ON DELETE CASCADE,
  candidate_id      BIGINT NULL REFERENCES market_pulse_candidates(id) ON DELETE CASCADE,
  news_event_id     BIGINT NOT NULL REFERENCES news_events(id) ON DELETE CASCADE,
  llm_analysis_id   BIGINT NULL REFERENCES llm_analyses(id) ON DELETE CASCADE,
  topic_family      TEXT NOT NULL,
  subtopic_label    TEXT,
  reasoning_summary TEXT,
  relevance_score   DOUBLE PRECISION,
  similarity_score  DOUBLE PRECISION,
  assigned_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS market_pulse_asset_links (
  id               BIGSERIAL PRIMARY KEY,
  asset_link_uuid  UUID NOT NULL DEFAULT gen_random_uuid(),
  topic_id         BIGINT NOT NULL REFERENCES market_pulse_topics(id) ON DELETE CASCADE,
  asset_symbol     TEXT NOT NULL,
  asset_type       TEXT,
  relation_type    TEXT,
  confidence_score DOUBLE PRECISION,
  mention_count    INTEGER NOT NULL DEFAULT 0,
  first_seen_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  last_seen_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.tables WHERE table_name = 'market_pulse_topics'
  ) THEN
    IF NOT EXISTS (
      SELECT 1 FROM information_schema.columns
      WHERE table_name = 'market_pulse_topics' AND column_name = 'topic_uuid'
    ) THEN
      ALTER TABLE market_pulse_topics ADD COLUMN topic_uuid UUID DEFAULT gen_random_uuid();
      ALTER TABLE market_pulse_topics ALTER COLUMN topic_uuid SET NOT NULL;
    END IF;

    IF NOT EXISTS (
      SELECT 1 FROM information_schema.columns
      WHERE table_name = 'market_pulse_topics' AND column_name = 'topic_family'
    ) THEN
      ALTER TABLE market_pulse_topics ADD COLUMN topic_family TEXT DEFAULT 'other';
    END IF;
    UPDATE market_pulse_topics SET topic_family = 'other' WHERE topic_family IS NULL;
    ALTER TABLE market_pulse_topics ALTER COLUMN topic_family SET NOT NULL;

    IF NOT EXISTS (
      SELECT 1 FROM information_schema.columns
      WHERE table_name = 'market_pulse_topics' AND column_name = 'strength_score'
    ) THEN
      ALTER TABLE market_pulse_topics ADD COLUMN strength_score DOUBLE PRECISION;
    END IF;
    IF NOT EXISTS (
      SELECT 1 FROM information_schema.columns
      WHERE table_name = 'market_pulse_topics' AND column_name = 'novelty_score'
    ) THEN
      ALTER TABLE market_pulse_topics ADD COLUMN novelty_score DOUBLE PRECISION;
    END IF;
    IF NOT EXISTS (
      SELECT 1 FROM information_schema.columns
      WHERE table_name = 'market_pulse_topics' AND column_name = 'last_clustered_at'
    ) THEN
      ALTER TABLE market_pulse_topics ADD COLUMN last_clustered_at TIMESTAMPTZ;
    END IF;
    IF NOT EXISTS (
      SELECT 1 FROM information_schema.columns
      WHERE table_name = 'market_pulse_topics' AND column_name = 'source_candidate_id'
    ) THEN
      ALTER TABLE market_pulse_topics ADD COLUMN source_candidate_id BIGINT;
    END IF;

    UPDATE market_pulse_topics SET display_name = topic_key WHERE display_name IS NULL;
    ALTER TABLE market_pulse_topics ALTER COLUMN display_name SET NOT NULL;
  END IF;

  IF EXISTS (
    SELECT 1 FROM information_schema.tables WHERE table_name = 'market_pulse_topic_mentions'
  ) THEN
    IF NOT EXISTS (
      SELECT 1 FROM information_schema.columns
      WHERE table_name = 'market_pulse_topic_mentions' AND column_name = 'mention_uuid'
    ) THEN
      ALTER TABLE market_pulse_topic_mentions ADD COLUMN mention_uuid UUID DEFAULT gen_random_uuid();
      ALTER TABLE market_pulse_topic_mentions ALTER COLUMN mention_uuid SET NOT NULL;
    END IF;
    IF NOT EXISTS (
      SELECT 1 FROM information_schema.columns
      WHERE table_name = 'market_pulse_topic_mentions' AND column_name = 'candidate_id'
    ) THEN
      ALTER TABLE market_pulse_topic_mentions ADD COLUMN candidate_id BIGINT;
    END IF;
    IF NOT EXISTS (
      SELECT 1 FROM information_schema.columns
      WHERE table_name = 'market_pulse_topic_mentions' AND column_name = 'llm_analysis_id'
    ) THEN
      ALTER TABLE market_pulse_topic_mentions ADD COLUMN llm_analysis_id BIGINT;
    END IF;
    IF NOT EXISTS (
      SELECT 1 FROM information_schema.columns
      WHERE table_name = 'market_pulse_topic_mentions' AND column_name = 'topic_family'
    ) THEN
      ALTER TABLE market_pulse_topic_mentions ADD COLUMN topic_family TEXT DEFAULT 'other';
    END IF;
    UPDATE market_pulse_topic_mentions SET topic_family = 'other' WHERE topic_family IS NULL;
    ALTER TABLE market_pulse_topic_mentions ALTER COLUMN topic_family SET NOT NULL;
    IF NOT EXISTS (
      SELECT 1 FROM information_schema.columns
      WHERE table_name = 'market_pulse_topic_mentions' AND column_name = 'subtopic_label'
    ) THEN
      ALTER TABLE market_pulse_topic_mentions ADD COLUMN subtopic_label TEXT;
    END IF;
    IF NOT EXISTS (
      SELECT 1 FROM information_schema.columns
      WHERE table_name = 'market_pulse_topic_mentions' AND column_name = 'similarity_score'
    ) THEN
      ALTER TABLE market_pulse_topic_mentions ADD COLUMN similarity_score DOUBLE PRECISION;
    END IF;
    IF NOT EXISTS (
      SELECT 1 FROM information_schema.columns
      WHERE table_name = 'market_pulse_topic_mentions' AND column_name = 'assigned_at'
    ) THEN
      ALTER TABLE market_pulse_topic_mentions ADD COLUMN assigned_at TIMESTAMPTZ DEFAULT NOW();
      UPDATE market_pulse_topic_mentions SET assigned_at = COALESCE(assigned_at, created_at, NOW());
      ALTER TABLE market_pulse_topic_mentions ALTER COLUMN assigned_at SET NOT NULL;
    END IF;
  END IF;

  IF EXISTS (
    SELECT 1 FROM information_schema.tables WHERE table_name = 'market_pulse_asset_links'
  ) THEN
    IF NOT EXISTS (
      SELECT 1 FROM information_schema.columns
      WHERE table_name = 'market_pulse_asset_links' AND column_name = 'asset_link_uuid'
    ) THEN
      ALTER TABLE market_pulse_asset_links ADD COLUMN asset_link_uuid UUID DEFAULT gen_random_uuid();
      ALTER TABLE market_pulse_asset_links ALTER COLUMN asset_link_uuid SET NOT NULL;
    END IF;
    IF NOT EXISTS (
      SELECT 1 FROM information_schema.columns
      WHERE table_name = 'market_pulse_asset_links' AND column_name = 'mention_count'
    ) THEN
      ALTER TABLE market_pulse_asset_links ADD COLUMN mention_count INTEGER DEFAULT 0;
      ALTER TABLE market_pulse_asset_links ALTER COLUMN mention_count SET NOT NULL;
    END IF;
    IF NOT EXISTS (
      SELECT 1 FROM information_schema.columns
      WHERE table_name = 'market_pulse_asset_links' AND column_name = 'first_seen_at'
    ) THEN
      ALTER TABLE market_pulse_asset_links ADD COLUMN first_seen_at TIMESTAMPTZ DEFAULT NOW();
      UPDATE market_pulse_asset_links SET first_seen_at = COALESCE(first_seen_at, created_at, NOW());
      ALTER TABLE market_pulse_asset_links ALTER COLUMN first_seen_at SET NOT NULL;
    END IF;
    IF NOT EXISTS (
      SELECT 1 FROM information_schema.columns
      WHERE table_name = 'market_pulse_asset_links' AND column_name = 'last_seen_at'
    ) THEN
      ALTER TABLE market_pulse_asset_links ADD COLUMN last_seen_at TIMESTAMPTZ DEFAULT NOW();
      UPDATE market_pulse_asset_links SET last_seen_at = COALESCE(last_seen_at, created_at, NOW());
      ALTER TABLE market_pulse_asset_links ALTER COLUMN last_seen_at SET NOT NULL;
    END IF;
    IF NOT EXISTS (
      SELECT 1 FROM information_schema.columns
      WHERE table_name = 'market_pulse_asset_links' AND column_name = 'updated_at'
    ) THEN
      ALTER TABLE market_pulse_asset_links ADD COLUMN updated_at TIMESTAMPTZ DEFAULT NOW();
      UPDATE market_pulse_asset_links SET updated_at = COALESCE(updated_at, created_at, NOW());
      ALTER TABLE market_pulse_asset_links ALTER COLUMN updated_at SET NOT NULL;
    END IF;
    UPDATE market_pulse_asset_links SET asset_symbol = 'UNKNOWN' WHERE asset_symbol IS NULL;
    ALTER TABLE market_pulse_asset_links ALTER COLUMN asset_symbol SET NOT NULL;
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'uq_market_pulse_topics_topic_key'
  ) THEN
    ALTER TABLE market_pulse_topics
      ADD CONSTRAINT uq_market_pulse_topics_topic_key UNIQUE (topic_key);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'chk_market_pulse_topics_status'
  ) THEN
    UPDATE market_pulse_topics
      SET status = 'active'
      WHERE status IS NULL OR status IN ('new','ongoing');
    ALTER TABLE market_pulse_topics
      ADD CONSTRAINT chk_market_pulse_topics_status
      CHECK (status IN ('candidate','active','strengthening','fading','archived'));
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'chk_market_pulse_topics_direction'
  ) THEN
    UPDATE market_pulse_topics
      SET direction = CASE
        WHEN direction = 'bullish' THEN 'positive'
        WHEN direction = 'bearish' THEN 'negative'
        ELSE direction
      END
      WHERE direction IS NOT NULL;
    ALTER TABLE market_pulse_topics
      ADD CONSTRAINT chk_market_pulse_topics_direction
      CHECK (direction IS NULL OR direction IN ('positive','negative','neutral','mixed'));
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'chk_market_pulse_topics_strength_score'
  ) THEN
    ALTER TABLE market_pulse_topics
      ADD CONSTRAINT chk_market_pulse_topics_strength_score
      CHECK (strength_score IS NULL OR strength_score >= 0);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'chk_market_pulse_topics_novelty_score'
  ) THEN
    ALTER TABLE market_pulse_topics
      ADD CONSTRAINT chk_market_pulse_topics_novelty_score
      CHECK (novelty_score IS NULL OR novelty_score >= 0);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'chk_market_pulse_topics_confidence_score'
  ) THEN
    ALTER TABLE market_pulse_topics
      ADD CONSTRAINT chk_market_pulse_topics_confidence_score
      CHECK (confidence_score IS NULL OR (confidence_score >= 0 AND confidence_score <= 1));
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'chk_market_pulse_candidates_status'
  ) THEN
    UPDATE market_pulse_candidates
      SET status = 'candidate'
      WHERE status IS NULL;
    ALTER TABLE market_pulse_candidates
      ADD CONSTRAINT chk_market_pulse_candidates_status
      CHECK (status IN ('candidate','promoted','rejected','archived'));
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'chk_market_pulse_candidates_avg_relevance'
  ) THEN
    ALTER TABLE market_pulse_candidates
      ADD CONSTRAINT chk_market_pulse_candidates_avg_relevance
      CHECK (avg_relevance_score IS NULL OR (avg_relevance_score >= 0 AND avg_relevance_score <= 1));
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'chk_market_pulse_topic_mentions_relevance'
  ) THEN
    ALTER TABLE market_pulse_topic_mentions
      ADD CONSTRAINT chk_market_pulse_topic_mentions_relevance
      CHECK (relevance_score IS NULL OR (relevance_score >= 0 AND relevance_score <= 1));
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'chk_market_pulse_topic_mentions_similarity'
  ) THEN
    ALTER TABLE market_pulse_topic_mentions
      ADD CONSTRAINT chk_market_pulse_topic_mentions_similarity
      CHECK (similarity_score IS NULL OR (similarity_score >= 0 AND similarity_score <= 1));
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'chk_market_pulse_topic_mentions_subject'
  ) THEN
    ALTER TABLE market_pulse_topic_mentions
      ADD CONSTRAINT chk_market_pulse_topic_mentions_subject
      CHECK (topic_id IS NOT NULL OR candidate_id IS NOT NULL);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'chk_market_pulse_asset_links_confidence'
  ) THEN
    ALTER TABLE market_pulse_asset_links
      ADD CONSTRAINT chk_market_pulse_asset_links_confidence
      CHECK (confidence_score IS NULL OR (confidence_score >= 0 AND confidence_score <= 1));
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'uq_market_pulse_candidates_candidate_key'
  ) THEN
    ALTER TABLE market_pulse_candidates
      ADD CONSTRAINT uq_market_pulse_candidates_candidate_key UNIQUE (candidate_key);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'uq_market_pulse_asset_links_topic_asset'
  ) THEN
    ALTER TABLE market_pulse_asset_links
      ADD CONSTRAINT uq_market_pulse_asset_links_topic_asset UNIQUE (topic_id, asset_symbol);
  END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_market_pulse_topics_topic_key
  ON market_pulse_topics (topic_key);
CREATE INDEX IF NOT EXISTS idx_market_pulse_topics_topic_family
  ON market_pulse_topics (topic_family);
CREATE INDEX IF NOT EXISTS idx_market_pulse_topics_status
  ON market_pulse_topics (status);
CREATE INDEX IF NOT EXISTS idx_market_pulse_topics_last_seen_at
  ON market_pulse_topics (last_seen_at);
CREATE INDEX IF NOT EXISTS idx_market_pulse_topics_source_candidate_id
  ON market_pulse_topics (source_candidate_id);

CREATE INDEX IF NOT EXISTS idx_market_pulse_candidates_topic_family
  ON market_pulse_candidates (topic_family);
CREATE INDEX IF NOT EXISTS idx_market_pulse_candidates_status
  ON market_pulse_candidates (status);
CREATE INDEX IF NOT EXISTS idx_market_pulse_candidates_last_seen_at
  ON market_pulse_candidates (last_seen_at);
CREATE INDEX IF NOT EXISTS idx_market_pulse_candidates_promoted_topic_id
  ON market_pulse_candidates (promoted_topic_id);

CREATE INDEX IF NOT EXISTS idx_market_pulse_topic_mentions_news_event_id
  ON market_pulse_topic_mentions (news_event_id);
CREATE INDEX IF NOT EXISTS idx_market_pulse_topic_mentions_llm_analysis_id
  ON market_pulse_topic_mentions (llm_analysis_id);
CREATE INDEX IF NOT EXISTS idx_market_pulse_topic_mentions_topic_family
  ON market_pulse_topic_mentions (topic_family);
CREATE INDEX IF NOT EXISTS idx_market_pulse_topic_mentions_assigned_at
  ON market_pulse_topic_mentions (assigned_at);

CREATE UNIQUE INDEX IF NOT EXISTS uq_market_pulse_topic_mentions_topic_event
  ON market_pulse_topic_mentions (topic_id, news_event_id)
  WHERE topic_id IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS uq_market_pulse_topic_mentions_candidate_event
  ON market_pulse_topic_mentions (candidate_id, news_event_id)
  WHERE candidate_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_market_pulse_asset_links_asset_symbol
  ON market_pulse_asset_links (asset_symbol);
CREATE INDEX IF NOT EXISTS idx_market_pulse_asset_links_last_seen_at
  ON market_pulse_asset_links (last_seen_at);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_market_pulse_topics_source_candidate'
  ) THEN
    ALTER TABLE market_pulse_topics
      ADD CONSTRAINT fk_market_pulse_topics_source_candidate
      FOREIGN KEY (source_candidate_id) REFERENCES market_pulse_candidates(id) ON DELETE SET NULL;
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_market_pulse_candidates_promoted_topic'
  ) THEN
    ALTER TABLE market_pulse_candidates
      ADD CONSTRAINT fk_market_pulse_candidates_promoted_topic
      FOREIGN KEY (promoted_topic_id) REFERENCES market_pulse_topics(id) ON DELETE SET NULL;
  END IF;
END $$;
