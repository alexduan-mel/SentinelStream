import pytest

from llm.interface import LLMClient, AnalysisResult, LLMProviderResponse


class FakeProvider:
    name = "fake"
    model = "fake-model"

    def __init__(self, outputs):
        self._outputs = list(outputs)

    def generate(self, prompt: str, timeout_seconds: int) -> LLMProviderResponse:
        return LLMProviderResponse(output_text=self._outputs.pop(0), response=None)


def test_parse_valid_json():
    output = '{"tickers":["AAPL"],"sentiment":"positive","confidence":0.9,"reasoning_summary":"Strong product demand."}'
    client = LLMClient(FakeProvider([output]), timeout_seconds=5, max_retries=0)
    result = client.analyze_news("Title: Example")
    assert isinstance(result, AnalysisResult)
    assert result.tickers == ["AAPL"]
    assert result.sentiment == "positive"


def test_retry_on_invalid_json_then_success():
    bad = "not-json"
    good = '{"tickers":[],"sentiment":"neutral","confidence":0.5,"reasoning_summary":"No clear impact."}'
    client = LLMClient(FakeProvider([bad, good]), timeout_seconds=5, max_retries=1)
    result = client.analyze_news("Title: Example")
    assert result.sentiment == "neutral"
    assert len(client.last_attempts) == 2


def test_retry_on_schema_error_then_success():
    bad = '{"tickers":["AAPL"],"sentiment":"positive","confidence":2,"reasoning_summary":"bad"}'
    good = '{"tickers":["AAPL"],"sentiment":"positive","confidence":0.7,"reasoning_summary":"ok"}'
    client = LLMClient(FakeProvider([bad, good]), timeout_seconds=5, max_retries=1)
    result = client.analyze_news("Title: Example")
    assert result.confidence == 0.7
    assert len(client.last_attempts) == 2
