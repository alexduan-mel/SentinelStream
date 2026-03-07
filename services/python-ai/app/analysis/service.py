from __future__ import annotations

import logging
import os
from typing import Any
from uuid import uuid4

import psycopg2
from psycopg2.extensions import connection as PgConnection
from psycopg2.extras import Json, execute_values

from llm.factory import load_llm_client
from llm.interface import LLMAnalysisError, LLMClient, LLMRunAttempt


def connect_db() -> PgConnection:
    host = os.getenv("POSTGRES_HOST")
    port = int(os.getenv("POSTGRES_PORT", "5432"))
    name = os.getenv("POSTGRES_DB")
    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    missing = [key for key, value in {
        "POSTGRES_HOST": host,
        "POSTGRES_DB": name,
        "POSTGRES_USER": user,
        "POSTGRES_PASSWORD": password,
    }.items() if not value]
    if missing:
        raise RuntimeError(f"Missing DB environment variables: {', '.join(missing)}")
    conn = psycopg2.connect(
        host=host,
        port=port,
        dbname=name,
        user=user,
        password=password,
    )
    with conn.cursor() as cursor:
        cursor.execute("SET TIME ZONE 'UTC'")
    conn.commit()
    return conn


def _fetch_news_event(conn, news_event_id: int) -> dict[str, Any] | None:
    sql = (
        "SELECT id, title, url, content, source, published_at "
        "FROM news_events WHERE id = %s"
    )
    with conn.cursor() as cursor:
        cursor.execute(sql, (news_event_id,))
        row = cursor.fetchone()
    if not row:
        return None
    return {
        "id": row[0],
        "title": row[1],
        "url": row[2],
        "content": row[3],
        "source": row[4],
        "published_at": row[5],
    }


def _build_input_text(event: dict[str, Any]) -> str:
    parts = [f"Title: {event['title']}"]
    if event.get("url"):
        parts.append(f"URL: {event['url']}")
    if event.get("content"):
        parts.append(f"Content: {event['content']}")
    return "\n".join(parts)


def _upsert_analysis_pending(
    conn,
    news_event_id: int,
    trace_id: str,
    provider: str,
    model: str,
    request_payload: dict[str, Any] | None,
) -> int:
    sql = (
        "INSERT INTO llm_analyses (news_event_id, trace_id, provider, model, request, status, created_at, updated_at) "
        "VALUES (%s, %s, %s, %s, %s, 'pending', NOW(), NOW()) "
        "ON CONFLICT (news_event_id, provider, model) DO UPDATE SET "
        "trace_id = EXCLUDED.trace_id, status = 'pending', error_message = NULL, "
        "request = EXCLUDED.request, updated_at = NOW() "
        "RETURNING id"
    )
    with conn.cursor() as cursor:
        cursor.execute(
            sql,
            (
                news_event_id,
                trace_id,
                provider,
                model,
                Json(request_payload) if request_payload is not None else None,
            ),
        )
        analysis_id = cursor.fetchone()[0]
    conn.commit()
    return analysis_id


def _update_analysis_success(
    conn,
    analysis_id: int,
    result,
    raw_output: dict[str, Any],
    request_payload: dict[str, Any] | None,
) -> None:
    sql = (
        "UPDATE llm_analyses SET status = 'succeeded', updated_at = NOW(), "
        "sentiment = %s, confidence = %s, summary = %s, error_message = NULL, "
        "raw_output = %s, entities = %s, request = %s "
        "WHERE id = %s"
    )
    with conn.cursor() as cursor:
        cursor.execute(
            sql,
            (
                result.sentiment,
                result.confidence,
                result.reasoning_summary,
                Json(raw_output),
                Json(result.tickers),
                Json(request_payload) if request_payload is not None else None,
                analysis_id,
            ),
        )
    conn.commit()


def _update_analysis_failed(
    conn,
    analysis_id: int,
    error_message: str,
    raw_output: dict[str, Any],
    request_payload: dict[str, Any] | None,
) -> None:
    sql = (
        "UPDATE llm_analyses SET status = 'failed', updated_at = NOW(), "
        "error_message = %s, raw_output = %s, request = %s "
        "WHERE id = %s"
    )
    with conn.cursor() as cursor:
        cursor.execute(
            sql,
            (
                error_message,
                Json(raw_output),
                Json(request_payload) if request_payload is not None else None,
                analysis_id,
            ),
        )
    conn.commit()


def _build_raw_output(attempt: LLMRunAttempt | None) -> dict[str, Any]:
    if not attempt:
        return {
            "error": "no_attempts",
            "response": None,
            "output_text": None,
            "output_json": None,
        }
    return {
        "error": attempt.error,
        "response": attempt.response,
        "output_text": attempt.output_text,
        "output_json": attempt.output_json,
    }


def _replace_analysis_tickers(conn, analysis_id: int, tickers: list[str]) -> None:
    with conn.cursor() as cursor:
        cursor.execute("DELETE FROM analysis_tickers WHERE analysis_id = %s", (analysis_id,))
        if tickers:
            rows = [(analysis_id, ticker) for ticker in tickers]
            execute_values(
                cursor,
                "INSERT INTO analysis_tickers (analysis_id, ticker) VALUES %s",
                rows,
            )
    conn.commit()


def analyze_news_event(news_event_id: int) -> dict[str, Any]:
    logger = logging.getLogger(__name__)
    trace_id = str(uuid4())

    with connect_db() as conn:
        event = _fetch_news_event(conn, news_event_id)
        if not event:
            return {
                "status": "not_found",
                "error_message": "news_event_not_found",
            }

        try:
            client: LLMClient = load_llm_client()
            provider = client.provider_name
            model = client.model
        except Exception as exc:  # noqa: BLE001
            provider = "gemini"
            model = os.getenv("GEMINI_MODEL", "gemini-3-flash-preview")
            analysis_id = _upsert_analysis_pending(
                conn,
                news_event_id=news_event_id,
                trace_id=trace_id,
                provider=provider,
                model=model,
                request_payload=None,
            )
            _update_analysis_failed(
                conn,
                analysis_id,
                f"llm_init_error: {exc}",
                raw_output=_build_raw_output(None),
                request_payload=None,
            )
            return {
                "analysis_id": analysis_id,
                "status": "failed",
                "error_message": str(exc),
            }

        analysis_id = _upsert_analysis_pending(
            conn,
            news_event_id=news_event_id,
            trace_id=trace_id,
            provider=provider,
            model=model,
            request_payload=None,
        )

        input_text = _build_input_text(event)
        try:
            result = client.analyze_news(input_text)
            raw_output = client.last_raw_output or _build_raw_output(
                client.last_attempts[-1] if client.last_attempts else None
            )
            _update_analysis_success(
                conn,
                analysis_id,
                result,
                raw_output,
                request_payload=client.last_request,
            )
            _replace_analysis_tickers(conn, analysis_id, result.tickers)
            return {
                "analysis_id": analysis_id,
                "status": "succeeded",
                "result": result,
                "tickers": result.tickers,
                "provider": provider,
                "model": model,
            }
        except LLMAnalysisError as exc:
            last_attempt = exc.attempts[-1] if exc.attempts else None
            raw_output = _build_raw_output(last_attempt)
            last_error = exc.attempts[-1].error if exc.attempts else str(exc)
            error_message = f"{exc}: {last_error}" if last_error else str(exc)
            logger.error("llm_analysis_failed news_event_id=%s error=%s", news_event_id, error_message)
            _update_analysis_failed(
                conn,
                analysis_id,
                error_message,
                raw_output,
                request_payload=client.last_request,
            )
            return {
                "analysis_id": analysis_id,
                "status": "failed",
                "error_message": error_message,
                "provider": provider,
                "model": model,
            }
        except Exception as exc:  # noqa: BLE001
            logger.error("llm_analysis_failed news_event_id=%s error=%s", news_event_id, exc)
            _update_analysis_failed(
                conn,
                analysis_id,
                f"unexpected_error: {exc}",
                raw_output=_build_raw_output(None),
                request_payload=client.last_request,
            )
            return {
                "analysis_id": analysis_id,
                "status": "failed",
                "error_message": str(exc),
                "provider": provider,
                "model": model,
            }
