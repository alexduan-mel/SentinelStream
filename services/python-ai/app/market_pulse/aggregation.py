from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

import psycopg2


@dataclass(frozen=True)
class TopicFields:
    topic_key: str
    main_topic: str
    topic_type: str | None
    direction: str | None
    summary: str | None


@dataclass(frozen=True)
class AnalysisRecord:
    news_event_id: int
    published_at: datetime
    impact_score: float | None
    entities: list[dict[str, Any]]
    topic: TopicFields


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


def _extract_topic_fields(raw_output: Any) -> TopicFields | None:
    if not isinstance(raw_output, dict):
        return None
    payload = None
    if isinstance(raw_output.get("normalized"), dict):
        payload = raw_output["normalized"]
    elif isinstance(raw_output.get("output_json"), dict):
        payload = raw_output["output_json"]
    elif all(key in raw_output for key in ("topic_key", "main_topic")):
        payload = raw_output

    if not isinstance(payload, dict):
        return None

    topic_key = payload.get("topic_key")
    main_topic = payload.get("main_topic")
    if not isinstance(topic_key, str) or not topic_key.strip():
        return None
    if not isinstance(main_topic, str) or not main_topic.strip():
        return None

    topic_type = payload.get("topic_type")
    direction = payload.get("direction")
    summary = payload.get("summary")
    return TopicFields(
        topic_key=topic_key.strip(),
        main_topic=main_topic.strip(),
        topic_type=topic_type.strip() if isinstance(topic_type, str) and topic_type.strip() else None,
        direction=direction.strip() if isinstance(direction, str) and direction.strip() else None,
        summary=summary.strip() if isinstance(summary, str) and summary.strip() else None,
    )


def _normalize_entities(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    normalized: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        symbol = item.get("symbol")
        if not isinstance(symbol, str) or not symbol.strip():
            continue
        symbol = symbol.strip().upper()
        confidence = item.get("confidence")
        if isinstance(confidence, (int, float)) and 0 <= float(confidence) <= 1:
            conf_value = float(confidence)
        else:
            conf_value = 0.5
        normalized.append({"symbol": symbol, "confidence": conf_value})
    return normalized


def _compute_status(
    now: datetime,
    first_seen_at: datetime | None,
    evidence_count: int,
    recent_count: int,
    baseline_count: int,
) -> str:
    if first_seen_at and first_seen_at >= now - timedelta(hours=24) and evidence_count <= 3:
        return "new"
    if recent_count >= 2 and recent_count > baseline_count:
        return "strengthening"
    return "ongoing"


def _compute_intensity(recent_count: int, avg_impact: float | None) -> float:
    if recent_count <= 0:
        return 0.0
    normalized_recent = min(1.0, recent_count / 5.0)
    impact_component = max(0.0, min(1.0, avg_impact)) if avg_impact is not None else 0.0
    intensity = 0.7 * normalized_recent + 0.3 * impact_component
    return min(1.0, round(intensity, 4))


def aggregate_market_pulse(conn, now: datetime | None = None) -> dict[str, int]:
    logger = logging.getLogger(__name__)
    now = now or datetime.now(timezone.utc)

    sql = (
        "SELECT la.news_event_id, la.entities, la.impact_score, la.raw_output, ne.published_at "
        "FROM llm_analyses la "
        "JOIN news_events ne ON ne.id = la.news_event_id "
        "WHERE la.status = 'succeeded' AND ne.scope = 'market'"
    )
    with conn.cursor() as cursor:
        cursor.execute(sql)
        rows = cursor.fetchall()

    records: list[AnalysisRecord] = []
    skipped = 0
    for news_event_id, entities, impact_score, raw_output, published_at in rows:
        topic = _extract_topic_fields(raw_output)
        if not topic:
            skipped += 1
            continue
        if published_at.tzinfo is None:
            published_at = published_at.replace(tzinfo=timezone.utc)
        entities_norm = _normalize_entities(entities)
        records.append(
            AnalysisRecord(
                news_event_id=news_event_id,
                published_at=published_at,
                impact_score=impact_score,
                entities=entities_norm,
                topic=topic,
            )
        )

    grouped: dict[str, list[AnalysisRecord]] = {}
    for record in records:
        grouped.setdefault(record.topic.topic_key, []).append(record)

    topics_upserted = 0
    mentions_inserted = 0
    assets_upserted = 0

    for topic_key, items in grouped.items():
        items_sorted = sorted(items, key=lambda r: r.published_at, reverse=True)
        latest = items_sorted[0]
        display_name = latest.topic.main_topic
        topic_type = latest.topic.topic_type
        direction = latest.topic.direction
        summary = latest.topic.summary

        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO market_pulse_topics "
                "(topic_key, display_name, topic_type, direction, summary, updated_at) "
                "VALUES (%s, %s, %s, %s, %s, NOW()) "
                "ON CONFLICT (topic_key) DO UPDATE SET "
                "display_name = EXCLUDED.display_name, "
                "topic_type = EXCLUDED.topic_type, "
                "direction = EXCLUDED.direction, "
                "summary = EXCLUDED.summary, "
                "updated_at = NOW() "
                "RETURNING id",
                (topic_key, display_name, topic_type, direction, summary),
            )
            topic_id = cursor.fetchone()[0]
        conn.commit()
        topics_upserted += 1

        for record in items:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT 1 FROM market_pulse_topic_mentions "
                    "WHERE topic_id = %s AND news_event_id = %s",
                    (topic_id, record.news_event_id),
                )
                exists = cursor.fetchone() is not None
            if exists:
                continue
            with conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO market_pulse_topic_mentions "
                    "(topic_id, news_event_id, relevance_score, reasoning_summary, created_at) "
                    "VALUES (%s, %s, %s, %s, NOW())",
                    (
                        topic_id,
                        record.news_event_id,
                        record.impact_score,
                        record.topic.summary,
                    ),
                )
            conn.commit()
            mentions_inserted += 1

        asset_symbols: dict[str, float] = {}
        for record in items:
            for entity in record.entities:
                symbol = entity.get("symbol")
                confidence = entity.get("confidence")
                if not symbol:
                    continue
                try:
                    conf_value = float(confidence)
                except (TypeError, ValueError):
                    conf_value = 0.5
                prev = asset_symbols.get(symbol)
                if prev is None or conf_value > prev:
                    asset_symbols[symbol] = conf_value

        for symbol, confidence in asset_symbols.items():
            with conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE market_pulse_asset_links "
                    "SET confidence_score = GREATEST(confidence_score, %s) "
                    "WHERE topic_id = %s AND asset_symbol = %s",
                    (confidence, topic_id, symbol),
                )
                updated = cursor.rowcount
            if updated:
                conn.commit()
                continue
            with conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO market_pulse_asset_links "
                    "(topic_id, asset_symbol, asset_type, relation_type, confidence_score, created_at) "
                    "VALUES (%s, %s, %s, %s, %s, NOW())",
                    (topic_id, symbol, None, "affected", confidence),
                )
            conn.commit()
            assets_upserted += 1

        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*), MIN(ne.published_at), MAX(ne.published_at) "
                "FROM market_pulse_topic_mentions mtm "
                "JOIN news_events ne ON ne.id = mtm.news_event_id "
                "WHERE mtm.topic_id = %s",
                (topic_id,),
            )
            count_row = cursor.fetchone()
        evidence_count = int(count_row[0]) if count_row and count_row[0] is not None else 0
        first_seen_at = count_row[1]
        last_seen_at = count_row[2]

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
                "SELECT AVG(la.impact_score) "
                "FROM market_pulse_topic_mentions mtm "
                "JOIN news_events ne ON ne.id = mtm.news_event_id "
                "JOIN llm_analyses la ON la.news_event_id = mtm.news_event_id "
                "WHERE mtm.topic_id = %s AND la.status = 'succeeded' "
                "AND la.impact_score IS NOT NULL AND ne.published_at >= %s",
                (topic_id, now - timedelta(hours=24)),
            )
            avg_impact_row = cursor.fetchone()
            avg_impact = avg_impact_row[0] if avg_impact_row else None

        status = _compute_status(now, first_seen_at, evidence_count, recent_count, baseline_count)
        intensity_score = _compute_intensity(recent_count, avg_impact)

        with conn.cursor() as cursor:
            cursor.execute(
                "UPDATE market_pulse_topics "
                "SET evidence_count = %s, first_seen_at = %s, last_seen_at = %s, "
                "status = %s, intensity_score = %s, updated_at = NOW() "
                "WHERE id = %s",
                (
                    evidence_count,
                    first_seen_at,
                    last_seen_at,
                    status,
                    intensity_score,
                    topic_id,
                ),
            )
        conn.commit()

    logger.info(
        "market_pulse_aggregation_complete topics=%s mentions=%s assets=%s skipped=%s",
        topics_upserted,
        mentions_inserted,
        assets_upserted,
        skipped,
    )

    return {
        "topics_upserted": topics_upserted,
        "mentions_inserted": mentions_inserted,
        "assets_upserted": assets_upserted,
        "skipped": skipped,
    }
