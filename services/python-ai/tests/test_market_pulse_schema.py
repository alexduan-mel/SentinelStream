import hashlib
import os
from datetime import datetime, timezone
from uuid import uuid4

import psycopg2
import pytest


def _db_conn():
    host = os.getenv("POSTGRES_HOST")
    port = int(os.getenv("POSTGRES_PORT", "5432"))
    name = os.getenv("POSTGRES_DB")
    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    if not all([host, name, user, password]):
        pytest.skip("POSTGRES_* env vars not set")
    return psycopg2.connect(
        host=host,
        port=port,
        dbname=name,
        user=user,
        password=password,
    )


def _insert_news_event(conn) -> int:
    news_id = hashlib.sha256(uuid4().hex.encode("utf-8")).hexdigest()
    now = datetime.now(timezone.utc)
    with conn.cursor() as cursor:
        cursor.execute(
            "INSERT INTO news_events (news_id, trace_id, provider, publisher, published_at, ingested_at, title, url, content, tickers, raw_payload, scope) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id",
            (
                news_id,
                str(uuid4()),
                "finnhub",
                "Reuters",
                now,
                now,
                "Market update",
                f"https://example.com/{news_id}",
                "Body",
                [],
                {},
                "market",
            ),
        )
        event_id = cursor.fetchone()[0]
    conn.commit()
    return event_id


def test_market_pulse_tables_exist_and_insert():
    with _db_conn() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_name IN ('market_pulse_topics','market_pulse_topic_mentions','market_pulse_asset_links')"
            )
            tables = {row[0] for row in cursor.fetchall()}
        assert tables == {
            "market_pulse_topics",
            "market_pulse_topic_mentions",
            "market_pulse_asset_links",
        }

        news_event_id = _insert_news_event(conn)
        now = datetime.now(timezone.utc)

        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO market_pulse_topics "
                "(topic_key, display_name, topic_type, direction, summary, intensity_score, confidence_score, "
                "evidence_count, status, first_seen_at, last_seen_at) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id",
                (
                    "memory_pricing",
                    "Memory pricing",
                    "sector",
                    "neutral",
                    "Prices stabilized",
                    0.6,
                    0.7,
                    1,
                    "new",
                    now,
                    now,
                ),
            )
            topic_id = cursor.fetchone()[0]

            cursor.execute(
                "INSERT INTO market_pulse_topic_mentions "
                "(topic_id, news_event_id, relevance_score, reasoning_summary) "
                "VALUES (%s, %s, %s, %s) RETURNING id",
                (
                    topic_id,
                    news_event_id,
                    0.8,
                    "Directly discussed pricing",
                ),
            )
            mention_id = cursor.fetchone()[0]

            cursor.execute(
                "INSERT INTO market_pulse_asset_links "
                "(topic_id, asset_symbol, asset_type, relation_type, confidence_score) "
                "VALUES (%s, %s, %s, %s, %s) RETURNING id",
                (
                    topic_id,
                    "MU",
                    "equity",
                    "impacted",
                    0.9,
                ),
            )
            asset_link_id = cursor.fetchone()[0]

        conn.commit()

        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT topic_id, news_event_id FROM market_pulse_topic_mentions WHERE id = %s",
                (mention_id,),
            )
            mention_row = cursor.fetchone()
            assert mention_row == (topic_id, news_event_id)

            cursor.execute(
                "SELECT topic_id, asset_symbol FROM market_pulse_asset_links WHERE id = %s",
                (asset_link_id,),
            )
            asset_row = cursor.fetchone()
            assert asset_row == (topic_id, "MU")

            cursor.execute("DELETE FROM market_pulse_asset_links WHERE topic_id = %s", (topic_id,))
            cursor.execute("DELETE FROM market_pulse_topic_mentions WHERE topic_id = %s", (topic_id,))
            cursor.execute("DELETE FROM market_pulse_topics WHERE id = %s", (topic_id,))
            cursor.execute("DELETE FROM news_events WHERE id = %s", (news_event_id,))
        conn.commit()
