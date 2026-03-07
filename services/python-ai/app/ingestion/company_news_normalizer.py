from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from ingestion.models import NewsEvent
from ingestion.url_utils import canonicalize_url


class NormalizationError(ValueError):
    pass


COMPANY_NEWS_SCOPE = "company"
COMPANY_NEWS_EVENT_TYPE = "company_news"


def _parse_related(related: str | None) -> list[str]:
    if not related:
        return []
    items = [item.strip().upper() for item in related.split(",")]
    return [item for item in items if item]


def _dedupe_preserve(items: list[str]) -> list[str]:
    return list(dict.fromkeys(items))


def _derive_primary_symbol(request_symbol: str | None, item: dict[str, Any], related: list[str]) -> str | None:
    if request_symbol:
        return request_symbol
    symbol = item.get("symbol")
    if isinstance(symbol, str):
        symbol = symbol.strip().upper() or None
    else:
        symbol = None
    if symbol:
        return symbol
    if len(related) == 1:
        return related[0]
    return None


def _parse_timestamp(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(int(value), tz=timezone.utc)
    if isinstance(value, str):
        if value.isdigit():
            return datetime.fromtimestamp(int(value), tz=timezone.utc)
        iso = value.strip()
        if iso.endswith("Z"):
            iso = iso[:-1] + "+00:00"
        try:
            parsed = datetime.fromisoformat(iso)
        except ValueError:
            return None
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed
    return None


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _dedup_company_news_key(
    provider: str,
    source_event_id: str | None,
    canonical_url: str | None,
    title: str,
    published_at: datetime,
) -> str:
    if source_event_id:
        return _sha256(f"{provider}|{source_event_id}")
    if canonical_url:
        return _sha256(f"{provider}|{canonical_url}")
    published_str = published_at.isoformat() if published_at else ""
    return _sha256(f"{provider}|{title}|{published_str}")


def normalize_finnhub(
    item: dict[str, Any],
    trace_id: UUID,
    ingested_at: datetime,
    request_ticker: str | None = None,
) -> NewsEvent:
    url = item.get("url")
    headline = item.get("headline") or item.get("title")
    timestamp = item.get("datetime") or item.get("published_at")
    published_at = _parse_timestamp(timestamp)

    if not url or not headline or not published_at:
        raise NormalizationError("Missing required fields: url/headline/datetime")

    canonical_url = canonicalize_url(url)

    content = item.get("summary") or item.get("content")
    if isinstance(content, str):
        content = content.strip() or None
    else:
        content = None

    related = _parse_related(item.get("related"))
    request_symbol = request_ticker or item.get("request_ticker")
    if isinstance(request_symbol, str):
        request_symbol = request_symbol.strip().upper() or None
    else:
        request_symbol = None
    tickers = _dedupe_preserve(related)

    provider = "finnhub"
    publisher = item.get("source") if isinstance(item.get("source"), str) else None
    if isinstance(publisher, str):
        publisher = publisher.strip() or None
    source_event_id = item.get("id")
    if source_event_id is not None:
        source_event_id = str(source_event_id)
    else:
        source_event_id = None
    news_id = _dedup_company_news_key(provider, source_event_id, canonical_url, headline, published_at)
    primary_symbol = _derive_primary_symbol(request_symbol, item, tickers)

    return NewsEvent(
        news_id=news_id,
        trace_id=trace_id,
        provider=provider,
        publisher=publisher,
        request_ticker=request_symbol,
        source_event_id=source_event_id,
        scope=COMPANY_NEWS_SCOPE,
        event_type=COMPANY_NEWS_EVENT_TYPE,
        primary_symbol=primary_symbol,
        published_at=published_at,
        ingested_at=ingested_at,
        title=headline,
        url=canonical_url,
        content=content,
        tickers=tickers,
        raw_payload=item,
    )
