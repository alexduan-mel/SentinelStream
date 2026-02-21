from __future__ import annotations

import logging
import time
from typing import Any
from uuid import UUID

import httpx

BASE_URL = "https://finnhub.io/api/v1"
LOGGER = logging.getLogger(__name__)


class FinnhubError(RuntimeError):
    pass


def _request_with_retries(
    client: httpx.Client,
    url: str,
    params: dict[str, Any],
    *,
    max_attempts: int = 3,
    trace_id: UUID | None = None,
    ticker: str | None = None,
) -> httpx.Response:
    last_exception: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            response = client.get(url, params=params)
            LOGGER.info(
                "finnhub_http_response trace_id=%s ticker=%s status=%s attempt=%s",
                trace_id,
                ticker,
                response.status_code,
                attempt,
            )
        except httpx.RequestError as exc:
            last_exception = exc
            if attempt == max_attempts:
                break
            time.sleep(2 ** (attempt - 1))
            continue

        if response.status_code < 400:
            return response

        if response.status_code == 429 or 500 <= response.status_code <= 599:
            if attempt == max_attempts:
                break
            retry_after = response.headers.get("Retry-After")
            if retry_after and retry_after.isdigit():
                sleep_seconds = max(int(retry_after), 1)
            else:
                sleep_seconds = 2 ** (attempt - 1)
            time.sleep(sleep_seconds)
            continue

        response.raise_for_status()

    if last_exception is not None:
        raise FinnhubError("Finnhub request failed") from last_exception

    raise FinnhubError(
        f"Finnhub request failed with status {response.status_code}: {response.text}"
    )


def fetch_company_news(
    client: httpx.Client,
    token: str,
    symbol: str,
    date_from: str,
    date_to: str,
    *,
    trace_id: UUID | None = None,
) -> tuple[list[dict[str, Any]], int]:
    # We use /company-news because it scopes to specific U.S. equity tickers and supports
    # date-range filtering, matching our CLI and keeping payloads small.
    # Finnhub's Python client uses `_from` for the "from" query param; the REST API expects "from".
    url = f"{BASE_URL}/company-news"
    params = {
        "symbol": symbol,
        "from": date_from,
        "to": date_to,
        "token": token,
    }
    response = _request_with_retries(client, url, params, trace_id=trace_id, ticker=symbol)
    status_code = response.status_code
    payload = response.json()
    if not isinstance(payload, list):
        raise FinnhubError(f"Unexpected Finnhub payload: {payload}")
    LOGGER.info(
        "finnhub_items trace_id=%s ticker=%s status=%s items=%s",
        trace_id,
        symbol,
        status_code,
        len(payload),
    )
    return payload, status_code
