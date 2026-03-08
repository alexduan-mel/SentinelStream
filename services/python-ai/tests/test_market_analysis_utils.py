from analysis.market_news import (
    map_affected_assets_to_entities,
    map_direction_to_sentiment,
    normalize_market_result,
    normalize_topic_key,
)
from llm.interface import MarketAnalysisResult


def test_topic_key_normalization_and_aliases():
    assert normalize_topic_key("Memory pricing") == "memory_pricing"
    assert normalize_topic_key("AI-capex") == "ai_infrastructure_spending"
    assert normalize_topic_key("datacenter spending") == "ai_infrastructure_spending"
    assert normalize_topic_key("Fed policy shift") == "fed_policy_shift"
    assert normalize_topic_key("Gold rally!") == "gold_rally"


def test_direction_mapping():
    assert map_direction_to_sentiment("bullish") == "positive"
    assert map_direction_to_sentiment("bearish") == "negative"
    assert map_direction_to_sentiment("mixed") == "neutral"
    assert map_direction_to_sentiment(None) == "neutral"


def test_affected_assets_mapping():
    assets = [
        {"symbol": "mu", "confidence": 0.9},
        "AAPL",
        {"ticker": "msft", "confidence": 0.7},
        {"symbol": "AAPL", "confidence": 0.6},
        {"symbol": "", "confidence": 0.2},
    ]
    entities = map_affected_assets_to_entities(assets)
    entities_sorted = sorted(entities, key=lambda item: item["symbol"])
    assert entities_sorted == [
        {"symbol": "AAPL", "confidence": 0.6},
        {"symbol": "MSFT", "confidence": 0.7},
        {"symbol": "MU", "confidence": 0.9},
    ]


def test_normalize_market_result_output():
    result = MarketAnalysisResult(
        main_topic="Memory pricing",
        topic_key="dram_pricing",
        topic_type="sector",
        direction="neutral",
        summary="Prices stabilized.",
        affected_assets=["MU"],
        market_relevance_score=0.4,
    )
    normalized = normalize_market_result(result)
    assert normalized["topic_key"] == "memory_pricing"
    assert normalized["sentiment"] == "neutral"
    assert normalized["entities"] == [{"symbol": "MU", "confidence": 0.5}]
