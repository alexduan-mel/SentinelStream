from __future__ import annotations

from openai import OpenAI

from llm.interface import LLMProviderResponse


def _response_to_dict(response) -> dict | None:
    for attr in ("model_dump", "to_dict", "dict"):
        method = getattr(response, attr, None)
        if callable(method):
            try:
                return method()
            except Exception:
                continue
    return None


class OpenAIClient:
    name = "openai"

    def __init__(self, api_key: str, model: str) -> None:
        if not api_key:
            raise ValueError("OPENAI_API_KEY is required")
        self.model = model
        self._client = OpenAI(api_key=api_key)

    def generate(self, prompt: str, timeout_seconds: int) -> LLMProviderResponse:
        response = self._client.responses.create(
            model=self.model,
            input=prompt,
            timeout=timeout_seconds,
        )
        text = getattr(response, "output_text", None)
        response_dict = _response_to_dict(response)
        if text:
            return LLMProviderResponse(output_text=text, response=response_dict)
        if getattr(response, "output", None):
            return LLMProviderResponse(
                output_text=response.output[0].content[0].text,
                response=response_dict,
            )
        raise RuntimeError("OpenAI response missing output text")
