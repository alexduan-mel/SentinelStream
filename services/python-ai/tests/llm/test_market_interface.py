from llm.interface import LLMClient, LLMProviderResponse, MarketAnalysisResult


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
        '"affected_assets":[{"symbol":"MU","confidence":0.9}],"market_relevance_score":0.7}'
    )
    client = LLMClient(FakeProvider([output]), timeout_seconds=5, max_retries=0)
    result = client.analyze_market_news("Title: Example")
    assert isinstance(result, MarketAnalysisResult)
    assert result.sector == "information_technology"
    assert result.subtopic == "semiconductors"
    assert result.subtopic_label == "Memory pricing"
    assert result.market_relevance_score == 0.7


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
