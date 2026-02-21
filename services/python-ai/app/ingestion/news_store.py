from __future__ import annotations

from typing import Iterable

from psycopg2.extras import Json, execute_values

from ingestion.models import NewsEvent


def insert_news_events(conn, events: Iterable[NewsEvent]) -> int:
    rows = [
        (
            event.news_id,
            str(event.trace_id),
            event.source,
            event.published_at,
            event.ingested_at,
            event.title,
            event.url,
            event.content,
            event.tickers,
            Json(event.raw_payload),
        )
        for event in events
    ]
    if not rows:
        return 0

    sql = (
        "INSERT INTO news_events (news_id, trace_id, source, published_at, ingested_at, "
        "title, url, content, tickers, raw_payload) "
        "VALUES %s "
        "ON CONFLICT (source, url) DO NOTHING "
        "RETURNING 1"
    )

    with conn.cursor() as cursor:
        result = execute_values(cursor, sql, rows, fetch=True)
        inserted = len(result)
    conn.commit()
    return inserted
