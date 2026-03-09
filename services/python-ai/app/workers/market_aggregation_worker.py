from __future__ import annotations

import argparse
import logging
import os
import time
from datetime import datetime, timezone
from uuid import uuid4

from dotenv import load_dotenv

from market_pulse.aggregation import aggregate_market_pulse, connect_db


JOB_NAME = "market_aggregation"


def _configure_logging() -> None:
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s %(levelname)s %(message)s",
    )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Market pulse aggregation worker")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    return parser.parse_args()


def _get_env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or not value.strip():
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise SystemExit(f"{name} must be an integer") from exc


def main() -> int:
    _configure_logging()
    load_dotenv()
    logger = logging.getLogger(__name__)
    args = _parse_args()

    poll_seconds = max(_get_env_int("MARKET_PULSE_POLL_SECONDS", 300), 1)
    logger.info("market_aggregation_worker_start poll_seconds=%s", poll_seconds)

    while True:
        trace_id = uuid4()
        try:
            with connect_db() as conn:
                result = aggregate_market_pulse(conn)
            logger.info(
                "market_aggregation_complete trace_id=%s analyses_scanned=%s skipped_low_relevance=%s "
                "matched_topics=%s matched_candidates=%s candidates_created=%s candidates_promoted=%s "
                "mentions_created=%s asset_links_updated=%s",
                trace_id,
                result.get("analyses_scanned"),
                result.get("analyses_skipped_low_relevance"),
                result.get("matched_existing_topics"),
                result.get("matched_candidates"),
                result.get("candidates_created"),
                result.get("candidates_promoted"),
                result.get("mentions_created"),
                result.get("asset_links_updated"),
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("market_aggregation_failed trace_id=%s error=%s", trace_id, exc)

        if args.once:
            break
        time.sleep(poll_seconds)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
