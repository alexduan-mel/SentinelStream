from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from ingestion.models import NewsEvent
from ingestion.url_utils import canonicalize_url, generate_news_id


class NormalizationError(ValueError):
    pass


def _parse_related(related: str | None) -> list[str]:
    if not related:
        return []
    items = [item.strip().upper() for item in related.split(",")]
    return [item for item in items if item]


def _dedupe_preserve(items: list[str]) -> list[str]:
    return list(dict.fromkeys(items))


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

    source = item.get("source") or "finnhub"
    news_id = generate_news_id(source, canonical_url)

    return NewsEvent(
        news_id=news_id,
        trace_id=trace_id,
        source=source,
        request_ticker=request_symbol,
        published_at=published_at,
        ingested_at=ingested_at,
        title=headline,
        url=canonical_url,
        content=content,
        tickers=tickers,
        raw_payload=item,
    )
