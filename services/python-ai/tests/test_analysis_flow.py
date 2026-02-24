import hashlib
import logging
import os
from datetime import datetime, timezone
from uuid import uuid4

import psycopg2
import pytest

from jobs import worker
from llm.interface import LLMClient, ProviderError
import analysis.service as analysis_service


class FakeProvider:
    name = "fake"
    model = "fake-model"

    def __init__(self, outputs):
        self._outputs = list(outputs)

    def generate(self, prompt: str, timeout_seconds: int) -> str:
        next_item = self._outputs.pop(0)
        if isinstance(next_item, Exception):
            raise next_item
        return next_item


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
            "INSERT INTO news_events (news_id, trace_id, source, published_at, ingested_at, title, url, content, tickers, raw_payload) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id",
            (
                news_id,
                str(uuid4()),
                "finnhub",
                now,
                now,
                "Test title",
                f"https://example.com/{news_id}",
                "Body",
                [],
                {},
            ),
        )
        event_id = cursor.fetchone()[0]
    conn.commit()
    return event_id


def _insert_job(conn, news_event_id: int) -> None:
    with conn.cursor() as cursor:
        cursor.execute(
            "INSERT INTO analysis_jobs (news_event_id, trace_id, job_type) VALUES (%s, %s, %s)",
            (news_event_id, str(uuid4()), "llm_analysis"),
        )
    conn.commit()


def _fetch_analysis(conn, news_event_id: int):
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT status, sentiment, confidence, summary, error_message, raw_output, id "
            "FROM llm_analyses WHERE news_event_id = %s",
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
        jobs = worker._claim_jobs(conn, 10, "test", max_attempts, run_after_column)
        worker._process_jobs(conn, jobs, logging.getLogger("test"), max_attempts, run_after_column)


def test_happy_path(monkeypatch):
    output = '{"tickers":["AAPL","MSFT"],"sentiment":"positive","confidence":0.9,"reasoning_summary":"Strong demand."}'
    provider = FakeProvider([output])

    with _db_conn() as conn:
        news_event_id = _insert_news_event(conn)
        _insert_job(conn, news_event_id)

    _run_with_provider(monkeypatch, provider, max_retries=2)
    _run_worker_once(max_attempts=1)

    with _db_conn() as conn:
        row = _fetch_analysis(conn, news_event_id)
        assert row[0] == "succeeded"
        assert row[1] == "positive"
        assert float(row[2]) == 0.9
        assert row[3] == "Strong demand."
        raw_output = row[5]
        analysis_id = row[6]
        assert isinstance(raw_output, list)
        assert len(raw_output) == 1
        assert _fetch_analysis_tickers(conn, analysis_id) == ["AAPL", "MSFT"]
        assert _fetch_job_status(conn, news_event_id) == "done"
        _cleanup(conn, news_event_id)


def test_invalid_json_retries_and_fails(monkeypatch):
    provider = FakeProvider(["not-json", "still-bad", "nope"])
    with _db_conn() as conn:
        news_event_id = _insert_news_event(conn)
        _insert_job(conn, news_event_id)
    _run_with_provider(monkeypatch, provider, max_retries=2)
    _run_worker_once(max_attempts=1)

    with _db_conn() as conn:
        row = _fetch_analysis(conn, news_event_id)
        assert row[0] == "failed"
        assert row[4]
        raw_output = row[5]
        assert isinstance(raw_output, list)
        assert len(raw_output) == 3
        assert _fetch_job_status(conn, news_event_id) == "failed"
        _cleanup(conn, news_event_id)


def test_schema_validation_retries_and_fails(monkeypatch):
    bad = '{"tickers":["AAPL"],"sentiment":"positive","confidence":2,"reasoning_summary":"bad"}'
    provider = FakeProvider([bad, bad, bad])
    with _db_conn() as conn:
        news_event_id = _insert_news_event(conn)
        _insert_job(conn, news_event_id)
    _run_with_provider(monkeypatch, provider, max_retries=2)
    _run_worker_once(max_attempts=1)

    with _db_conn() as conn:
        row = _fetch_analysis(conn, news_event_id)
        assert row[0] == "failed"
        raw_output = row[5]
        assert isinstance(raw_output, list)
        assert len(raw_output) == 3
        assert _fetch_job_status(conn, news_event_id) == "failed"
        _cleanup(conn, news_event_id)


def test_timeout_retries_and_fails(monkeypatch):
    provider = FakeProvider([TimeoutError("timeout"), TimeoutError("timeout"), TimeoutError("timeout")])
    with _db_conn() as conn:
        news_event_id = _insert_news_event(conn)
        _insert_job(conn, news_event_id)
    _run_with_provider(monkeypatch, provider, max_retries=2)
    _run_worker_once(max_attempts=1)

    with _db_conn() as conn:
        row = _fetch_analysis(conn, news_event_id)
        assert row[0] == "failed"
        raw_output = row[5]
        assert isinstance(raw_output, list)
        assert len(raw_output) == 3
        assert _fetch_job_status(conn, news_event_id) == "failed"
        _cleanup(conn, news_event_id)


def test_non_retryable_error(monkeypatch):
    provider = FakeProvider([ProviderError("quota", code="insufficient_quota")])
    with _db_conn() as conn:
        news_event_id = _insert_news_event(conn)
        _insert_job(conn, news_event_id)
    _run_with_provider(monkeypatch, provider, max_retries=2)
    _run_worker_once(max_attempts=1)

    with _db_conn() as conn:
        row = _fetch_analysis(conn, news_event_id)
        assert row[0] == "failed"
        raw_output = row[5]
        assert isinstance(raw_output, list)
        assert len(raw_output) == 1
        assert _fetch_job_status(conn, news_event_id) == "failed"
        _cleanup(conn, news_event_id)
