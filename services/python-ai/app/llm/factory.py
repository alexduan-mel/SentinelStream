from __future__ import annotations

import os

from llm.gemini_client import GeminiClient
from llm.interface import LLMClient
from llm.openai_client import OpenAIClient


def load_llm_client(
    *,
    provider_override: str | None = None,
    openai_cls=OpenAIClient,
    gemini_cls=GeminiClient,
) -> LLMClient:
    provider = (provider_override or os.getenv("LLM_PROVIDER", "openai")).lower()
    timeout_seconds = float(os.getenv("LLM_TIMEOUT_SECONDS", "20"))
    if timeout_seconds <= 0:
        timeout_seconds = 20.0
    max_retries = int(os.getenv("LLM_MAX_RETRIES", "2"))

    if provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        client = openai_cls(api_key=api_key, model=model)
        return LLMClient(client, timeout_seconds, max_retries)

    if provider != "gemini":
        provider = "gemini"

    api_key = os.getenv("GOOGLE_API_KEY")
    model = os.getenv("GEMINI_MODEL", "gemini-3-flash-preview")
    client = gemini_cls(api_key=api_key, model=model, timeout_seconds=timeout_seconds)
    return LLMClient(client, timeout_seconds, max_retries)

    # unreachable
