from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from analysis.service import analyze_news_event
from llm.interface import AnalysisResult

app = FastAPI(title="SentinelStream AI Service")


class AnalysisResponse(BaseModel):
    analysis_id: int | None = None
    status: str
    tickers: list[str] = []
    sentiment: str | None = None
    confidence: float | None = None
    reasoning_summary: str | None = None
    error_message: str | None = None


@app.post("/news-events/{news_event_id}/analysis", response_model=AnalysisResponse)
def analyze_news_event_endpoint(news_event_id: int) -> AnalysisResponse:
    result = analyze_news_event(news_event_id)
    if result.get("status") == "not_found":
        raise HTTPException(status_code=404, detail=result.get("error_message"))

    if result.get("status") == "failed":
        return AnalysisResponse(
            analysis_id=result.get("analysis_id"),
            status="failed",
            error_message=result.get("error_message"),
        )

    if result.get("analysis_kind") == "market":
        return AnalysisResponse(
            analysis_id=result.get("analysis_id"),
            status="succeeded",
            tickers=[],
            sentiment=result.get("sentiment"),
            confidence=result.get("impact_score"),
            reasoning_summary=result.get("summary"),
        )

    analysis: AnalysisResult = result.get("result")
    return AnalysisResponse(
        analysis_id=result.get("analysis_id"),
        status="succeeded",
        tickers=analysis.tickers,
        sentiment=analysis.sentiment,
        confidence=analysis.confidence,
        reasoning_summary=analysis.reasoning_summary,
    )
