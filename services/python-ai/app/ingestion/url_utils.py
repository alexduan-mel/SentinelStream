from __future__ import annotations

import hashlib
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


TRACKING_PARAMS = {
    "gclid",
    "fbclid",
    "mc_cid",
    "mc_eid",
    "ref",
    "ref_src",
    "cmpid",
}


def canonicalize_url(url: str) -> str:
    if url is None:
        raise ValueError("url is required")
    raw = url.strip()
    if not raw:
        raise ValueError("url is required")

    parts = urlsplit(raw)
    scheme = parts.scheme.lower()
    hostname = parts.hostname.lower() if parts.hostname else ""

    netloc = hostname
    if parts.username:
        userinfo = parts.username
        if parts.password:
            userinfo = f"{userinfo}:{parts.password}"
        netloc = f"{userinfo}@{netloc}"
    if parts.port:
        netloc = f"{netloc}:{parts.port}"

    path = parts.path
    if path == "":
        path = "/"
    else:
        path = path.rstrip("/")
        if path == "":
            path = "/"

    filtered = []
    for key, value in parse_qsl(parts.query, keep_blank_values=True):
        key_lower = key.lower()
        if key_lower.startswith("utm_") or key_lower in TRACKING_PARAMS:
            continue
        filtered.append((key, value))
    filtered.sort(key=lambda pair: (pair[0], pair[1]))
    query = urlencode(filtered, doseq=True)

    return urlunsplit((scheme, netloc, path, query, ""))


def generate_news_id(source: str, url: str) -> str:
    canonical_url = canonicalize_url(url)
    raw = f"{source}|{canonical_url}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
