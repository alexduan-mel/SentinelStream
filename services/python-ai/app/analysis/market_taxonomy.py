from __future__ import annotations

import re
from typing import Iterable



TAXONOMY_ITEMS: list[tuple[str, str]] = [
    ("middle_east_geopolitical_risk", "Middle East geopolitical risk"),
    ("china_us_geopolitical_tension", "China-US geopolitical tension"),
    ("global_trade_tensions", "Global trade tensions"),
    ("global_oil_market_disruption", "Global oil market disruption"),
    ("gold_safe_haven_demand", "Gold safe-haven demand"),
    ("fed_policy_shift", "Fed policy shift"),
    ("inflation_reacceleration", "Inflation reacceleration"),
    ("growth_slowdown_risk", "Growth slowdown risk"),
    ("geopolitical_market_volatility", "Geopolitical market volatility"),
    ("risk_off_rotation", "Risk-off rotation"),
    ("ai_infrastructure_spending", "AI infrastructure spending"),
    ("semiconductor_supply_demand", "Semiconductor supply/demand"),
    ("memory_pricing", "Memory pricing"),
    ("defense_industry_expansion", "Defense industry expansion"),
    ("airline_industry_disruption", "Airline industry disruption"),
    ("prediction_market_regulation", "Prediction market regulation"),
    ("ai_application_adoption", "AI application adoption"),
    ("other_market_theme", "Other market theme"),
]

TAXONOMY_LABELS = {key: label for key, label in TAXONOMY_ITEMS}
ALLOWED_TOPIC_KEYS = set(TAXONOMY_LABELS)


def normalize_topic_key(raw: str) -> str:
    if not isinstance(raw, str):
        raise ValueError("topic_key must be a string")
    normalized = raw.strip().lower()
    if not normalized:
        raise ValueError("topic_key must be non-empty")
    normalized = normalized.replace("-", " ")
    normalized = re.sub(r"[^\w\s]", "", normalized)
    normalized = re.sub(r"[\s_]+", "_", normalized)
    normalized = normalized.strip("_")
    normalized = re.sub(r"_+", "_", normalized)
    return normalized


def classify_topic_key(raw_key: str) -> str:
    normalized = normalize_topic_key(raw_key)
    if normalized in ALLOWED_TOPIC_KEYS:
        return normalized
    return "other_market_theme"


def topic_label(topic_key: str) -> str | None:
    return TAXONOMY_LABELS.get(topic_key)


def taxonomy_prompt_lines() -> str:
    return "\n".join(f"- {key}: {label}" for key, label in TAXONOMY_ITEMS)


def taxonomy_keys() -> Iterable[str]:
    return (key for key, _ in TAXONOMY_ITEMS)
