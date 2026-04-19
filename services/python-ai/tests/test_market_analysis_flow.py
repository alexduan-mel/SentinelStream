import hashlib
import logging
import os
from datetime import datetime, timezone
from uuid import uuid4

import psycopg2
import pytest

from jobs import market_analysis_worker as worker
from llm.interface import LLMClient, LLMProviderResponse
import analysis.service as analysis_service


class FakeProvider:
    name = "fake"
    model = "fake-model"

    def __init__(self, outputs):
        self._outputs = list(outputs)

    def generate(self, prompt: str, timeout_seconds: int) -> LLMProviderResponse:
        next_item = self._outputs.pop(0)
        return LLMProviderResponse(output_text=next_item, response=None)


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


def _insert_market_event(conn) -> int:
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
                "Chip prices stabilized.",
                [],
                {},
                "market",
            ),
        )
        event_id = cursor.fetchone()[0]
    conn.commit()
    return event_id


def _insert_company_event(conn) -> int:
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
                "Company update",
                f"https://example.com/{news_id}",
                "Company results.",
                [],
                {},
                "company",
            ),
        )
        event_id = cursor.fetchone()[0]
    conn.commit()
    return event_id


def _insert_job(conn, news_event_id: int) -> int:
    with conn.cursor() as cursor:
        cursor.execute(
            "INSERT INTO analysis_jobs (news_event_id, trace_id, job_type) VALUES (%s, %s, %s) RETURNING id",
            (news_event_id, str(uuid4()), "llm_analysis_market"),
        )
        job_id = cursor.fetchone()[0]
    conn.commit()
    return job_id


def _fetch_analysis(conn, news_event_id: int):
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT status, sentiment, confidence, impact_score, summary, entities, raw_output, analysis_job_id, id "
            "FROM llm_analyses WHERE news_event_id = %s "
            "ORDER BY created_at DESC LIMIT 1",
            (news_event_id,),
        )
        return cursor.fetchone()


def _fetch_analysis_tickers(conn, analysis_id: int) -> list[str]:
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT ticker FROM analysis_tickers WHERE analysis_id = %s ORDER BY ticker",
            (analysis_id,),
        )
        rows = cursor.fetchall()
    return [row[0] for row in rows]


def _fetch_job_status(conn, news_event_id: int) -> str | None:
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT status FROM analysis_jobs WHERE news_event_id = %s",
            (news_event_id,),
        )
        row = cursor.fetchone()
    return row[0] if row else None


def _cleanup(conn, news_event_id: int) -> None:
    with conn.cursor() as cursor:
        cursor.execute("DELETE FROM news_events WHERE id = %s", (news_event_id,))
    conn.commit()


def _run_with_provider(monkeypatch, provider, max_retries=2):
    client = LLMClient(provider, timeout_seconds=5, max_retries=max_retries)
    monkeypatch.setattr(analysis_service, "load_llm_client", lambda: client)


def _run_worker_once(max_attempts: int = 1):
    with _db_conn() as conn:
        run_after_column = worker._get_run_after_column(conn)
        jobs = worker._claim_jobs(
            conn,
            10,
            "test",
            max_attempts,
            run_after_column,
            ("llm_analysis_market",),
        )
        worker._process_jobs(conn, jobs, logging.getLogger("test"), max_attempts, run_after_column)


def test_market_analysis_flow(monkeypatch):
    output = (
        '{"main_topic":"Memory pricing","topic_key":"dram_pricing","topic_type":"sector",'
        '"direction":"mixed","summary":"Chip prices stabilized.",'
        '"affected_assets":['
        '{"symbol":"MU","asset_type":"equity","relation":"positive","confidence":0.9},'
        '{"symbol":"WDC","asset_type":"equity","relation":"mixed","confidence":0.5}'
        '],'
        '"market_relevance_score":0.72}'
    )
    provider = FakeProvider([output])

    with _db_conn() as conn:
        news_event_id = _insert_market_event(conn)
        job_id = _insert_job(conn, news_event_id)

    _run_with_provider(monkeypatch, provider, max_retries=2)
    _run_worker_once(max_attempts=1)

    with _db_conn() as conn:
        row = _fetch_analysis(conn, news_event_id)
        assert row[0] == "succeeded"
        assert row[1] == "neutral"
        assert row[2] is None
        assert float(row[3]) == 0.72
        assert row[4] == "Chip prices stabilized."
        entities = row[5]
        raw_output = row[6]
        assert row[7] == job_id
        analysis_id = row[8]
        entities_sorted = sorted(entities, key=lambda item: item["symbol"])
        assert entities_sorted == [
            {"symbol": "MU", "confidence": 0.9},
            {"symbol": "WDC", "confidence": 0.5},
        ]
        assert raw_output["normalized"]["topic_key"] == "memory_pricing"
        assert _fetch_analysis_tickers(conn, analysis_id) == []
        assert _fetch_job_status(conn, news_event_id) == "done"
        _cleanup(conn, news_event_id)


def test_market_worker_skips_company_event():
    with _db_conn() as conn:
        news_event_id = _insert_company_event(conn)
        _insert_job(conn, news_event_id)

    _run_worker_once(max_attempts=1)

    with _db_conn() as conn:
        assert _fetch_job_status(conn, news_event_id) == "failed"
        row = _fetch_analysis(conn, news_event_id)
        assert row is None
        _cleanup(conn, news_event_id)
