-- Indexes to support monitor snapshot query
CREATE INDEX IF NOT EXISTS idx_news_request_ticker_published_at
  ON news_events (request_ticker, published_at DESC);

CREATE INDEX IF NOT EXISTS idx_analysis_news_event_id
  ON llm_analyses (news_event_id);

CREATE INDEX IF NOT EXISTS idx_analysis_entities_gin
  ON llm_analyses USING GIN (entities);
