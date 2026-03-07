from datetime import datetime, timezone
from uuid import uuid4

import pytest

from ingestion.company_news_normalizer import NormalizationError, normalize_finnhub


def test_company_news_normalization_provider_publisher():
    trace_id = uuid4()
    ingested_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
    item = {
        "headline": "Earnings beat",
        "summary": "Company beats expectations",
        "datetime": 1704067200,
        "url": "https://example.com/article",
        "source": "Reuters",
        "related": "AAPL",
    }

    event = normalize_finnhub(item, trace_id, ingested_at, request_ticker="AAPL")

    assert event.provider == "finnhub"
    assert event.publisher == "Reuters"
    assert event.primary_symbol == "AAPL"


def test_company_news_normalization_null_publisher():
    trace_id = uuid4()
    ingested_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
    item = {
        "headline": "No publisher",
        "summary": "Publisher missing",
        "datetime": 1704067200,
        "url": "https://example.com/no-publisher",
        "related": "MSFT",
    }

    event = normalize_finnhub(item, trace_id, ingested_at, request_ticker="MSFT")

    assert event.provider == "finnhub"
    assert event.publisher is None


def test_company_news_normalization_dedup_by_external_id():
    trace_id = uuid4()
    ingested_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
    base = {
        "id": 999,
        "headline": "Same id",
        "summary": "Different urls",
        "datetime": 1704067200,
        "source": "Reuters",
        "related": "AAPL",
    }
    item_a = {**base, "url": "https://example.com/a"}
    item_b = {**base, "url": "https://example.com/b"}

    event_a = normalize_finnhub(item_a, trace_id, ingested_at, request_ticker="AAPL")
    event_b = normalize_finnhub(item_b, trace_id, ingested_at, request_ticker="AAPL")

    assert event_a.news_id == event_b.news_id


def test_company_news_normalization_requires_fields():
    trace_id = uuid4()
    ingested_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
    item = {
        "headline": "Missing URL",
        "datetime": 1704067200,
    }

    with pytest.raises(NormalizationError):
        normalize_finnhub(item, trace_id, ingested_at, request_ticker="MSFT")
