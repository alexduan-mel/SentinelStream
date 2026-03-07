from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from ingestion.models import NewsEvent
from ingestion.url_utils import canonicalize_url

MARKET_NEWS_SCOPE = "market"
MARKET_NEWS_EVENT_TYPE = "market_news"
DEFAULT_PROVIDER = "finnhub"


class MarketNewsParseError(ValueError):
    pass


class MarketNewsNormalizationError(ValueError):
    pass


def parse_market_news_payload(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        for key in ("news", "data"):
            items = payload.get(key)
            if isinstance(items, list):
                return [item for item in items if isinstance(item, dict)]
    raise MarketNewsParseError(f"Unexpected market news payload: {payload}")


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
        return parsed.astimezone(timezone.utc)
    return None


def _parse_related(related: str | None) -> list[str]:
    if not related:
        return []
    items = [item.strip().upper() for item in related.split(",")]
    return [item for item in items if item]


def _dedupe_preserve(items: list[str]) -> list[str]:
    return list(dict.fromkeys(items))


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _derive_primary_symbol(item: dict[str, Any], related: list[str]) -> str | None:
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


def dedup_market_news_key(
    provider: str,
    source_event_id: str | None,
    canonical_url: str | None,
    title: str | None,
    published_at: datetime | None,
) -> str:
    if source_event_id:
        return _sha256(f"{provider}|{source_event_id}")
    if canonical_url:
        return _sha256(f"{provider}|{canonical_url}")
    published_str = published_at.isoformat() if published_at else ""
    return _sha256(f"{provider}|{title or ''}|{published_str}")


def normalize_market_news_item(
    item: dict[str, Any],
    trace_id: UUID,
    ingested_at: datetime,
    category: str,
    provider: str = DEFAULT_PROVIDER,
) -> NewsEvent:
    url = item.get("url")
    headline = item.get("headline") or item.get("title")
    timestamp = item.get("datetime") or item.get("published_at")
    published_at = _parse_timestamp(timestamp)

    if not url or not headline or not published_at:
        raise MarketNewsNormalizationError("Missing required fields: url/headline/datetime")

    try:
        canonical_url = canonicalize_url(str(url))
    except ValueError as exc:
        raise MarketNewsNormalizationError("Invalid url") from exc

    content = item.get("summary") or item.get("description") or item.get("content")
    if isinstance(content, str):
        content = content.strip() or None
    else:
        content = None

    related_value = item.get("related")
    related = _parse_related(related_value if isinstance(related_value, str) else None)
    tickers = _dedupe_preserve(related)
    primary_symbol = _derive_primary_symbol(item, tickers)

    source_event_id = item.get("id")
    if source_event_id is not None:
        source_event_id = str(source_event_id)
    else:
        source_event_id = None

    news_id = dedup_market_news_key(provider, source_event_id, canonical_url, str(headline), published_at)

    raw_payload = {
        "item": item,
        "_meta": {
            "category": category,
            "fetched_at": ingested_at.isoformat(),
            "dedup_key": news_id,
            "scope": MARKET_NEWS_SCOPE,
            "event_type": MARKET_NEWS_EVENT_TYPE,
        },
    }

    publisher = item.get("source") if isinstance(item.get("source"), str) else None
    if isinstance(publisher, str):
        publisher = publisher.strip() or None

    return NewsEvent(
        news_id=news_id,
        trace_id=trace_id,
        provider=provider,
        publisher=publisher,
        request_ticker=None,
        source_event_id=source_event_id,
        scope=MARKET_NEWS_SCOPE,
        event_type=MARKET_NEWS_EVENT_TYPE,
        primary_symbol=primary_symbol,
        published_at=published_at,
        ingested_at=ingested_at,
        title=str(headline),
        url=canonical_url,
        content=content,
        tickers=tickers,
        raw_payload=raw_payload,
    )
