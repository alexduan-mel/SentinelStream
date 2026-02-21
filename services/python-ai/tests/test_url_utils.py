import pytest

from ingestion.url_utils import canonicalize_url, generate_news_id


def test_fragment_removed():
    url = "https://example.com/path#section"
    assert canonicalize_url(url) == "https://example.com/path"


def test_utm_params_removed():
    url = "https://example.com/article?id=123&utm_source=a&utm_medium=b"
    assert canonicalize_url(url) == "https://example.com/article?id=123"


def test_gclid_fbclid_removed():
    url = "https://example.com/article?id=123&gclid=aaa&fbclid=bbb"
    assert canonicalize_url(url) == "https://example.com/article?id=123"


def test_query_params_sorted_stably():
    url = "https://example.com/path?b=2&a=1&a=0"
    assert canonicalize_url(url) == "https://example.com/path?a=0&a=1&b=2"


def test_trailing_slash_normalized():
    assert canonicalize_url("https://example.com/path/") == "https://example.com/path"
    assert canonicalize_url("https://example.com/") == "https://example.com/"


def test_generate_news_id_same_for_tracking_variants():
    u1 = "https://example.com/article?id=123&utm_source=a"
    u2 = "https://example.com/article?id=123&utm_campaign=b"
    assert generate_news_id("finnhub", u1) == generate_news_id("finnhub", u2)


def test_empty_url_raises():
    with pytest.raises(ValueError):
        canonicalize_url("")
