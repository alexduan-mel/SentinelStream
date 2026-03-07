from __future__ import annotations

from psycopg2.extras import Json

from ingestion.models import NewsEvent


def upsert_news_event(conn, event: NewsEvent) -> tuple[int, bool]:
    sql = (
        "INSERT INTO news_events (news_id, trace_id, source, request_ticker, published_at, ingested_at, "
        "title, url, content, tickers, raw_payload) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) "
        "ON CONFLICT (news_id) DO UPDATE SET news_id = EXCLUDED.news_id "
        "RETURNING id, (xmax = 0) AS inserted"
    )
    with conn.cursor() as cursor:
        cursor.execute(
            sql,
            (
                event.news_id,
                str(event.trace_id),
                event.source,
                event.request_ticker,
                event.published_at,
                event.ingested_at,
                event.title,
                event.url,
                event.content,
                event.tickers,
                Json(event.raw_payload),
            ),
        )
        row = cursor.fetchone()
        if not row:
            raise RuntimeError("Failed to upsert news_event")
        event_id = row[0]
        inserted = bool(row[1])
    conn.commit()
    return event_id, inserted
