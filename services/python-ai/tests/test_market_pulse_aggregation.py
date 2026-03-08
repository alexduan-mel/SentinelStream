import hashlib
import os
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import psycopg2
import pytest
from psycopg2.extras import Json

from market_pulse.aggregation import (
    _compute_intensity,
    _compute_status,
    _extract_topic_fields,
    aggregate_market_pulse,
)


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


def _insert_news_event(conn, published_at: datetime) -> int:
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
                published_at,
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


def _insert_analysis(
    conn,
    news_event_id: int,
    raw_output: dict,
    entities: list[dict],
    impact_score: float | None,
) -> int:
    with conn.cursor() as cursor:
        cursor.execute(
            "INSERT INTO llm_analyses (news_event_id, trace_id, provider, model, status, raw_output, entities, impact_score) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id",
            (
                news_event_id,
                str(uuid4()),
                "openai",
                "gpt-4o-mini",
                "succeeded",
                Json(raw_output),
                Json(entities),
                impact_score,
            ),
        )
        analysis_id = cursor.fetchone()[0]
    conn.commit()
    return analysis_id


def _cleanup(conn, news_event_ids: list[int]) -> None:
    with conn.cursor() as cursor:
        cursor.execute(
            "DELETE FROM market_pulse_asset_links WHERE topic_id IN "
            "(SELECT id FROM market_pulse_topics WHERE topic_key = %s)",
            ("memory_pricing",),
        )
        cursor.execute(
            "DELETE FROM market_pulse_topic_mentions WHERE topic_id IN "
            "(SELECT id FROM market_pulse_topics WHERE topic_key = %s)",
            ("memory_pricing",),
        )
        cursor.execute(
            "DELETE FROM market_pulse_topics WHERE topic_key = %s",
            ("memory_pricing",),
        )
        cursor.execute("DELETE FROM llm_analyses WHERE news_event_id = ANY(%s)", (news_event_ids,))
        cursor.execute("DELETE FROM news_events WHERE id = ANY(%s)", (news_event_ids,))
    conn.commit()


def test_extract_topic_fields():
    raw = {
        "normalized": {
            "topic_key": "memory_pricing",
            "main_topic": "Memory pricing",
            "topic_type": "sector",
            "direction": "neutral",
            "summary": "Prices stabilized",
        }
    }
    parsed = _extract_topic_fields(raw)
    assert parsed is not None
    assert parsed.topic_key == "memory_pricing"
    assert parsed.main_topic == "Memory pricing"


def test_status_and_intensity_helpers():
    now = datetime(2026, 3, 8, tzinfo=timezone.utc)
    status = _compute_status(now, now - timedelta(hours=2), 2, 2, 0)
    assert status == "new"
    status = _compute_status(now, now - timedelta(days=2), 5, 3, 1)
    assert status == "strengthening"
    status = _compute_status(now, now - timedelta(days=2), 5, 1, 2)
    assert status == "ongoing"

    intensity = _compute_intensity(0, 0.9)
    assert intensity == 0.0
    intensity = _compute_intensity(5, 0.5)
    assert 0.6 <= intensity <= 1.0


def test_market_pulse_aggregation_idempotent():
    now = datetime.now(timezone.utc)
    raw_output = {
        "normalized": {
            "topic_key": "memory_pricing",
            "main_topic": "Memory pricing",
            "topic_type": "sector",
            "direction": "neutral",
            "summary": "Prices stabilized",
        }
    }
    entities = [{"symbol": "MU", "confidence": 0.9}, {"symbol": "WDC", "confidence": 0.6}]

    with _db_conn() as conn:
        event1 = _insert_news_event(conn, now - timedelta(hours=2))
        event2 = _insert_news_event(conn, now - timedelta(hours=1))
        _insert_analysis(conn, event1, raw_output, entities, 0.7)
        _insert_analysis(conn, event2, raw_output, entities, 0.6)

        aggregate_market_pulse(conn, now=now)
        aggregate_market_pulse(conn, now=now)

        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*), MIN(evidence_count), MAX(status) FROM market_pulse_topics")
            topic_row = cursor.fetchone()
            assert topic_row[0] == 1
            assert topic_row[1] == 2
            assert topic_row[2] in {"new", "ongoing", "strengthening"}

            cursor.execute("SELECT COUNT(*) FROM market_pulse_topic_mentions")
            assert cursor.fetchone()[0] == 2

            cursor.execute("SELECT COUNT(*) FROM market_pulse_asset_links")
            assert cursor.fetchone()[0] == 2

        _cleanup(conn, [event1, event2])
