import os
from datetime import datetime, timezone
from uuid import uuid4

import psycopg2
import pytest

from jobs.publisher import publish_job


@pytest.fixture()
def db_conn():
    host = os.getenv("POSTGRES_HOST")
    port = int(os.getenv("POSTGRES_PORT", "5432"))
    name = os.getenv("POSTGRES_DB")
    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    if not all([host, name, user, password]):
        pytest.skip("POSTGRES_* env vars not set")
    conn = psycopg2.connect(
        host=host,
        port=port,
        dbname=name,
        user=user,
        password=password,
    )
    try:
        yield conn
    finally:
        conn.close()


def test_publish_job_dedup(db_conn):
    news_id = f"test-{uuid4()}"
    trace_id = uuid4()
    now = datetime.now(timezone.utc)

    with db_conn.cursor() as cursor:
        cursor.execute(
            "INSERT INTO news_events (news_id, trace_id, source, published_at, ingested_at, title, url, content, tickers, raw_payload) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (
                news_id,
                str(trace_id),
                "finnhub",
                now,
                now,
                "Test title",
                f"https://example.com/{news_id}",
                None,
                [],
                {},
            ),
        )
    db_conn.commit()

    first = publish_job(db_conn, news_id, trace_id)
    second = publish_job(db_conn, news_id, trace_id)
    assert first is True
    assert second is False

    with db_conn.cursor() as cursor:
        cursor.execute(
            "SELECT COUNT(*) FROM analysis_jobs WHERE news_id = %s AND job_type = %s",
            (news_id, "llm_analysis"),
        )
        count = cursor.fetchone()[0]
    assert count == 1

    with db_conn.cursor() as cursor:
        cursor.execute("DELETE FROM analysis_jobs WHERE news_id = %s", (news_id,))
        cursor.execute("DELETE FROM news_events WHERE news_id = %s", (news_id,))
    db_conn.commit()
