from __future__ import annotations

import argparse
import logging
import os
import signal
import socket
import time
from dataclasses import dataclass
from datetime import timedelta
from typing import Iterable

import psycopg2

from analysis.service import analyze_news_event

@dataclass(frozen=True)
class JobRow:
    id: int
    job_uuid: str
    news_event_id: int
    job_type: str
    trace_id: str
    attempts: int


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analysis job worker")
    parser.add_argument("--poll-interval", type=int, default=10, help="Seconds between polls")
    parser.add_argument("--batch-size", type=int, default=1, help="Jobs to claim per loop")
    parser.add_argument("--once", action="store_true", help="Process once and exit")
    parser.add_argument("--worker-id", default=None, help="Worker identifier for locking")
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


def _claim_jobs(
    conn, batch_size: int, worker_id: str, max_attempts: int, run_after_column: str
) -> list[JobRow]:
    sql = (
        "WITH cte AS ("
        "  SELECT id, job_uuid, news_event_id, job_type, trace_id, attempts "
        "  FROM analysis_jobs "
        "  WHERE status = 'pending' "
        f"    AND {run_after_column} <= NOW() "
        "    AND attempts < %s "
        f"  ORDER BY {run_after_column} ASC, created_at ASC "
        "  FOR UPDATE SKIP LOCKED "
        "  LIMIT %s"
        ") "
        "UPDATE analysis_jobs j "
        "SET status = 'running', locked_at = NOW(), locked_by = %s, updated_at = NOW() "
        "FROM cte "
        "WHERE j.id = cte.id "
        "RETURNING j.id, j.job_uuid::text, j.news_event_id, j.job_type, j.trace_id::text, "
        "cte.attempts"
    )
    with conn.cursor() as cursor:
        cursor.execute(sql, (max_attempts, batch_size, worker_id))
        rows = cursor.fetchall()
    conn.commit()
    return [JobRow(*row) for row in rows]


def _load_news_event(conn, news_event_id: int) -> tuple[int, str, str]:
    sql = "SELECT id, news_id, title FROM news_events WHERE id = %s"
    with conn.cursor() as cursor:
        cursor.execute(sql, (news_event_id,))
        row = cursor.fetchone()
    if not row:
        raise RuntimeError(f"news_event_not_found: {news_event_id}")
    return row[0], row[1], row[2]


def _mark_done(conn, job_id: int) -> None:
    sql = (
        "UPDATE analysis_jobs "
        "SET status = 'done', updated_at = NOW(), last_error = NULL "
        "WHERE id = %s"
    )
    with conn.cursor() as cursor:
        cursor.execute(sql, (job_id,))
    conn.commit()


def _mark_failed(
    conn, job: JobRow, error: str, retryable: bool, max_attempts: int, run_after_column: str
) -> None:
    next_attempts = job.attempts + 1
    if retryable and next_attempts < max_attempts:
        backoff_seconds = 2 ** next_attempts
        sql = (
            "UPDATE analysis_jobs "
            "SET status = 'pending', attempts = attempts + 1, last_error = %s, "
            f"{run_after_column} = NOW() + (%s || ' seconds')::interval, updated_at = NOW(), "
            "locked_at = NULL, locked_by = NULL "
            "WHERE id = %s"
        )
        params = (error[:500], backoff_seconds, job.id)
    else:
        sql = (
            "UPDATE analysis_jobs "
            "SET status = 'failed', attempts = attempts + 1, last_error = %s, updated_at = NOW(), "
            "locked_at = NULL, locked_by = NULL "
            "WHERE id = %s"
        )
        params = (error[:500], job.id)
    with conn.cursor() as cursor:
        cursor.execute(sql, params)
    conn.commit()


def _recover_stuck_jobs(conn, visibility_timeout_seconds: int) -> int:
    sql = (
        "UPDATE analysis_jobs "
        "SET status = 'pending', locked_at = NULL, locked_by = NULL, updated_at = NOW() "
        "WHERE status = 'running' AND locked_at IS NOT NULL "
        "AND locked_at < NOW() - (%s || ' seconds')::interval"
    )
    with conn.cursor() as cursor:
        cursor.execute(sql, (visibility_timeout_seconds,))
        recovered = cursor.rowcount
    conn.commit()
    return recovered


def _is_retryable_error(error_message: str | None) -> bool:
    if not error_message:
        return False
    lowered = error_message.lower()
    if "insufficient_quota" in lowered or "401" in lowered or "403" in lowered:
        return False
    if "timeout" in lowered:
        return True
    if "json" in lowered:
        return True
    if "validation" in lowered:
        return True
    return False


def _process_jobs(
    conn,
    jobs: Iterable[JobRow],
    logger: logging.Logger,
    max_attempts: int,
    run_after_column: str,
) -> None:
    for job in jobs:
        start_time = time.monotonic()
        try:
            if job.job_type == "llm_analysis":
                result = analyze_news_event(job.news_event_id)
                duration_ms = int((time.monotonic() - start_time) * 1000)
                if result.get("status") == "succeeded":
                    _mark_done(conn, job.id)
                    logger.info(
                        "job_done job_id=%s news_event_id=%s attempts=%s provider=%s duration_ms=%s",
                        job.id,
                        job.news_event_id,
                        job.attempts + 1,
                        result.get("provider"),
                        duration_ms,
                    )
                else:
                    error_message = result.get("error_message", "analysis_failed")
                    retryable = _is_retryable_error(error_message)
                    _mark_failed(conn, job, error_message, retryable, max_attempts, run_after_column)
                    logger.error(
                        "job_failed job_id=%s news_event_id=%s attempts=%s retryable=%s provider=%s error=%s duration_ms=%s",
                        job.id,
                        job.news_event_id,
                        job.attempts + 1,
                        retryable,
                        result.get("provider"),
                        error_message,
                        duration_ms,
                    )
                continue

            event_id, news_id, _title = _load_news_event(conn, job.news_event_id)
            duration_ms = int((time.monotonic() - start_time) * 1000)
            logger.info(
                "job_done job_id=%s news_event_id=%s attempts=%s duration_ms=%s",
                job.id,
                event_id,
                job.attempts + 1,
                duration_ms,
            )
            _mark_done(conn, job.id)
        except Exception as exc:  # noqa: BLE001
            error_message = str(exc)
            retryable = _is_retryable_error(error_message)
            _mark_failed(conn, job, error_message, retryable, max_attempts, run_after_column)
            logger.error(
                "job_failed job_id=%s news_event_id=%s attempts=%s retryable=%s error=%s",
                job.id,
                job.news_event_id,
                job.attempts + 1,
                retryable,
                error_message,
            )


def _get_run_after_column(conn) -> str:
    sql = (
        "SELECT column_name "
        "FROM information_schema.columns "
        "WHERE table_name = 'analysis_jobs' AND column_name IN ('run_after','next_run_at')"
    )
    with conn.cursor() as cursor:
        cursor.execute(sql)
        columns = {row[0] for row in cursor.fetchall()}
    if "run_after" in columns:
        return "run_after"
    if "next_run_at" in columns:
        return "next_run_at"
    raise RuntimeError("analysis_jobs missing run_after/next_run_at column")


def main() -> int:
    _configure_logging()
    args = _parse_args()
    logger = logging.getLogger(__name__)

    running = {"value": True}

    def _handle_shutdown(signum, _frame):  # noqa: ANN001
        logger.info("worker_shutdown signal=%s", signum)
        running["value"] = False

    signal.signal(signal.SIGTERM, _handle_shutdown)
    signal.signal(signal.SIGINT, _handle_shutdown)

    worker_id = args.worker_id
    if not worker_id:
        worker_id = f"{socket.gethostname()}:{os.getpid()}"

    poll_seconds = int(os.getenv("WORKER_POLL_SECONDS", str(args.poll_interval)))
    visibility_timeout = int(os.getenv("WORKER_VISIBILITY_TIMEOUT_SECONDS", "300"))
    max_attempts = int(os.getenv("WORKER_MAX_ATTEMPTS", "3"))

    with _connect_db() as conn:
        run_after_column = _get_run_after_column(conn)

        while running["value"]:
            recovered = _recover_stuck_jobs(conn, visibility_timeout)
            if recovered:
                logger.info("worker_recovered_jobs count=%s", recovered)

            jobs = _claim_jobs(conn, args.batch_size, worker_id, max_attempts, run_after_column)
            if not jobs:
                if args.once:
                    break
                time.sleep(max(poll_seconds, 1))
                continue

            _process_jobs(conn, jobs, logger, max_attempts, run_after_column)

            if args.once:
                break

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
