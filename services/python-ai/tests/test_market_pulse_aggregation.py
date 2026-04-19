import hashlib
import os
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import psycopg2
import pytest
from psycopg2.extras import Json

from market_pulse.aggregation import aggregate_market_pulse, build_topic_key


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


def _insert_analysis(conn, news_event_id: int, payload: dict, impact_score: float | None) -> int:
    raw_output = {"normalized": payload}
    with conn.cursor() as cursor:
        cursor.execute(
            "INSERT INTO llm_analyses (news_event_id, trace_id, provider, model, status, raw_output, impact_score) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id",
            (
                news_event_id,
                str(uuid4()),
                "openai",
                "gpt-4o-mini",
                "succeeded",
                Json(raw_output),
                impact_score,
            ),
        )
        analysis_id = cursor.fetchone()[0]
    conn.commit()
    return analysis_id


def _cleanup(conn, news_event_ids: list[int]) -> None:
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT DISTINCT topic_id "
            "FROM market_pulse_topic_mentions WHERE news_event_id = ANY(%s)",
            (news_event_ids,),
        )
        rows = cursor.fetchall()
        topic_ids = [row[0] for row in rows if row[0] is not None]
        cursor.execute(
            "DELETE FROM market_pulse_topic_mentions WHERE news_event_id = ANY(%s)",
            (news_event_ids,),
        )
        if topic_ids:
            cursor.execute(
                "DELETE FROM market_pulse_asset_links WHERE topic_id = ANY(%s)",
                (topic_ids,),
            )
            cursor.execute("DELETE FROM market_pulse_topics WHERE id = ANY(%s)", (topic_ids,))
        cursor.execute("DELETE FROM llm_analyses WHERE news_event_id = ANY(%s)", (news_event_ids,))
        cursor.execute("DELETE FROM news_events WHERE id = ANY(%s)", (news_event_ids,))
    conn.commit()


def _payload(
    sector: str,
    subtopic: str,
    subtopic_label: str,
    summary: str,
    relevance: float,
    assets=None,
) -> dict:
    return {
        "sector": sector,
        "subtopic": subtopic,
        "subtopic_label": subtopic_label,
        "topic_type": "macro",
        "direction": "neutral",
        "summary": summary,
        "affected_assets": assets or [],
        "market_relevance_score": relevance,
    }


def test_low_relevance_skipped():
    os.environ["MARKET_PULSE_MIN_RELEVANCE"] = "0.35"
    now = datetime.now(timezone.utc)

    with _db_conn() as conn:
        event_id = _insert_news_event(conn, now - timedelta(hours=1))
        _insert_analysis(conn, event_id, _payload("macro", "geopolitics", "low relevance", "Minor update", 0.2), 0.2)

        aggregate_market_pulse(conn, now=now)

        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM market_pulse_topics")
            assert cursor.fetchone()[0] == 0
            cursor.execute("SELECT COUNT(*) FROM market_pulse_topic_mentions")
            assert cursor.fetchone()[0] == 0

        _cleanup(conn, [event_id])


def test_topic_key_generation():
    assert build_topic_key("macro", "geopolitics") == "macro__geopolitics"
    assert build_topic_key("energy", "other") == "energy__other"


def test_conflict_news_maps_to_macro_geopolitics():
    now = datetime.now(timezone.utc)
    with _db_conn() as conn:
        event_id = _insert_news_event(conn, now - timedelta(hours=1))
        _insert_analysis(
            conn,
            event_id,
            _payload("macro", "geopolitics", "Iran conflict", "Escalation in gulf", 0.7),
            0.7,
        )

        aggregate_market_pulse(conn, now=now)

        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT id FROM market_pulse_topics WHERE topic_key = %s",
                ("macro__geopolitics",),
            )
            assert cursor.fetchone() is not None

        _cleanup(conn, [event_id])


def test_oil_conflict_maps_to_energy_oil():
    now = datetime.now(timezone.utc)
    with _db_conn() as conn:
        event_id = _insert_news_event(conn, now - timedelta(hours=1))
        _insert_analysis(
            conn,
            event_id,
            _payload("energy", "oil", "Oil supply risk", "Supply disruption risk", 0.7),
            0.7,
        )

        aggregate_market_pulse(conn, now=now)

        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT id FROM market_pulse_topics WHERE topic_key = %s",
                ("energy__oil",),
            )
            assert cursor.fetchone() is not None

        _cleanup(conn, [event_id])


def test_uncategorized_news_maps_to_sector_other():
    now = datetime.now(timezone.utc)
    with _db_conn() as conn:
        event_id = _insert_news_event(conn, now - timedelta(hours=1))
        _insert_analysis(
            conn,
            event_id,
            _payload("utilities", "other", "Regulatory update", "Regulatory change impact", 0.6),
            0.6,
        )

        aggregate_market_pulse(conn, now=now)

        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT id FROM market_pulse_topics WHERE topic_key = %s",
                ("utilities__other",),
            )
            assert cursor.fetchone() is not None

        _cleanup(conn, [event_id])


def test_direct_topic_upsert_and_mentions():
    now = datetime.now(timezone.utc)
    with _db_conn() as conn:
        event1 = _insert_news_event(conn, now - timedelta(hours=2))
        event2 = _insert_news_event(conn, now - timedelta(hours=1))
        _insert_analysis(
            conn,
            event1,
            _payload("macro", "geopolitics", "Iran conflict", "Escalation risk", 0.7),
            0.7,
        )
        _insert_analysis(
            conn,
            event2,
            _payload("macro", "geopolitics", "Regional conflict", "Escalation risk", 0.7),
            0.7,
        )

        aggregate_market_pulse(conn, now=now)

        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM market_pulse_topics WHERE topic_key = %s", ("macro__geopolitics",))
            assert cursor.fetchone()[0] == 1
            cursor.execute(
                "SELECT COUNT(*) FROM market_pulse_topic_mentions WHERE topic_id = "
                "(SELECT id FROM market_pulse_topics WHERE topic_key = %s)",
                ("macro__geopolitics",),
            )
            assert cursor.fetchone()[0] >= 2

        _cleanup(conn, [event1, event2])


def test_idempotent_mentions_and_assets():
    now = datetime.now(timezone.utc)
    assets = [{"symbol": "MU", "asset_type": "equity", "relation": "positive", "confidence": 0.9}]

    with _db_conn() as conn:
        event1 = _insert_news_event(conn, now - timedelta(hours=2))
        event2 = _insert_news_event(conn, now - timedelta(hours=1))
        _insert_analysis(
            conn,
            event1,
            _payload("information_technology", "semiconductors", "Memory pricing", "Demand steady", 0.8, assets),
            0.8,
        )
        _insert_analysis(
            conn,
            event2,
            _payload("information_technology", "semiconductors", "Memory pricing", "Prices stable", 0.8, assets),
            0.8,
        )

        aggregate_market_pulse(conn, now=now)
        aggregate_market_pulse(conn, now=now)

        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM market_pulse_topic_mentions")
            mentions = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM market_pulse_asset_links")
            assets_count = cursor.fetchone()[0]
        assert mentions >= 2
        assert assets_count == 1

        _cleanup(conn, [event1, event2])


def test_mentions_attach_directly_to_topics():
    now = datetime.now(timezone.utc)
    with _db_conn() as conn:
        event1 = _insert_news_event(conn, now - timedelta(hours=1))
        analysis1 = _insert_analysis(
            conn,
            event1,
            _payload("macro", "central_banks", "Fed policy shift", "Policy easing", 0.7),
            0.7,
        )

        aggregate_market_pulse(conn, now=now)

        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT topic_id FROM market_pulse_topic_mentions WHERE llm_analysis_id = %s",
                (analysis1,),
            )
            rows1 = cursor.fetchall()
            assert any(row[0] is not None for row in rows1)

        _cleanup(conn, [event1])
