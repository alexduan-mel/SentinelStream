from __future__ import annotations

import argparse
import logging
import os
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from zoneinfo import ZoneInfo

import httpx
import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import Json

from ingestion.finnhub_client import FinnhubError, fetch_company_news
from ingestion.news_store import upsert_news_event
from ingestion.normalizer import NormalizationError, normalize_finnhub
from ingestion.raw_store import insert_raw_items, mark_raw_failed, mark_raw_normalized, select_raw_items
from jobs.publisher import publish_job

JOB_NAME = "finnhub_ingestion"
LOCK_KEY = "finnhub_ingestion"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Finnhub news ingestion worker")
    parser.add_argument(
        "--tickers",
        nargs="*",
        default=None,
        help="Ticker symbols to fetch (defaults to all tickers in the DB)",
    )
    parser.add_argument(
        "--minutes-back",
        type=int,
        default=60,
        help="Minutes back from now to include in the ingestion window",
    )
    parser.add_argument(
        "--process-limit",
        type=int,
        default=200,
        help="Max raw items to process per run",
    )
    parser.add_argument(
        "--replay-only",
        action="store_true",
        help="Skip fetching and only process existing raw_news_items",
    )
    return parser.parse_args()


def _configure_logging() -> None:
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s %(levelname)s %(message)s",
    )


def _get_env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or not value.strip():
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise SystemExit(f"{name} must be an integer") from exc


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


def _try_advisory_lock(conn) -> bool:
    sql = "SELECT pg_try_advisory_lock(hashtext(%s))"
    with conn.cursor() as cursor:
        cursor.execute(sql, (LOCK_KEY,))
        locked = cursor.fetchone()[0]
    conn.commit()
    return bool(locked)


def _insert_ingestion_run(
    conn,
    job_name: str,
    trace_id: str,
    tickers: list[str],
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
        cursor.execute(sql, (job_name, trace_id, Json(tickers), window_from, window_to))
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


def _fetch_ticker_symbols(conn, symbols: list[str] | None) -> list[str]:
    if symbols:
        sql = "SELECT UPPER(TRIM(symbol)) FROM tickers WHERE UPPER(TRIM(symbol)) = ANY(%s)"
        params = (symbols,)
    else:
        sql = "SELECT UPPER(TRIM(symbol)) FROM tickers"
        params = None
    with conn.cursor() as cursor:
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
        rows = cursor.fetchall()
    return list(dict.fromkeys([row[0] for row in rows if row[0]]))


def _parse_finnhub_timestamp(value) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(int(value), tz=timezone.utc)
    if isinstance(value, str):
        if value.isdigit():
            return datetime.fromtimestamp(int(value), tz=timezone.utc)
        iso = value.strip()
        if iso.endswith("Z"):
            iso = iso[:-1] + "+00:00"
        try:
            parsed = datetime.fromisoformat(iso)
        except ValueError:
            return None
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    return None


def _rank_items(items: list[dict]) -> list[tuple[datetime | None, dict]]:
    ranked: list[tuple[datetime | None, dict]] = []
    for item in items:
        ts = item.get("datetime") or item.get("published_at")
        ranked.append((_parse_finnhub_timestamp(ts), item))
    ranked.sort(
        key=lambda pair: pair[0] or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )
    return ranked


def _limit_items_per_day(
    ranked: list[tuple[datetime | None, dict]],
    limit: int,
    local_tz: ZoneInfo,
) -> tuple[list[dict], int]:
    if limit <= 0:
        return [item for _, item in ranked], 0
    counts: dict[str, int] = {}
    kept: list[dict] = []
    for published_at, item in ranked:
        if published_at:
            date_key = published_at.astimezone(local_tz).date().isoformat()
        else:
            date_key = "unknown"
        if counts.get(date_key, 0) >= limit:
            continue
        counts[date_key] = counts.get(date_key, 0) + 1
        kept.append(item)
    dropped = len(ranked) - len(kept)
    return kept, dropped


def main() -> int:
    _configure_logging()
    args = _parse_args()
    logger = logging.getLogger(__name__)

    load_dotenv()

    trace_id = uuid4()

    token = os.getenv("FINNHUB_TOKEN")
    if not token and not args.replay_only:
        raise SystemExit("FINNHUB_TOKEN is required unless --replay-only is set")

    if args.tickers and args.replay_only:
        logger.info("tickers_ignored_replay_only trace_id=%s", trace_id)

    latest_per_run = _get_env_int("INTAKE_LATEST_PER_RUN_PER_TICKER", 10)
    daily_max = _get_env_int("INTAKE_DAILY_MAX_PER_TICKER", 100)

    now_utc = datetime.now(timezone.utc)
    nyc_tz = ZoneInfo("America/New_York")
    now_nyc = now_utc.astimezone(nyc_tz)
    window_start_nyc = now_nyc - timedelta(minutes=args.minutes_back)
    window_end_nyc = now_nyc
    window_start = window_start_nyc.astimezone(timezone.utc)
    window_end = window_end_nyc.astimezone(timezone.utc)
    logger.info(
        "finnhub_window trace_id=%s start=%s end=%s",
        trace_id,
        window_start.isoformat(),
        window_end.isoformat(),
    )
    logger.info(
        "finnhub_window_nyc trace_id=%s start=%s end=%s",
        trace_id,
        window_start_nyc.isoformat(),
        window_end_nyc.isoformat(),
    )
    # Finnhub company-news accepts YYYY-MM-DD only, so we fetch by date range.
    # Dates are based on NYC local time, not the server timezone.
    date_from = window_start_nyc.date().isoformat()
    date_to = window_end_nyc.date().isoformat()

    requested = None
    if args.tickers:
        requested = [ticker.strip().upper() for ticker in args.tickers if ticker.strip()]

    fetched_count = 0
    raw_inserted_count = 0
    raw_updated_count = 0

    to_process_count = 0
    normalized_ok_count = 0
    normalized_failed_count = 0
    news_inserted_count = 0
    news_upsert_count = 0
    jobs_enqueued_count = 0
    jobs_skipped_count = 0

    conn = _connect_db()
    run_id: int | None = None
    try:
        if not _try_advisory_lock(conn):
            logger.info("ingestion_lock_not_acquired trace_id=%s", trace_id)
            return 0

        if not args.replay_only:
            tickers = _fetch_ticker_symbols(conn, requested)
            if requested:
                missing = sorted(set(requested) - set(tickers))
                for symbol in missing:
                    logger.warning("ticker_not_in_db trace_id=%s symbol=%s", trace_id, symbol)
        else:
            tickers = requested or []

        run_id = _insert_ingestion_run(conn, JOB_NAME, str(trace_id), tickers, window_start, window_end)

        if not tickers and not args.replay_only:
            logger.info("no_tickers_found trace_id=%s", trace_id)
            meta = {
                "raw_inserted_count": raw_inserted_count,
                "raw_updated_count": raw_updated_count,
                "normalized_ok_count": normalized_ok_count,
                "normalized_failed_count": normalized_failed_count,
                "jobs_enqueued_count": jobs_enqueued_count,
                "jobs_skipped_count": jobs_skipped_count,
                "latest_per_run": latest_per_run,
                "daily_max": daily_max,
                "process_limit": args.process_limit,
                "minutes_back": args.minutes_back,
            }
            _finish_ingestion_run(
                conn,
                run_id,
                "succeeded",
                fetched_count,
                news_inserted_count,
                0,
                None,
                meta,
            )
            return 0

        if not args.replay_only:
            timeout = httpx.Timeout(10.0, connect=5.0)
            with httpx.Client(timeout=timeout) as client:
                raw_items: list[dict] = []
                for symbol in tickers:
                    try:
                        items, _status = fetch_company_news(
                            client,
                            token,
                            symbol,
                            date_from,
                            date_to,
                            trace_id=trace_id,
                        )
                    except FinnhubError as exc:
                        logger.error(
                            "finnhub_fetch_failed trace_id=%s ticker=%s error=%s",
                            trace_id,
                            symbol,
                            exc,
                        )
                        continue
                    ranked = _rank_items(items)
                    daily_limited, dropped_daily = _limit_items_per_day(ranked, daily_max, nyc_tz)
                    if dropped_daily:
                        logger.info(
                            "finnhub_daily_limit_applied trace_id=%s ticker=%s limit=%s dropped=%s",
                            trace_id,
                            symbol,
                            daily_max,
                            dropped_daily,
                        )
                    latest_items = daily_limited
                    dropped_latest = 0
                    if latest_per_run > 0 and len(daily_limited) > latest_per_run:
                        latest_items = daily_limited[:latest_per_run]
                        dropped_latest = len(daily_limited) - len(latest_items)
                    if dropped_latest:
                        logger.info(
                            "finnhub_latest_limit_applied trace_id=%s ticker=%s limit=%s dropped=%s",
                            trace_id,
                            symbol,
                            latest_per_run,
                            dropped_latest,
                        )
                    for item in latest_items:
                        enriched = dict(item)
                        enriched["request_ticker"] = symbol
                        raw_items.append(enriched)

                fetched_count = len(raw_items)
                raw_inserted_count, raw_updated_count = insert_raw_items(
                    conn,
                    "finnhub",
                    trace_id,
                    now_utc,
                    raw_items,
                )

        raw_rows = select_raw_items(conn, "finnhub", args.process_limit)
        to_process_count = len(raw_rows)

        ingested_at = datetime.now(timezone.utc)
        for raw_row in raw_rows:
            try:
                event = normalize_finnhub(
                    raw_row.raw_payload,
                    trace_id,
                    ingested_at,
                    request_ticker=raw_row.request_ticker,
                )
                event_id, inserted = upsert_news_event(conn, event)
                news_upsert_count += 1
                if inserted:
                    news_inserted_count += 1
                job_inserted = publish_job(conn, event_id, trace_id)
                if job_inserted:
                    jobs_enqueued_count += 1
                else:
                    jobs_skipped_count += 1
                mark_raw_normalized(conn, raw_row.id)
                normalized_ok_count += 1
            except NormalizationError as exc:
                mark_raw_failed(conn, raw_row.id, str(exc))
                normalized_failed_count += 1
            except Exception as exc:  # noqa: BLE001
                mark_raw_failed(conn, raw_row.id, f"unexpected_error: {exc}")
                normalized_failed_count += 1

        deduped_count = max(0, news_upsert_count - news_inserted_count)
        meta = {
            "raw_inserted_count": raw_inserted_count,
            "raw_updated_count": raw_updated_count,
            "normalized_ok_count": normalized_ok_count,
            "normalized_failed_count": normalized_failed_count,
            "jobs_enqueued_count": jobs_enqueued_count,
            "jobs_skipped_count": jobs_skipped_count,
            "latest_per_run": latest_per_run,
            "daily_max": daily_max,
            "process_limit": args.process_limit,
            "minutes_back": args.minutes_back,
        }
        _finish_ingestion_run(
            conn,
            run_id,
            "succeeded",
            fetched_count,
            news_inserted_count,
            deduped_count,
            None,
            meta,
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("finnhub_run_failed trace_id=%s", trace_id)
        if run_id is not None:
            deduped_count = max(0, news_upsert_count - news_inserted_count)
            meta = {
                "raw_inserted_count": raw_inserted_count,
                "raw_updated_count": raw_updated_count,
                "normalized_ok_count": normalized_ok_count,
                "normalized_failed_count": normalized_failed_count,
                "jobs_enqueued_count": jobs_enqueued_count,
                "jobs_skipped_count": jobs_skipped_count,
                "latest_per_run": latest_per_run,
                "daily_max": daily_max,
                "process_limit": args.process_limit,
                "minutes_back": args.minutes_back,
            }
            _finish_ingestion_run(
                conn,
                run_id,
                "failed",
                fetched_count,
                news_inserted_count,
                deduped_count,
                str(exc),
                meta,
            )
        return 1
    finally:
        conn.close()

    logger.info(
        "finnhub_run_summary trace_id=%s fetched_count=%s raw_inserted_count=%s "
        "raw_updated_count=%s to_process_count=%s normalized_ok_count=%s "
        "normalized_failed_count=%s news_inserted_count=%s news_deduped_count=%s "
        "jobs_enqueued_count=%s jobs_skipped_count=%s",
        trace_id,
        fetched_count,
        raw_inserted_count,
        raw_updated_count,
        to_process_count,
        normalized_ok_count,
        normalized_failed_count,
        news_inserted_count,
        max(0, news_upsert_count - news_inserted_count),
        jobs_enqueued_count,
        jobs_skipped_count,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
