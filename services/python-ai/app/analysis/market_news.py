from __future__ import annotations

import re
from typing import Any

from llm.interface import MarketAnalysisResult

ALIAS_MAP = {
    "dram_pricing": "memory_pricing",
    "memory_chip_pricing": "memory_pricing",
    "ai_capex": "ai_infrastructure_spending",
    "datacenter_spending": "ai_infrastructure_spending",
}


def normalize_topic_key(main_topic: str) -> str:
    if not isinstance(main_topic, str):
        raise ValueError("main_topic must be a string")
    raw = main_topic.strip().lower()
    if not raw:
        raise ValueError("main_topic must be non-empty")
    raw = raw.replace("-", " ")
    raw = re.sub(r"[^\w\s]", "", raw)
    raw = re.sub(r"[\s_]+", "_", raw)
    raw = raw.strip("_")
    raw = re.sub(r"_+", "_", raw)
    return ALIAS_MAP.get(raw, raw)


def map_direction_to_sentiment(direction: str | None) -> str:
    if not direction:
        return "neutral"
    lowered = direction.strip().lower()
    if lowered == "bullish":
        return "positive"
    if lowered == "bearish":
        return "negative"
    if lowered in {"neutral", "mixed"}:
        return "neutral"
    return "neutral"


def map_affected_assets_to_entities(affected_assets: Any) -> list[dict[str, Any]]:
    if not isinstance(affected_assets, list):
        return []
    by_symbol: dict[str, float] = {}
    for item in affected_assets:
        symbol = None
        confidence = 0.5
        if isinstance(item, str):
            symbol = item.strip().upper()
        elif isinstance(item, dict):
            raw_symbol = item.get("symbol") or item.get("ticker")
            if isinstance(raw_symbol, str):
                symbol = raw_symbol.strip().upper()
            raw_conf = item.get("confidence")
            if isinstance(raw_conf, (int, float)):
                if 0 <= float(raw_conf) <= 1:
                    confidence = float(raw_conf)
        if not symbol:
            continue
        prev = by_symbol.get(symbol)
        if prev is None or confidence > prev:
            by_symbol[symbol] = confidence
    return [{"symbol": symbol, "confidence": conf} for symbol, conf in by_symbol.items()]


def normalize_market_result(result: MarketAnalysisResult) -> dict[str, Any]:
    topic_key = normalize_topic_key(result.main_topic)
    sentiment = map_direction_to_sentiment(result.direction)
    entities = map_affected_assets_to_entities(result.affected_assets)
    return {
        "topic_key": topic_key,
        "sentiment": sentiment,
        "entities": entities,
    }
