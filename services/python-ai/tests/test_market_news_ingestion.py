from datetime import datetime, timezone
from uuid import uuid4

import pytest

from ingestion.url_utils import canonicalize_url
from ingestion.market_news_ingestion import (
    MarketNewsParseError,
    dedup_market_news_key,
    normalize_market_news_item,
    parse_market_news_payload,
)


def test_parse_market_news_payload_list():
    payload = [{"headline": "Test"}]
    assert parse_market_news_payload(payload) == payload


def test_parse_market_news_payload_dict():
    payload = {"news": [{"headline": "Test"}]}
    assert parse_market_news_payload(payload) == payload["news"]


def test_parse_market_news_payload_invalid():
    with pytest.raises(MarketNewsParseError):
        parse_market_news_payload({"invalid": True})


def test_dedup_market_news_key_prefers_external_id():
    published_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
    key1 = dedup_market_news_key("finnhub", "123", "https://example.com/a", "A", published_at)
    key2 = dedup_market_news_key("finnhub", "123", "https://example.com/b", "B", published_at)
    assert key1 == key2


def test_normalize_market_news_item():
    trace_id = uuid4()
    ingested_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
    item = {
        "id": 456,
        "headline": "Market moves",
        "summary": "Stocks rallied",
        "datetime": 1704067200,
        "url": "https://example.com/article?utm_source=test",
        "source": "Bloomberg",
        "related": "AAPL, MSFT",
    }

    event = normalize_market_news_item(item, trace_id, ingested_at, "general")

    assert event.provider == "finnhub"
    assert event.publisher == "Bloomberg"
    assert event.scope == "market"
    assert event.event_type == "market_news"
    assert event.primary_symbol is None
    assert event.title == "Market moves"
    assert event.content == "Stocks rallied"
    assert event.url == canonicalize_url(item["url"])
    assert event.published_at == datetime.fromtimestamp(1704067200, tz=timezone.utc)
    assert event.tickers == ["AAPL", "MSFT"]
    assert event.raw_payload["item"]["source"] == "Bloomberg"


def test_normalize_market_news_primary_symbol_from_single_related():
    trace_id = uuid4()
    ingested_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
    item = {
        "headline": "Single symbol",
        "summary": "Only one ticker",
        "datetime": 1704067200,
        "url": "https://example.com/single",
        "related": "AAPL",
    }

    event = normalize_market_news_item(item, trace_id, ingested_at, "general")

    assert event.primary_symbol == "AAPL"


def test_normalize_market_news_null_publisher():
    trace_id = uuid4()
    ingested_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
    item = {
        "headline": "Publisher missing",
        "summary": "No source field",
        "datetime": 1704067200,
        "url": "https://example.com/no-source",
    }

    event = normalize_market_news_item(item, trace_id, ingested_at, "general")

    assert event.provider == "finnhub"
    assert event.publisher is None
