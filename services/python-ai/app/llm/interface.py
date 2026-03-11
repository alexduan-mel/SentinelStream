from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable, Protocol

import yaml
from pydantic import BaseModel, Field, ValidationError, field_validator


LOGGER = logging.getLogger(__name__)


def _taxonomy_paths() -> list[Path]:
    paths: list[Path] = []
    env_path = os.getenv("MARKET_TAXONOMY_PATH")
    if env_path:
        paths.append(Path(env_path))
    paths.append(Path("/app/config/market_taxonomy.yaml"))
    paths.append(Path.cwd() / "config" / "market_taxonomy.yaml")
    current = Path(__file__).resolve()
    for parent in current.parents:
        candidate = parent / "config" / "market_taxonomy.yaml"
        paths.append(candidate)
        if candidate.is_file():
            break
    return paths


def _load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle)
    return payload if isinstance(payload, dict) else {}


@lru_cache(maxsize=1)
def _load_market_taxonomy_raw() -> dict[str, list[str]]:
    data: dict[str, Any] = {}
    for path in _taxonomy_paths():
        if path.is_file():
            data = _load_yaml(path)
            break
    raw = data.get("sectors") if isinstance(data, dict) else None
    if not isinstance(raw, dict):
        LOGGER.warning("market_taxonomy_missing_or_invalid")
        return {}
    cleaned: dict[str, list[str]] = {}
    for sector, subtopics in raw.items():
        if not isinstance(sector, str):
            continue
        sector_key = sector.strip().lower()
        if not sector_key:
            continue
        items: list[str] = []
        if isinstance(subtopics, list):
            for item in subtopics:
                if not isinstance(item, str):
                    continue
                value = item.strip().lower()
                if value:
                    items.append(value)
        if items:
            cleaned[sector_key] = items
    if not cleaned:
        LOGGER.warning("market_taxonomy_empty")
    return cleaned


@lru_cache(maxsize=1)
def _load_market_taxonomy_sets() -> dict[str, set[str]]:
    raw = _load_market_taxonomy_raw()
    return {sector: set(subtopics) for sector, subtopics in raw.items()}


def _format_taxonomy_for_prompt() -> str:
    raw = _load_market_taxonomy_raw()
    if not raw:
        return ""
    lines = []
    for sector, subtopics in raw.items():
        lines.append(f"  {sector}: {', '.join(subtopics)}")
    return "\n".join(lines)


class AnalysisResult(BaseModel):
    tickers: list[str] = Field(default_factory=list)
    sentiment: str
    confidence: float
    reasoning_summary: str

    model_config = {
        "extra": "forbid",
        "strict": True,
    }

    @field_validator("tickers")
    @classmethod
    def _validate_tickers(cls, value: list[str]) -> list[str]:
        cleaned: list[str] = []
        for item in value:
            if not isinstance(item, str):
                raise ValueError("tickers must be strings")
            item = item.strip().upper()
            if not item:
                raise ValueError("tickers must be non-empty")
            cleaned.append(item)
        return list(dict.fromkeys(cleaned))

    @field_validator("sentiment")
    @classmethod
    def _validate_sentiment(cls, value: str) -> str:
        allowed = {"positive", "neutral", "negative"}
        if value not in allowed:
            raise ValueError("sentiment must be positive|neutral|negative")
        return value

    @field_validator("confidence")
    @classmethod
    def _validate_confidence(cls, value: float) -> float:
        if value < 0 or value > 1:
            raise ValueError("confidence must be between 0 and 1")
        return value

    @field_validator("reasoning_summary")
    @classmethod
    def _validate_summary(cls, value: str) -> str:
        if not isinstance(value, str):
            raise ValueError("reasoning_summary must be a string")
        summary = value.strip()
        if not summary:
            raise ValueError("reasoning_summary must be non-empty")
        if len(summary) > 280:
            raise ValueError("reasoning_summary must be <= 280 chars")
        return summary


class MarketAnalysisResult(BaseModel):
    sector: str
    subtopic: str
    subtopic_label: str
    topic_type: str
    direction: str
    summary: str
    affected_assets: list[object] = Field(default_factory=list)
    market_relevance_score: float

    model_config = {
        "extra": "forbid",
        "strict": True,
    }

    @field_validator("sector")
    @classmethod
    def _validate_sector(cls, value: str) -> str:
        if not isinstance(value, str):
            raise ValueError("sector must be a string")
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("sector must be non-empty")
        cleaned = cleaned.lower()
        taxonomy = _load_market_taxonomy_sets()
        if not taxonomy:
            raise ValueError("sector taxonomy is not configured")
        if cleaned not in taxonomy:
            raise ValueError("sector must be a supported value")
        return cleaned

    @field_validator("subtopic")
    @classmethod
    def _validate_subtopic(cls, value: str, info: Any) -> str:
        if not isinstance(value, str):
            raise ValueError("subtopic must be a string")
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("subtopic must be non-empty")
        cleaned = cleaned.lower()
        sector = info.data.get("sector") if hasattr(info, "data") else None
        if isinstance(sector, str):
            allowed = _load_market_taxonomy_sets().get(sector.lower(), set())
            if cleaned not in allowed:
                raise ValueError("subtopic must be a supported value for the sector")
        return cleaned

    @field_validator("subtopic_label")
    @classmethod
    def _validate_subtopic_label(cls, value: str) -> str:
        if not isinstance(value, str):
            raise ValueError("subtopic_label must be a string")
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("subtopic_label must be non-empty")
        if len(cleaned) > 120:
            raise ValueError("subtopic_label must be <= 120 chars")
        return cleaned

    @field_validator("topic_type")
    @classmethod
    def _validate_topic_type(cls, value: str) -> str:
        if not isinstance(value, str):
            raise ValueError("topic_type must be a string")
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("topic_type must be non-empty")
        return cleaned

    @field_validator("direction")
    @classmethod
    def _validate_direction(cls, value: str) -> str:
        if not isinstance(value, str):
            raise ValueError("direction must be a string")
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("direction must be non-empty")
        return cleaned

    @field_validator("summary")
    @classmethod
    def _validate_summary(cls, value: str) -> str:
        if not isinstance(value, str):
            raise ValueError("summary must be a string")
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("summary must be non-empty")
        return cleaned

    @field_validator("affected_assets")
    @classmethod
    def _validate_assets(cls, value: list[object]) -> list[object]:
        if not isinstance(value, list):
            raise ValueError("affected_assets must be a list")
        return value

    @field_validator("market_relevance_score")
    @classmethod
    def _validate_score(cls, value: float) -> float:
        if value < 0 or value > 1:
            raise ValueError("market_relevance_score must be between 0 and 1")
        return value


@dataclass(frozen=True)
class LLMProviderResponse:
    output_text: str
    response: dict[str, Any] | None


@dataclass(frozen=True)
class LLMRunAttempt:
    prompt: str
    output_text: str | None
    output_json: dict[str, Any] | None
    response: dict[str, Any] | None
    error: str | None


class LLMProvider(Protocol):
    name: str
    model: str

    def generate(self, prompt: str, timeout_seconds: int) -> LLMProviderResponse:
        ...


class LLMAnalysisError(RuntimeError):
    def __init__(self, message: str, attempts: list[LLMRunAttempt]):
        super().__init__(message)
        self.attempts = attempts


class ProviderError(RuntimeError):
    def __init__(self, message: str, code: str | None = None):
        super().__init__(message)
        self.code = code


def build_prompt(input_text: str) -> str:
    return (
        "You are a financial news analyst. "
        "Analyze the news below and output ONLY valid JSON with keys: "
        "tickers (list of strings), sentiment (positive|neutral|negative), "
        "confidence (0..1), reasoning_summary (<=280 chars). "
        "No markdown, no extra text.\n\n"
        f"NEWS:\n{input_text}\n"
    )


def build_market_prompt(input_text: str) -> str:
    title = ""
    url = ""
    publisher = ""
    content = ""
    for line in input_text.splitlines():
        if line.startswith("Title:"):
            title = line.replace("Title:", "", 1).strip()
        elif line.startswith("URL:"):
            url = line.replace("URL:", "", 1).strip()
        elif line.startswith("Publisher:"):
            publisher = line.replace("Publisher:", "", 1).strip()
        elif line.startswith("Content:"):
            content = line.replace("Content:", "", 1).strip()

    return (
        "You are a market news analyst. Output ONLY valid JSON with keys:\n"
        "sector, subtopic, subtopic_label, topic_type, direction, summary, affected_assets, market_relevance_score\n\n"
        "Classification:\n"
        "- sector must be one of the configured sectors\n"
        "- subtopic must be allowed for the chosen sector:\n"
        f"{_format_taxonomy_for_prompt()}\n"
        "- use `other` only if no listed subtopic fits\n"
        "- if conflict itself -> macro/geopolitics; sector-impact focus -> that sector\n\n"
        "subtopic_label:\n"
        "- 2-6 word noun phrase\n"
        "- not a sentence/headline\n"
        "- describe the core market narrative\n\n"
        "topic_type: equity | macro | commodity | policy | geopolitics | sector | other\n"
        "direction: bullish | bearish | neutral | mixed\n"
        "market_relevance_score: 0-1\n\n"
        "affected_assets:\n"
        "- only directly impacted assets, max 5\n"
        "- prefer commodities/ETFs/indexes for macro news\n"
        "- avoid speculative/weak links\n"
        "- must be objects: {symbol, asset_type, relation, confidence}\n"
        "- asset_type: equity | etf | commodity | index | fx | other\n"
        "- relation: positive | negative | mixed\n"
        "- confidence: 0-1\n"
        "- no plain ticker strings\n\n"
        "Return JSON only. No markdown.\n\n"
        "NEWS:\n"
        f"Title: {title}\n"
        f"URL: {url}\n"
        f"Publisher: {publisher}\n"
        f"Content: {content}\n"
    )


def build_retry_prompt(input_text: str) -> str:
    template = (
        '{"tickers":["AAPL"],"sentiment":"neutral","confidence":0.5,'
        '"reasoning_summary":"Short reason."}'
    )
    return (
        "STRICT MODE: Output ONLY JSON matching this exact schema. "
        "Do not include any extra keys, markdown, or commentary.\n"
        f"TEMPLATE:\n{template}\n\n"
        f"NEWS:\n{input_text}\n"
    )


def build_market_retry_prompt(input_text: str) -> str:
    template = (
        '{"sector":"information_technology","subtopic":"semiconductors","subtopic_label":"memory pricing",'
        '"topic_type":"sector","direction":"neutral","summary":"Brief summary.",'
        '"affected_assets":[{"symbol":"MU","asset_type":"equity","relation":"positive","confidence":0.7}],'
        '"market_relevance_score":0.5}'
    )
    return (
        "STRICT MODE: Output ONLY JSON matching this exact schema. "
        "Do not include any extra keys, markdown, or commentary.\n"
        f"TEMPLATE:\n{template}\n\n"
        f"NEWS:\n{input_text}\n"
    )


def parse_analysis_json(text: str) -> tuple[AnalysisResult, dict[str, Any]]:
    payload = json.loads(text)
    if not isinstance(payload, dict):
        raise ValueError("JSON root must be an object")
    return AnalysisResult.model_validate(payload), payload


def parse_market_analysis_json(text: str) -> tuple[MarketAnalysisResult, dict[str, Any]]:
    payload = json.loads(text)
    if not isinstance(payload, dict):
        raise ValueError("JSON root must be an object")
    return MarketAnalysisResult.model_validate(payload), payload


class LLMClient:
    def __init__(self, provider: LLMProvider, timeout_seconds: int, max_retries: int):
        self._provider = provider
        self._timeout_seconds = timeout_seconds
        self._max_retries = max_retries
        self.last_attempts: list[LLMRunAttempt] = []
        self.last_request: dict[str, Any] | None = None
        self.last_raw_output: dict[str, Any] | None = None

    @property
    def provider_name(self) -> str:
        return self._provider.name

    @property
    def model(self) -> str:
        return self._provider.model

    def analyze_news(self, input_text: str) -> AnalysisResult:
        self.last_attempts = []
        self.last_request = None
        self.last_raw_output = None
        prompts: Iterable[str] = [build_prompt(input_text)]
        retry_prompt = build_retry_prompt(input_text)
        logger = logging.getLogger(__name__)

        for attempt in range(self._max_retries + 1):
            if attempt > 0:
                time.sleep(2)
            prompt = prompts[0] if attempt == 0 else retry_prompt
            self.last_request = {
                "prompt": prompt,
                "provider": self.provider_name,
                "model": self.model,
                "timeout_seconds": self._timeout_seconds,
                "max_retries": self._max_retries,
                "temperature": None,
                "max_tokens": None,
            }
            output_text: str | None = None
            output_json: dict[str, Any] | None = None
            response_payload: dict[str, Any] | None = None
            error: str | None = None
            try:
                logger.info(
                    "llm_attempt provider=%s model=%s attempt=%s",
                    self.provider_name,
                    self.model,
                    attempt + 1,
                )
                provider_response = self._provider.generate(prompt, self._timeout_seconds)
                output_text = provider_response.output_text
                response_payload = provider_response.response
                result, output_json = parse_analysis_json(output_text)
                self.last_attempts.append(
                    LLMRunAttempt(
                        prompt=prompt,
                        output_text=output_text,
                        output_json=output_json,
                        response=response_payload,
                        error=None,
                    )
                )
                self.last_raw_output = {
                    "error": None,
                    "response": response_payload,
                    "output_text": output_text,
                    "output_json": output_json,
                }
                logger.info(
                    "llm_attempt_success provider=%s model=%s attempt=%s",
                    self.provider_name,
                    self.model,
                    attempt + 1,
                )
                return result
            except ProviderError as exc:
                error = f"provider_error:{exc.code}:{exc}" if exc.code else f"provider_error:{exc}"
                self.last_attempts.append(
                    LLMRunAttempt(
                        prompt=prompt,
                        output_text=output_text,
                        output_json=None,
                        response=response_payload,
                        error=error,
                    )
                )
                logger.warning(
                    "llm_attempt_failed provider=%s model=%s attempt=%s error=%s output_snippet=%s",
                    self.provider_name,
                    self.model,
                    attempt + 1,
                    error,
                    (output_text or "")[:200],
                )
                if exc.code == "insufficient_quota":
                    raise LLMAnalysisError("LLM analysis failed", self.last_attempts)
                continue
            except (json.JSONDecodeError, ValidationError, ValueError) as exc:
                error = str(exc)
            except Exception as exc:  # noqa: BLE001
                error = f"provider_error: {exc}"

            self.last_attempts.append(
                LLMRunAttempt(
                    prompt=prompt,
                    output_text=output_text,
                    output_json=output_json,
                    response=response_payload,
                    error=error,
                )
            )
            logger.warning(
                "llm_attempt_failed provider=%s model=%s attempt=%s error=%s output_snippet=%s",
                self.provider_name,
                self.model,
                attempt + 1,
                error,
                (output_text or "")[:200],
            )

        raise LLMAnalysisError("LLM analysis failed", self.last_attempts)

    def analyze_market_news(self, input_text: str) -> MarketAnalysisResult:
        self.last_attempts = []
        self.last_request = None
        self.last_raw_output = None
        prompts: Iterable[str] = [build_market_prompt(input_text)]
        retry_prompt = build_market_retry_prompt(input_text)
        logger = logging.getLogger(__name__)

        for attempt in range(self._max_retries + 1):
            if attempt > 0:
                time.sleep(2)
            prompt = prompts[0] if attempt == 0 else retry_prompt
            self.last_request = {
                "prompt": prompt,
                "provider": self.provider_name,
                "model": self.model,
                "timeout_seconds": self._timeout_seconds,
                "max_retries": self._max_retries,
                "temperature": None,
                "max_tokens": None,
            }
            output_text: str | None = None
            output_json: dict[str, Any] | None = None
            response_payload: dict[str, Any] | None = None
            error: str | None = None
            try:
                logger.info(
                    "llm_attempt provider=%s model=%s attempt=%s",
                    self.provider_name,
                    self.model,
                    attempt + 1,
                )
                provider_response = self._provider.generate(prompt, self._timeout_seconds)
                output_text = provider_response.output_text
                response_payload = provider_response.response
                result, output_json = parse_market_analysis_json(output_text)
                self.last_attempts.append(
                    LLMRunAttempt(
                        prompt=prompt,
                        output_text=output_text,
                        output_json=output_json,
                        response=response_payload,
                        error=None,
                    )
                )
                self.last_raw_output = {
                    "error": None,
                    "response": response_payload,
                    "output_text": output_text,
                    "output_json": output_json,
                }
                logger.info(
                    "llm_attempt_success provider=%s model=%s attempt=%s",
                    self.provider_name,
                    self.model,
                    attempt + 1,
                )
                return result
            except ProviderError as exc:
                error = f"provider_error:{exc.code}:{exc}" if exc.code else f"provider_error:{exc}"
                self.last_attempts.append(
                    LLMRunAttempt(
                        prompt=prompt,
                        output_text=output_text,
                        output_json=None,
                        response=response_payload,
                        error=error,
                    )
                )
                logger.warning(
                    "llm_attempt_failed provider=%s model=%s attempt=%s error=%s output_snippet=%s",
                    self.provider_name,
                    self.model,
                    attempt + 1,
                    error,
                    (output_text or "")[:200],
                )
                if exc.code == "insufficient_quota":
                    raise LLMAnalysisError("LLM analysis failed", self.last_attempts)
                continue
            except (json.JSONDecodeError, ValidationError, ValueError) as exc:
                error = str(exc)
            except Exception as exc:  # noqa: BLE001
                error = f"provider_error: {exc}"

            self.last_attempts.append(
                LLMRunAttempt(
                    prompt=prompt,
                    output_text=output_text,
                    output_json=output_json,
                    response=response_payload,
                    error=error,
                )
            )
            logger.warning(
                "llm_attempt_failed provider=%s model=%s attempt=%s error=%s output_snippet=%s",
                self.provider_name,
                self.model,
                attempt + 1,
                error,
                (output_text or "")[:200],
            )

        raise LLMAnalysisError("LLM analysis failed", self.last_attempts)
