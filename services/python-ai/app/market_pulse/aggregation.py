from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

import psycopg2


@dataclass(frozen=True)
class AnalysisInput:
    analysis_id: int
    news_event_id: int
    published_at: datetime
    sector: str
    subtopic: str
    subtopic_label: str
    topic_type: str | None
    direction: str | None
    summary: str | None
    affected_assets: list[Any]
    relevance_score: float


def connect_db():
    host = os.getenv("POSTGRES_HOST")
    port = int(os.getenv("POSTGRES_PORT", "5432"))
    name = os.getenv("POSTGRES_DB")
    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    missing = [key for key, value in {
        "POSTGRES_HOST": host,
        "POSTGRES_DB": name,
        "POSTGRES_USER": user,
        "POSTGRES_PASSWORD": password,
    }.items() if not value]
    if missing:
        raise RuntimeError(f"Missing DB environment variables: {', '.join(missing)}")
    conn = psycopg2.connect(
        host=host,
        port=port,
        dbname=name,
        user=user,
        password=password,
    )
    with conn.cursor() as cursor:
        cursor.execute("SET TIME ZONE 'UTC'")
    conn.commit()
    return conn


def build_topic_key(sector: str, subtopic: str) -> str:
    return f"{sector.strip().lower()}__{subtopic.strip().lower()}"


def build_display_name(label: str) -> str:
    cleaned = label.strip()
    if not cleaned:
        return "Market theme"
    return cleaned[:1].upper() + cleaned[1:]


def _normalize_direction(direction: str | None, sentiment: str | None) -> str | None:
    if isinstance(sentiment, str) and sentiment.strip():
        lowered = sentiment.strip().lower()
        if lowered in {"positive", "negative", "neutral", "mixed"}:
            return lowered
    if not direction:
        return None
    lowered = direction.strip().lower()
    if lowered == "bullish":
        return "positive"
    if lowered == "bearish":
        return "negative"
    if lowered in {"positive", "negative", "neutral", "mixed"}:
        return lowered
    return None

def _extract_market_payload(raw_output: Any) -> dict[str, Any] | None:
    if not isinstance(raw_output, dict):
        return None
    payload = None
    if isinstance(raw_output.get("normalized"), dict):
        payload = raw_output["normalized"]
    elif isinstance(raw_output.get("output_json"), dict):
        payload = raw_output["output_json"]
    elif isinstance(raw_output, dict):
        payload = raw_output
    if not isinstance(payload, dict):
        return None
    sector = payload.get("sector")
    subtopic = payload.get("subtopic")
    subtopic_label = payload.get("subtopic_label")
    if not isinstance(sector, str) or not sector.strip():
        return None
    if not isinstance(subtopic, str) or not subtopic.strip():
        return None
    if not isinstance(subtopic_label, str) or not subtopic_label.strip():
        return None
    return payload


def _build_analysis_inputs(conn, min_relevance: float) -> tuple[list[AnalysisInput], int, int]:
    sql = (
        "SELECT la.id, la.news_event_id, la.raw_output, la.impact_score, ne.published_at "
        "FROM llm_analyses la "
        "JOIN news_events ne ON ne.id = la.news_event_id "
        "LEFT JOIN market_pulse_topic_mentions mtm ON mtm.llm_analysis_id = la.id "
        "WHERE la.status = 'succeeded' AND ne.scope = 'market' AND mtm.id IS NULL"
    )
    with conn.cursor() as cursor:
        cursor.execute(sql)
        rows = cursor.fetchall()

    analyses: list[AnalysisInput] = []
    scanned = 0
    skipped_low = 0
    for analysis_id, news_event_id, raw_output, impact_score, published_at in rows:
        scanned += 1
        payload = _extract_market_payload(raw_output)
        if not payload:
            continue
        relevance = payload.get("market_relevance_score")
        if relevance is None and isinstance(impact_score, (int, float)):
            relevance = float(impact_score)
        if relevance is None or not isinstance(relevance, (int, float)) or float(relevance) < min_relevance:
            skipped_low += 1
            continue
        sector = payload.get("sector", "").strip().lower()
        subtopic = payload.get("subtopic", "").strip().lower()
        subtopic_label = payload.get("subtopic_label", "").strip()
        if not sector or not subtopic or not subtopic_label:
            continue
        if published_at.tzinfo is None:
            published_at = published_at.replace(tzinfo=timezone.utc)
        analyses.append(
            AnalysisInput(
                analysis_id=analysis_id,
                news_event_id=news_event_id,
                published_at=published_at,
                sector=sector,
                subtopic=subtopic,
                subtopic_label=subtopic_label,
        topic_type=payload.get("topic_type"),
        direction=_normalize_direction(payload.get("direction"), payload.get("sentiment")),
                summary=payload.get("summary"),
                affected_assets=payload.get("affected_assets") or [],
                relevance_score=float(relevance),
            )
        )
    return analyses, scanned, skipped_low


def _upsert_topic(conn, analysis: AnalysisInput) -> int:
    topic_key = build_topic_key(analysis.sector, analysis.subtopic)
    display_name = build_display_name(analysis.subtopic_label or analysis.subtopic)
    with conn.cursor() as cursor:
        cursor.execute(
            "INSERT INTO market_pulse_topics "
            "(topic_key, display_name, topic_family, sector, subtopic, topic_type, summary, direction, "
            "status, evidence_count, first_seen_at, last_seen_at, created_at, updated_at) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'active', 0, %s, %s, NOW(), NOW()) "
            "ON CONFLICT (topic_key) DO UPDATE SET "
            "display_name = EXCLUDED.display_name, "
            "topic_family = EXCLUDED.topic_family, "
            "sector = EXCLUDED.sector, "
            "subtopic = EXCLUDED.subtopic, "
            "topic_type = COALESCE(EXCLUDED.topic_type, market_pulse_topics.topic_type), "
            "summary = COALESCE(EXCLUDED.summary, market_pulse_topics.summary), "
            "direction = COALESCE(EXCLUDED.direction, market_pulse_topics.direction), "
            "last_seen_at = GREATEST(market_pulse_topics.last_seen_at, EXCLUDED.last_seen_at), "
            "updated_at = NOW() "
            "RETURNING id",
            (
                topic_key,
                display_name,
                analysis.sector,
                analysis.sector,
                analysis.subtopic,
                analysis.topic_type,
                analysis.summary,
                analysis.direction,
                analysis.published_at,
                analysis.published_at,
            ),
        )
        topic_id = cursor.fetchone()[0]
    conn.commit()
    return topic_id


def _insert_mention(
    conn,
    *,
    topic_id: int,
    analysis: AnalysisInput,
    similarity_score: float | None,
    reasoning_summary: str | None,
) -> bool:
    with conn.cursor() as cursor:
        cursor.execute(
            "INSERT INTO market_pulse_topic_mentions "
            "(topic_id, news_event_id, llm_analysis_id, topic_family, sector, subtopic, "
            "subtopic_label, reasoning_summary, relevance_score, similarity_score, assigned_at, created_at) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW()) "
            "ON CONFLICT DO NOTHING",
            (
                topic_id,
                analysis.news_event_id,
                analysis.analysis_id,
                analysis.sector,
                analysis.sector,
                analysis.subtopic,
                analysis.subtopic_label,
                reasoning_summary,
                analysis.relevance_score,
                similarity_score,
            ),
        )
        inserted = cursor.rowcount > 0
    conn.commit()
    return inserted


def _update_asset_links_from_assets(
    conn, topic_id: int, affected_assets: list[Any], published_at: datetime
) -> int:
    updated = 0
    symbols: dict[str, float] = {}
    for item in affected_assets:
        symbol = None
        confidence = 0.5
        if isinstance(item, str):
            symbol = item.strip().upper()
        elif isinstance(item, dict):
            raw_symbol = item.get("symbol") or item.get("ticker")
            if isinstance(raw_symbol, str):
                symbol = raw_symbol.strip().upper()
            raw_conf = item.get("confidence")
            if isinstance(raw_conf, (int, float)) and 0 <= float(raw_conf) <= 1:
                confidence = float(raw_conf)
        if symbol:
            prev = symbols.get(symbol)
            if prev is None or confidence > prev:
                symbols[symbol] = confidence
    for symbol, confidence in symbols.items():
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO market_pulse_asset_links "
                "(topic_id, asset_symbol, asset_type, relation_type, confidence_score, "
                "mention_count, first_seen_at, last_seen_at, created_at, updated_at) "
                "VALUES (%s, %s, %s, %s, %s, 1, %s, %s, NOW(), NOW()) "
                "ON CONFLICT (topic_id, asset_symbol) DO UPDATE SET "
                "confidence_score = GREATEST(market_pulse_asset_links.confidence_score, EXCLUDED.confidence_score), "
                "mention_count = market_pulse_asset_links.mention_count + 1, "
                "last_seen_at = GREATEST(market_pulse_asset_links.last_seen_at, EXCLUDED.last_seen_at), "
                "updated_at = NOW()",
                (
                    topic_id,
                    symbol,
                    None,
                    "affected",
                    confidence,
                    published_at,
                    published_at,
                ),
            )
            updated += cursor.rowcount
        conn.commit()
    return updated


def _update_asset_links(conn, topic_id: int, analysis: AnalysisInput) -> int:
    return _update_asset_links_from_assets(conn, topic_id, analysis.affected_assets, analysis.published_at)


def _compute_strength_score(recent_count: int, avg_relevance: float | None) -> float:
    if recent_count <= 0:
        return 0.0
    normalized_recent = min(1.0, recent_count / 5.0)
    relevance_component = max(0.0, min(1.0, avg_relevance or 0.0))
    return min(1.0, round(0.7 * normalized_recent + 0.3 * relevance_component, 4))


def _compute_topic_status(
    now: datetime,
    last_seen_at: datetime | None,
    recent_count: int,
    baseline_count: int,
) -> str:
    if last_seen_at and last_seen_at < now - timedelta(days=14):
        return "archived"
    if last_seen_at and last_seen_at < now - timedelta(days=3) and recent_count == 0:
        return "fading"
    if recent_count >= 2 and recent_count > baseline_count:
        return "strengthening"
    return "active"


def _update_topic_metrics(conn, topic_id: int, now: datetime) -> None:
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT COUNT(*), MIN(ne.published_at), MAX(ne.published_at) "
            "FROM market_pulse_topic_mentions mtm "
            "JOIN news_events ne ON ne.id = mtm.news_event_id "
            "WHERE mtm.topic_id = %s",
            (topic_id,),
        )
        row = cursor.fetchone()
    total_count = int(row[0]) if row and row[0] is not None else 0
    first_seen = row[1]
    last_seen = row[2]

    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT COUNT(*) "
            "FROM market_pulse_topic_mentions mtm "
            "JOIN news_events ne ON ne.id = mtm.news_event_id "
            "WHERE mtm.topic_id = %s AND ne.published_at >= %s",
            (topic_id, now - timedelta(hours=24)),
        )
        recent_count = int(cursor.fetchone()[0])

        cursor.execute(
            "SELECT COUNT(*) "
            "FROM market_pulse_topic_mentions mtm "
            "JOIN news_events ne ON ne.id = mtm.news_event_id "
            "WHERE mtm.topic_id = %s AND ne.published_at >= %s AND ne.published_at < %s",
            (topic_id, now - timedelta(hours=48), now - timedelta(hours=24)),
        )
        baseline_count = int(cursor.fetchone()[0])

        cursor.execute(
            "SELECT AVG(relevance_score) "
            "FROM market_pulse_topic_mentions "
            "WHERE topic_id = %s AND relevance_score IS NOT NULL",
            (topic_id,),
        )
        avg_relevance = cursor.fetchone()[0]

    status = _compute_topic_status(now, last_seen, recent_count, baseline_count)
    strength_score = _compute_strength_score(recent_count, avg_relevance)

    with conn.cursor() as cursor:
        cursor.execute(
            "UPDATE market_pulse_topics "
            "SET evidence_count = %s, first_seen_at = %s, last_seen_at = %s, "
            "status = %s, strength_score = %s, updated_at = NOW() "
            "WHERE id = %s",
            (
                total_count,
                first_seen or now,
                last_seen or now,
                status,
                strength_score,
                topic_id,
            ),
        )
    conn.commit()


def aggregate_market_pulse(conn, now: datetime | None = None) -> dict[str, int]:
    logger = logging.getLogger(__name__)
    now = now or datetime.now(timezone.utc)

    min_relevance = float(os.getenv("MARKET_PULSE_MIN_RELEVANCE", "0.35"))

    analyses, scanned, skipped_low = _build_analysis_inputs(conn, min_relevance)

    topics_upserted = 0
    mentions_created = 0
    asset_links_updated = 0

    for analysis in analyses:
        topic_id = _upsert_topic(conn, analysis)
        topics_upserted += 1
        inserted = _insert_mention(
            conn,
            topic_id=topic_id,
            analysis=analysis,
            similarity_score=None,
            reasoning_summary=analysis.summary,
        )
        if inserted:
            mentions_created += 1
            asset_links_updated += _update_asset_links(conn, topic_id, analysis)
            _update_topic_metrics(conn, topic_id, now)

    result = {
        "analyses_scanned": scanned,
        "analyses_skipped_low_relevance": skipped_low,
        "topics_upserted": topics_upserted,
        "mentions_created": mentions_created,
        "asset_links_updated": asset_links_updated,
    }

    logger.info(
        "market_pulse_aggregation_complete analyses_scanned=%s skipped_low_relevance=%s "
        "topics_upserted=%s mentions_created=%s asset_links_updated=%s",
        scanned,
        skipped_low,
        topics_upserted,
        mentions_created,
        asset_links_updated,
    )

    return result
