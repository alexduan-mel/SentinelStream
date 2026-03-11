from llm.interface import (
    LLMClient,
    LLMProviderResponse,
    MarketAnalysisResult,
    build_market_prompt,
)


class FakeProvider:
    name = "fake"
    model = "fake-model"

    def __init__(self, outputs):
        self._outputs = list(outputs)

    def generate(self, prompt: str, timeout_seconds: int) -> LLMProviderResponse:
        return LLMProviderResponse(output_text=self._outputs.pop(0), response=None)


def test_market_parse_valid_json():
    output = (
        '{"sector":"information_technology","subtopic":"semiconductors","subtopic_label":"Memory pricing","topic_type":"sector",'
        '"direction":"neutral","summary":"Chip prices stabilized.",'
        '"affected_assets":[{"symbol":"MU","asset_type":"equity","relation":"positive","confidence":0.9}],'
        '"market_relevance_score":0.7}'
    )
    client = LLMClient(FakeProvider([output]), timeout_seconds=5, max_retries=0)
    result = client.analyze_market_news("Title: Example")
    assert isinstance(result, MarketAnalysisResult)
    assert result.sector == "information_technology"
    assert result.subtopic == "semiconductors"
    assert result.subtopic_label == "Memory pricing"
    assert result.market_relevance_score == 0.7
    assets = result.affected_assets
    assert len(assets) <= 5
    asset = assets[0]
    assert asset["asset_type"] in {"equity", "etf", "commodity", "index", "fx", "other"}
    assert asset["relation"] in {"positive", "negative", "mixed"}
    assert 0 <= asset["confidence"] <= 1
    assert asset["symbol"] == "MU"


def test_market_retry_on_invalid_json_then_success():
    bad = "not-json"
    good = (
        '{"sector":"macro","subtopic":"central_banks","subtopic_label":"Fed policy shift","topic_type":"macro",'
        '"direction":"bullish","summary":"Policy easing talk.",'
        '"affected_assets":[],"market_relevance_score":0.6}'
    )
    client = LLMClient(FakeProvider([bad, good]), timeout_seconds=5, max_retries=1)
    result = client.analyze_market_news("Title: Example")
    assert result.direction == "bullish"
    assert len(client.last_attempts) == 2


def test_market_parse_accepts_other_subtopic():
    output = (
        '{"sector":"utilities","subtopic":"other","subtopic_label":"Regulatory update","topic_type":"sector",'
        '"direction":"neutral","summary":"Policy update impacts utilities.",'
        '"affected_assets":[],"market_relevance_score":0.55}'
    )
    client = LLMClient(FakeProvider([output]), timeout_seconds=5, max_retries=0)
    result = client.analyze_market_news("Title: Example")
    assert isinstance(result, MarketAnalysisResult)
    assert result.sector == "utilities"
    assert result.subtopic == "other"


def test_market_prompt_mentions_other_behavior():
    prompt = build_market_prompt("Title: Example")
    assert "use `other` only when no listed subtopic fits well" in prompt
    assert "prefer a specific listed subtopic over `other` when possible" in prompt
    assert "affected_assets must be an array of objects" in prompt
    assert "asset_type must be one of: equity, etf, commodity, index, fx, other" in prompt
    assert "relation must be one of: positive, negative, mixed" in prompt
    assert "include at most 5 assets" in prompt
