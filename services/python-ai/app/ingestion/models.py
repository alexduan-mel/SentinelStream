from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class NewsEvent(BaseModel):
    id: int | None = None
    news_id: str
    trace_id: UUID
    source: str = Field(default="finnhub")
    request_ticker: str | None = None
    published_at: datetime
    ingested_at: datetime
    title: str
    url: str
    content: str | None = None
    tickers: list[str]
    raw_payload: dict[str, Any]

    model_config = {
        "extra": "forbid",
    }
