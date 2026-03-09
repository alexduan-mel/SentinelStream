import os
from pathlib import Path

from services.topic_normalizer import load_topic_aliases, normalize_topic


def _write_alias_file(path: Path) -> None:
    content = """
topics:
  ai_infrastructure_spending:
    aliases:
      - ai_capex
  memory_pricing: {}
blocked_topics:
  - us_meme_war
"""
    path.write_text(content, encoding="utf-8")


def test_blocked_topic_returns_none(tmp_path):
    alias_path = tmp_path / "topic_aliases.yaml"
    _write_alias_file(alias_path)
    os.environ["TOPIC_ALIASES_PATH"] = str(alias_path)
    load_topic_aliases.cache_clear()

    assert normalize_topic("US_MEME_WAR") is None


def test_passthrough_when_not_aliased(tmp_path):
    alias_path = tmp_path / "topic_aliases.yaml"
    _write_alias_file(alias_path)
    os.environ["TOPIC_ALIASES_PATH"] = str(alias_path)
    load_topic_aliases.cache_clear()

    assert normalize_topic("fed_policy_shift") == "fed_policy_shift"
