import pytest
from pydantic import ValidationError

from analysis.market_news import (
    map_affected_assets_to_entities,
    map_direction_to_sentiment,
    normalize_market_result,
)
from llm.interface import MarketAnalysisResult, _load_market_taxonomy_sets


def test_sector_validation():
    with pytest.raises(ValidationError):
        MarketAnalysisResult(
            sector="unknown",
            subtopic="geopolitics",
            subtopic_label="Random",
            topic_type="misc",
            direction="neutral",
            summary="Regional tensions.",
            affected_assets=[],
            market_relevance_score=0.6,
        )


def test_subtopic_validation_for_sector():
    with pytest.raises(ValidationError):
        MarketAnalysisResult(
            sector="energy",
            subtopic="ai",
            subtopic_label="AI demand",
            topic_type="sector",
            direction="neutral",
            summary="Energy markets mentioned AI demand.",
            affected_assets=[],
            market_relevance_score=0.6,
        )


def test_other_subtopic_supported_for_all_sectors():
    taxonomy = _load_market_taxonomy_sets()
    assert taxonomy
    for sector, subtopics in taxonomy.items():
        assert "other" in subtopics
        result = MarketAnalysisResult(
            sector=sector,
            subtopic="other",
            subtopic_label="Misc update",
            topic_type="sector",
            direction="neutral",
            summary="General market update.",
            affected_assets=[],
            market_relevance_score=0.5,
        )
        assert result.subtopic == "other"


def test_direction_mapping():
    assert map_direction_to_sentiment("bullish") == "positive"
    assert map_direction_to_sentiment("bearish") == "negative"
    assert map_direction_to_sentiment("mixed") == "neutral"
    assert map_direction_to_sentiment(None) == "neutral"


def test_affected_assets_mapping():
    assets = [
        {"symbol": "mu", "asset_type": "equity", "relation": "positive", "confidence": 0.9},
        {"symbol": "AAPL", "asset_type": "equity", "relation": "mixed", "confidence": 0.5},
        {"ticker": "msft", "asset_type": "equity", "relation": "positive", "confidence": 0.7},
        {"symbol": "AAPL", "asset_type": "equity", "relation": "negative", "confidence": 0.6},
        {"symbol": "", "asset_type": "equity", "relation": "mixed", "confidence": 0.2},
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
        sector="information_technology",
        subtopic="semiconductors",
        subtopic_label="Memory pricing",
        topic_type="sector",
        direction="neutral",
        summary="Prices stabilized.",
        affected_assets=[{"symbol": "MU", "asset_type": "equity", "relation": "positive", "confidence": 0.8}],
        market_relevance_score=0.4,
    )
    normalized = normalize_market_result(result)
    assert normalized["sector"] == "information_technology"
    assert normalized["subtopic"] == "semiconductors"
    assert normalized["subtopic_label"] == "Memory pricing"
    assert normalized["sentiment"] == "neutral"
    assert normalized["entities"] == [{"symbol": "MU", "confidence": 0.5}]
