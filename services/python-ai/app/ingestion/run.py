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

from ingestion.finnhub_client import FinnhubError, fetch_company_news
from ingestion.news_store import insert_news_events
from ingestion.normalizer import NormalizationError, normalize_finnhub
from ingestion.raw_store import insert_raw_items, mark_raw_failed, mark_raw_normalized, select_raw_items
from jobs.publisher import publish_job


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
    return psycopg2.connect(
        host=host,
        port=port,
        dbname=name,
        user=user,
        password=password,
    )


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
    # Finnhub company-news accepts YYYY-MM-DD only, so we fetch a superset and filter by time window.
    # Dates are based on NYC local time, not the server timezone.
    date_from = window_start_nyc.date().isoformat()
    date_to = window_end_nyc.date().isoformat()

    requested = None
    if args.tickers:
        requested = [ticker.strip().upper() for ticker in args.tickers if ticker.strip()]

    fetched_count = 0
    raw_inserted_count = 0
    raw_updated_count = 0

    with _connect_db() as conn:
        if not args.replay_only:
            tickers = _fetch_ticker_symbols(conn, requested)
            if requested:
                missing = sorted(set(requested) - set(tickers))
                for symbol in missing:
                    logger.warning("ticker_not_in_db trace_id=%s symbol=%s", trace_id, symbol)
            if not tickers:
                logger.info("no_tickers_found trace_id=%s", trace_id)
                return 0

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
                    raw_items.extend(items)

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
    normalized_ok_count = 0
    normalized_failed_count = 0
    news_inserted_count = 0
    jobs_enqueued_count = 0
    jobs_skipped_count = 0

    ingested_at = datetime.now(timezone.utc)
    with _connect_db() as conn:
        for raw_row in raw_rows:
            try:
                event = normalize_finnhub(raw_row.raw_payload, trace_id, ingested_at)
                inserted = insert_news_events(conn, [event])
                news_inserted_count += inserted
                job_inserted = publish_job(conn, event.news_id, trace_id)
                if job_inserted:
                    jobs_enqueued_count += 1
                else:
                    jobs_skipped_count += 1
                mark_raw_normalized(conn, raw_row.raw_id)
                normalized_ok_count += 1
            except NormalizationError as exc:
                mark_raw_failed(conn, raw_row.raw_id, str(exc))
                normalized_failed_count += 1
            except Exception as exc:  # noqa: BLE001
                mark_raw_failed(conn, raw_row.raw_id, f"unexpected_error: {exc}")
                normalized_failed_count += 1

    logger.info(
        "finnhub_run_summary trace_id=%s fetched_count=%s raw_inserted_count=%s "
        "raw_updated_count=%s to_process_count=%s normalized_ok_count=%s "
        "normalized_failed_count=%s news_inserted_count=%s jobs_enqueued_count=%s "
        "jobs_skipped_count=%s",
        trace_id,
        fetched_count,
        raw_inserted_count,
        raw_updated_count,
        to_process_count,
        normalized_ok_count,
        normalized_failed_count,
        news_inserted_count,
        jobs_enqueued_count,
        jobs_skipped_count,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
