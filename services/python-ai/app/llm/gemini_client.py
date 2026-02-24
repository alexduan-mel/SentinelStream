from __future__ import annotations

import logging

from google import genai

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


class GeminiClient:
    name = "gemini"

    def __init__(self, api_key: str, model: str, timeout_seconds: float) -> None:
        if not api_key:
            raise ValueError("GOOGLE_API_KEY is required")
        self.model = model
        # google-genai HttpOptions expects milliseconds; convert seconds -> ms
        timeout_ms = int(timeout_seconds * 1000)
        self._client = genai.Client(api_key=api_key, http_options={"timeout": timeout_ms})

    def generate(self, prompt: str, timeout_seconds: int) -> LLMProviderResponse:
        logger = logging.getLogger(__name__)
        response = self._client.models.generate_content(
            model=self.model,
            contents=prompt,
        )
        response_dict = _response_to_dict(response)
        text = getattr(response, "text", None)
        if text:
            logger.info("gemini_response model=%s chars=%s", self.model, len(text))
            return LLMProviderResponse(output_text=text, response=response_dict)
        if getattr(response, "candidates", None):
            text = response.candidates[0].content.parts[0].text
            logger.info("gemini_response model=%s chars=%s", self.model, len(text))
            return LLMProviderResponse(output_text=text, response=response_dict)
        raise RuntimeError("Gemini response missing output text")
