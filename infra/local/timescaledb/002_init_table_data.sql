-- ============================================================
-- SentinelStream - Seed table data (optional)
-- ============================================================
-- 1) Tickers seed data

INSERT INTO tickers (symbol, name, exchange)
VALUES
  ('AAPL', 'Apple Inc.', 'NASDAQ'),
  ('GOOGL', 'Alphabet Inc. (Google)', 'NASDAQ'),
  ('MSFT', 'Microsoft Corporation', 'NASDAQ')
ON CONFLICT (symbol) DO NOTHING;
