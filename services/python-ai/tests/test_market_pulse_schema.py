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


def _insert_topic(conn) -> int:
    now = datetime.now(timezone.utc)
    with conn.cursor() as cursor:
        cursor.execute(
            "INSERT INTO market_pulse_topics "
            "(topic_key, display_name, topic_family, sector, subtopic, topic_type, direction, summary, status, "
            "evidence_count, first_seen_at, last_seen_at, strength_score) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id",
            (
                f"memory_pricing_{uuid4().hex[:8]}",
                "Memory pricing",
                "information_technology",
                "information_technology",
                "semiconductors",
                "sector",
                "neutral",
                "Prices stabilized",
                "active",
                1,
                now,
                now,
                0.8,
            ),
        )
        topic_id = cursor.fetchone()[0]
    conn.commit()
    return topic_id


def test_market_pulse_tables_exist():
    with _db_conn() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_name IN ("
                "'market_pulse_topics',"
                "'market_pulse_topic_mentions',"
                "'market_pulse_asset_links'"
                ")"
            )
            tables = {row[0] for row in cursor.fetchall()}
        assert tables == {
            "market_pulse_topics",
            "market_pulse_topic_mentions",
            "market_pulse_asset_links",
        }

def test_mentions_reference_topic():
    with _db_conn() as conn:
        news_event_id = _insert_news_event(conn)
        topic_id = _insert_topic(conn)

        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO market_pulse_topic_mentions "
                "(topic_id, news_event_id, topic_family, sector, subtopic, relevance_score) "
                "VALUES (%s, %s, %s, %s, %s, %s) RETURNING id",
                (topic_id, news_event_id, "information_technology", "information_technology", "semiconductors", 0.7),
            )
            topic_mention_id = cursor.fetchone()[0]
        conn.commit()

        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT topic_id FROM market_pulse_topic_mentions WHERE id = %s",
                (topic_mention_id,),
            )
            assert cursor.fetchone() == (topic_id,)

        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM market_pulse_topic_mentions WHERE id = %s", (topic_mention_id,))
            cursor.execute("DELETE FROM market_pulse_topics WHERE id = %s", (topic_id,))
            cursor.execute("DELETE FROM news_events WHERE id = %s", (news_event_id,))
        conn.commit()


def test_mentions_require_topic():
    with _db_conn() as conn:
        news_event_id = _insert_news_event(conn)
        with conn.cursor() as cursor:
            with pytest.raises(psycopg2.Error):
                cursor.execute(
                    "INSERT INTO market_pulse_topic_mentions "
                    "(news_event_id, topic_family, sector, subtopic, relevance_score) "
                    "VALUES (%s, %s, %s, %s, %s)",
                    (news_event_id, "macro", "macro", "growth", 0.4),
                )
        conn.rollback()
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM news_events WHERE id = %s", (news_event_id,))
        conn.commit()


def test_asset_link_unique_constraint():
    with _db_conn() as conn:
        topic_id = _insert_topic(conn)
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO market_pulse_asset_links "
                "(topic_id, asset_symbol, asset_type, relation_type, confidence_score) "
                "VALUES (%s, %s, %s, %s, %s)",
                (topic_id, "MU", "equity", "affected", 0.8),
            )
            with pytest.raises(psycopg2.Error):
                cursor.execute(
                    "INSERT INTO market_pulse_asset_links "
                    "(topic_id, asset_symbol, asset_type, relation_type, confidence_score) "
                    "VALUES (%s, %s, %s, %s, %s)",
                    (topic_id, "MU", "equity", "affected", 0.7),
                )
        conn.rollback()
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM market_pulse_asset_links WHERE topic_id = %s", (topic_id,))
            cursor.execute("DELETE FROM market_pulse_topics WHERE id = %s", (topic_id,))
        conn.commit()


def test_status_constraints():
    with _db_conn() as conn:
        now = datetime.now(timezone.utc)
        with conn.cursor() as cursor:
            with pytest.raises(psycopg2.Error):
                cursor.execute(
                    "INSERT INTO market_pulse_topics "
                    "(topic_key, display_name, topic_family, status, evidence_count, first_seen_at, last_seen_at) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                    (f"bad_{uuid4().hex[:8]}", "Bad", "macro", "invalid", 0, now, now),
                )
        conn.rollback()
