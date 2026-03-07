DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'news_events' AND column_name = 'source'
  ) THEN
    ALTER TABLE news_events RENAME COLUMN source TO provider;
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'news_events' AND column_name = 'provider'
  ) THEN
    ALTER TABLE news_events ADD COLUMN provider TEXT;
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'news_events' AND column_name = 'publisher'
  ) THEN
    ALTER TABLE news_events ADD COLUMN publisher TEXT;
  END IF;
END$$;

UPDATE news_events
SET provider = 'finnhub'
WHERE provider IS NULL
  AND (
    raw_payload ? 'source'
    OR (raw_payload ? 'item' AND raw_payload->'item' ? 'source')
  );

UPDATE news_events
SET publisher = COALESCE(
    publisher,
    raw_payload->>'source',
    raw_payload->'item'->>'source'
)
WHERE publisher IS NULL;

DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_news_source_url'
  ) THEN
    ALTER TABLE news_events DROP CONSTRAINT uq_news_source_url;
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_news_provider_url'
  ) THEN
    ALTER TABLE news_events ADD CONSTRAINT uq_news_provider_url UNIQUE (provider, url);
  END IF;
END$$;

DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM pg_class
    WHERE relname = 'idx_news_source'
  ) THEN
    DROP INDEX idx_news_source;
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_class
    WHERE relname = 'idx_news_provider'
  ) THEN
    CREATE INDEX idx_news_provider ON news_events (provider);
  END IF;
END$$;
