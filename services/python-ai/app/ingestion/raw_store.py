from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Iterable
from uuid import UUID

from psycopg2.extras import Json, execute_values

from ingestion.url_utils import canonicalize_url


@dataclass(frozen=True)
class RawNewsRow:
    raw_id: str
    raw_payload: dict[str, Any]


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


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


def _dedup_key(source: str, url: str | None, title: str | None, published_at: datetime | None) -> str:
    if url:
        return _sha256(f"{source}|{url}")
    published_str = published_at.isoformat() if published_at else ""
    return _sha256(f"{source}|{title or ''}|{published_str}")


def insert_raw_items(
    conn,
    source: str,
    trace_id: UUID,
    fetched_at: datetime,
    items: Iterable[dict[str, Any]],
) -> tuple[int, int]:
    rows_by_key: dict[tuple[str, str], tuple] = {}
    for item in items:
        url = item.get("url")
        canonical_url = None
        if url:
            try:
                canonical_url = canonicalize_url(url)
            except ValueError:
                canonical_url = None
        title = item.get("headline") or item.get("title")
        published_at = _parse_timestamp(item.get("datetime") or item.get("published_at"))
        dedup_key = _dedup_key(source, canonical_url or url, title, published_at)
        rows_by_key[(source, dedup_key)] = (
            (
                source,
                str(trace_id),
                fetched_at,
                published_at,
                canonical_url or url,
                title,
                dedup_key,
                Json(item),
            )
        )

    rows = list(rows_by_key.values())
    if not rows:
        return 0, 0

    sql = (
        "INSERT INTO raw_news_items "
        "(source, trace_id, fetched_at, published_at, url, title, dedup_key, raw_payload) "
        "VALUES %s "
        "ON CONFLICT (source, dedup_key) DO UPDATE "
        "SET fetched_at = EXCLUDED.fetched_at, "
        "trace_id = EXCLUDED.trace_id, "
        "raw_payload = EXCLUDED.raw_payload "
        "RETURNING (xmax = 0) AS inserted"
    )

    with conn.cursor() as cursor:
        result = execute_values(cursor, sql, rows, fetch=True)
        inserted = sum(1 for row in result if row[0])
        updated = len(result) - inserted
    conn.commit()
    return inserted, updated


def select_raw_items(conn, source: str, limit: int) -> list[RawNewsRow]:
    sql = (
        "SELECT raw_id::text, raw_payload "
        "FROM raw_news_items "
        "WHERE source = %s "
        "AND status IN ('fetched','failed') "
        "AND attempts < 3 "
        "ORDER BY fetched_at DESC "
        "LIMIT %s"
    )
    with conn.cursor() as cursor:
        cursor.execute(sql, (source, limit))
        rows = cursor.fetchall()
    return [RawNewsRow(raw_id=row[0], raw_payload=row[1]) for row in rows]


def mark_raw_normalized(conn, raw_id: str) -> None:
    sql = (
        "UPDATE raw_news_items "
        "SET status = 'normalized', attempts = attempts + 1, last_error = NULL "
        "WHERE raw_id = %s"
    )
    with conn.cursor() as cursor:
        cursor.execute(sql, (raw_id,))
    conn.commit()


def mark_raw_failed(conn, raw_id: str, error: str) -> None:
    sql = (
        "UPDATE raw_news_items "
        "SET status = 'failed', attempts = attempts + 1, last_error = %s "
        "WHERE raw_id = %s"
    )
    with conn.cursor() as cursor:
        cursor.execute(sql, (error, raw_id))
    conn.commit()
