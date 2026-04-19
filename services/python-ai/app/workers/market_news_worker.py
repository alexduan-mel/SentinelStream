from __future__ import annotations

import argparse
import logging
import os
import time
from datetime import datetime, timezone
from uuid import uuid4

import httpx
import psycopg2
from psycopg2.extras import Json
from dotenv import load_dotenv

from ingestion.finnhub_client import FinnhubError, fetch_market_news
from ingestion.market_news_ingestion import (
    MarketNewsNormalizationError,
    MarketNewsParseError,
    normalize_market_news_item,
    parse_market_news_payload,
)
from ingestion.news_event_store import upsert_news_event
from jobs.publisher import publish_job

JOB_NAME = "finnhub_market_news"


def _configure_logging() -> None:
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s %(levelname)s %(message)s",
    )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Market news ingestion worker")
    parser.add_argument("--once", action="store_true", help="Run one poll and exit")
    return parser.parse_args()


def _get_env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or not value.strip():
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise SystemExit(f"{name} must be an integer") from exc


def _parse_categories(raw: str | None) -> list[str]:
    if raw is None:
        raw = ""
    parts = [item.strip().lower() for item in raw.split(",") if item.strip()]
    base = ["general"]
    if not parts:
        return base
    merged = list(dict.fromkeys(parts + base))
    return merged


def _safe_int(value: str | None) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _connect_db():
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
        raise SystemExit(f"Missing DB environment variables: {', '.join(missing)}")
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


def _insert_ingestion_run(
    conn,
    job_name: str,
    trace_id: str,
    categories: list[str],
    window_from: datetime | None,
    window_to: datetime | None,
) -> int:
    sql = (
        "INSERT INTO ingestion_runs "
        "(job_name, trace_id, status, tickers, window_from, window_to) "
        "VALUES (%s, %s, 'running', %s, %s, %s) "
        "RETURNING id"
    )
    with conn.cursor() as cursor:
        cursor.execute(sql, (job_name, trace_id, Json(categories), window_from, window_to))
        run_id = cursor.fetchone()[0]
    conn.commit()
    return run_id


def _finish_ingestion_run(
    conn,
    run_id: int,
    status: str,
    fetched_count: int,
    inserted_count: int,
    deduped_count: int,
    error_message: str | None,
    meta: dict,
) -> None:
    sql = (
        "UPDATE ingestion_runs "
        "SET finished_at = %s, status = %s, fetched_count = %s, "
        "inserted_count = %s, deduped_count = %s, error_message = %s, meta = %s "
        "WHERE id = %s"
    )
    with conn.cursor() as cursor:
        cursor.execute(
            sql,
            (
                datetime.now(timezone.utc),
                status,
                fetched_count,
                inserted_count,
                deduped_count,
                error_message,
                Json(meta),
                run_id,
            ),
        )
    conn.commit()


def _get_max_market_news_id(conn, category: str) -> int | None:
    sql = (
        "SELECT MAX(source_event_id::bigint) "
        "FROM news_events "
        "WHERE provider = %s AND event_type = %s "
        "AND source_event_id ~ '^[0-9]+$' "
        "AND raw_payload #>> '{_meta,category}' = %s"
    )
    with conn.cursor() as cursor:
        cursor.execute(sql, ("finnhub", "market_news", category))
        row = cursor.fetchone()
    return row[0] if row and row[0] is not None else None


def _resolve_api_key(logger: logging.Logger) -> str:
    api_key = os.getenv("FINNHUB_API_KEY")
    if api_key:
        return api_key
    legacy = os.getenv("FINNHUB_TOKEN")
    if legacy:
        logger.warning("finnhub_api_key_missing_using_legacy_token")
        return legacy
    raise SystemExit("FINNHUB_API_KEY is required")


def main() -> int:
    _configure_logging()
    load_dotenv()
    logger = logging.getLogger(__name__)
    args = _parse_args()

    api_key = _resolve_api_key(logger)
    categories = _parse_categories(os.getenv("MARKET_NEWS_CATEGORY", "general"))
    poll_seconds = max(_get_env_int("MARKET_NEWS_POLL_SECONDS", 300), 1)

    logger.info(
        "market_news_worker_start categories=%s poll_seconds=%s",
        categories,
        poll_seconds,
    )

    conn = None
    with httpx.Client(timeout=10.0) as client:
        while True:
            trace_id = uuid4()
            fetched_count = 0
            inserted_count = 0
            deduped_count = 0
            skipped_count = 0
            error_count = 0
            jobs_enqueued_count = 0
            jobs_skipped_count = 0
            now = datetime.now(timezone.utc)

            run_id: int | None = None
            run_finished = False
            try:
                if conn is None or conn.closed != 0:
                    conn = _connect_db()

                run_id = _insert_ingestion_run(
                    conn,
                    JOB_NAME,
                    str(trace_id),
                    categories,
                    None,
                    None,
                )

                max_ids: dict[str, int | None] = {}
                for category in categories:
                    max_source_event_id = _get_max_market_news_id(conn, category)
                    max_ids[category] = max_source_event_id
                    payload, _status = fetch_market_news(
                        client,
                        api_key,
                        category,
                        trace_id=trace_id,
                    )
                    items = parse_market_news_payload(payload)
                    fetched_count += len(items)

                    for item in items:
                        try:
                            event = normalize_market_news_item(item, trace_id, now, category)
                            source_event_id = _safe_int(event.source_event_id)
                            if source_event_id is None:
                                skipped_count += 1
                                continue
                            if max_source_event_id is not None and source_event_id <= max_source_event_id:
                                skipped_count += 1
                                continue
                            event_id, inserted = upsert_news_event(conn, event)
                            if inserted:
                                inserted_count += 1
                            else:
                                deduped_count += 1
                            job_inserted = publish_job(conn, event_id, trace_id, job_type="llm_analysis_market")
                            if job_inserted:
                                jobs_enqueued_count += 1
                            else:
                                jobs_skipped_count += 1
                        except MarketNewsNormalizationError:
                            skipped_count += 1
                        except psycopg2.Error:
                            error_count += 1
                            if conn is not None:
                                conn.rollback()
                            logger.exception("market_news_db_item_failed trace_id=%s", trace_id)
                        except Exception:
                            error_count += 1
                            if conn is not None:
                                conn.rollback()
                            logger.exception("market_news_item_failed trace_id=%s", trace_id)
                meta = {
                    "categories": categories,
                    "max_source_event_ids": max_ids,
                    "poll_seconds": poll_seconds,
                    "jobs_enqueued_count": jobs_enqueued_count,
                    "jobs_skipped_count": jobs_skipped_count,
                }
                if run_id is not None:
                    _finish_ingestion_run(
                        conn,
                        run_id,
                        "succeeded",
                        fetched_count,
                        inserted_count,
                        deduped_count,
                        None,
                        meta,
                    )
                    run_finished = True
            except MarketNewsParseError:
                error_count += 1
                logger.exception("market_news_parse_failed trace_id=%s", trace_id)
                if run_id is not None and conn is not None and conn.closed == 0 and not run_finished:
                    _finish_ingestion_run(
                        conn,
                        run_id,
                        "failed",
                        fetched_count,
                        inserted_count,
                        deduped_count,
                        "market_news_parse_failed",
                        {
                            "categories": categories,
                            "poll_seconds": poll_seconds,
                            "jobs_enqueued_count": jobs_enqueued_count,
                            "jobs_skipped_count": jobs_skipped_count,
                        },
                    )
                    run_finished = True
            except FinnhubError:
                error_count += 1
                logger.exception("market_news_fetch_failed trace_id=%s", trace_id)
                if run_id is not None and conn is not None and conn.closed == 0 and not run_finished:
                    _finish_ingestion_run(
                        conn,
                        run_id,
                        "failed",
                        fetched_count,
                        inserted_count,
                        deduped_count,
                        "market_news_fetch_failed",
                        {
                            "categories": categories,
                            "poll_seconds": poll_seconds,
                            "jobs_enqueued_count": jobs_enqueued_count,
                            "jobs_skipped_count": jobs_skipped_count,
                        },
                    )
                    run_finished = True
            except psycopg2.Error:
                error_count += 1
                logger.exception("market_news_db_failed trace_id=%s", trace_id)
                if run_id is not None and conn is not None and conn.closed == 0 and not run_finished:
                    _finish_ingestion_run(
                        conn,
                        run_id,
                        "failed",
                        fetched_count,
                        inserted_count,
                        deduped_count,
                        "market_news_db_failed",
                        {
                            "categories": categories,
                            "poll_seconds": poll_seconds,
                            "jobs_enqueued_count": jobs_enqueued_count,
                            "jobs_skipped_count": jobs_skipped_count,
                        },
                    )
                    run_finished = True
                if conn is not None:
                    conn.close()
                    conn = None
            except Exception:
                error_count += 1
                logger.exception("market_news_loop_failed trace_id=%s", trace_id)
                if run_id is not None and conn is not None and conn.closed == 0 and not run_finished:
                    _finish_ingestion_run(
                        conn,
                        run_id,
                        "failed",
                        fetched_count,
                        inserted_count,
                        deduped_count,
                        "market_news_loop_failed",
                        {
                            "categories": categories,
                            "poll_seconds": poll_seconds,
                            "jobs_enqueued_count": jobs_enqueued_count,
                            "jobs_skipped_count": jobs_skipped_count,
                        },
                    )
                    run_finished = True

            logger.info(
                "market_news_poll_complete trace_id=%s categories=%s fetch_count=%s inserted_count=%s "
                "deduped_count=%s skipped_count=%s error_count=%s jobs_enqueued_count=%s jobs_skipped_count=%s",
                trace_id,
                categories,
                fetched_count,
                inserted_count,
                deduped_count,
                skipped_count,
                error_count,
                jobs_enqueued_count,
                jobs_skipped_count,
            )

            if args.once:
                break
            time.sleep(poll_seconds)


if __name__ == "__main__":
    raise SystemExit(main())
