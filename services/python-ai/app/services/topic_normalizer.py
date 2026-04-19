from __future__ import annotations

import logging
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml


LOGGER = logging.getLogger(__name__)


def _candidate_paths() -> list[Path]:
    paths: list[Path] = []
    env_path = os.getenv("TOPIC_ALIASES_PATH")
    if env_path:
        paths.append(Path(env_path))
    paths.append(Path("/app/config/topic_aliases.yaml"))
    paths.append(Path.cwd() / "config" / "topic_aliases.yaml")
    return paths


def _load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle)
    return payload if isinstance(payload, dict) else {}


@lru_cache(maxsize=1)
def load_topic_aliases() -> dict[str, Any]:
    data: dict[str, Any] = {}
    for path in _candidate_paths():
        if path.is_file():
            data = _load_yaml(path)
            break

    blocked_raw = data.get("blocked_topics") if isinstance(data, dict) else None

    blocked: set[str] = set()
    if isinstance(blocked_raw, list):
        for item in blocked_raw:
            if not isinstance(item, str):
                continue
            normalized = item.strip().lower()
            if normalized:
                blocked.add(normalized)

    if not blocked:
        LOGGER.warning("topic_aliases_empty_or_missing")

    return {
        "blocked_topics": blocked,
    }


def normalize_topic(topic_key: str) -> str | None:
    if not isinstance(topic_key, str):
        return None
    normalized = topic_key.strip().lower()
    if not normalized:
        return None
    config = load_topic_aliases()
    blocked = config.get("blocked_topics", set())
    if normalized in blocked:
        return None
    return normalized
