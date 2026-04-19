from datetime import datetime

from ingestion.time_windows import resolve_company_news_dates


def test_resolve_company_news_dates_includes_nyc_previous_day():
    window_start_nyc = datetime(2026, 4, 19, 3, 30)
    window_end_nyc = datetime(2026, 4, 19, 4, 30)

    date_from, date_to = resolve_company_news_dates(window_start_nyc, window_end_nyc)

    assert date_from == "2026-04-18"
    assert date_to == "2026-04-19"


def test_resolve_company_news_dates_preserves_wider_lookback():
    window_start_nyc = datetime(2026, 4, 15, 9, 0)
    window_end_nyc = datetime(2026, 4, 19, 9, 0)

    date_from, date_to = resolve_company_news_dates(window_start_nyc, window_end_nyc)

    assert date_from == "2026-04-15"
    assert date_to == "2026-04-19"
