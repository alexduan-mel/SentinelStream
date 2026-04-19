from __future__ import annotations

from datetime import datetime, timedelta


def resolve_company_news_dates(window_start_nyc: datetime, window_end_nyc: datetime) -> tuple[str, str]:
    """
    Resolve Finnhub date window for /company-news.

    Finnhub accepts date-only params, and the effective day boundary is U.S. market time.
    To avoid missing overnight news when the host timezone is ahead of U.S. time,
    always include at least NYC T-1 ~ T. Wider requested windows remain honored.
    """
    end_date = window_end_nyc.date()
    min_start_date = end_date - timedelta(days=1)
    start_date = min(window_start_nyc.date(), min_start_date)
    return start_date.isoformat(), end_date.isoformat()
