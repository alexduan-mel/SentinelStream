from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

import psycopg2
from psycopg2 import errors
from psycopg2.extras import Json


@dataclass(frozen=True)
class AnalysisInput:
    analysis_id: int
    news_event_id: int
    published_at: datetime
    topic_family: str
    subtopic_label: str
    topic_type: str | None
    direction: str | None
    summary: str | None
    affected_assets: list[Any]
    relevance_score: float


@dataclass(frozen=True)
class TopicMatch:
    topic_id: int
    topic_key: str
    display_name: str
    summary: str | None
    similarity: float


@dataclass(frozen=True)
class CandidateMatch:
    candidate_id: int
    candidate_key: str
    candidate_label: str
    topic_family: str
    summary: str | None
    representative_subtopic: str | None
    evidence_count: int
    avg_relevance_score: float | None
    first_seen_at: datetime | None
    last_seen_at: datetime | None
    similarity: float


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


def build_clustering_text(subtopic_label: str, summary: str | None) -> str:
    parts = [subtopic_label.strip()]
    if summary:
        parts.append(summary.strip())
    return " ".join(part for part in parts if part)


def _tokenize(text: str) -> set[str]:
    normalized = re.sub(r"[^a-z0-9\s]", " ", text.lower())
    tokens = {token for token in normalized.split() if len(token) > 2}
    return tokens


def compute_similarity(text_a: str, text_b: str) -> float:
    tokens_a = _tokenize(text_a)
    tokens_b = _tokenize(text_b)
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = tokens_a.intersection(tokens_b)
    union = tokens_a.union(tokens_b)
    if not union:
        return 0.0
    return len(intersection) / len(union)


def _normalize_key(text: str) -> str:
    cleaned = re.sub(r"[^a-z0-9\s_]", " ", text.lower())
    cleaned = re.sub(r"[\s_]+", "_", cleaned).strip("_")
    return cleaned or "topic"


def build_candidate_key(topic_family: str, subtopic_label: str) -> str:
    return f"{_normalize_key(topic_family)}_{_normalize_key(subtopic_label)}"


def build_topic_key(topic_family: str, label: str) -> str:
    return f"{_normalize_key(topic_family)}_{_normalize_key(label)}"


def build_display_name(label: str) -> str:
    cleaned = label.strip()
    if not cleaned:
        return "Market theme"
    return cleaned[:1].upper() + cleaned[1:]


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
    topic_family = payload.get("topic_family")
    subtopic_label = payload.get("subtopic_label")
    if not isinstance(topic_family, str) or not topic_family.strip():
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
        topic_family = payload.get("topic_family", "").strip().lower()
        subtopic_label = payload.get("subtopic_label", "").strip()
        if not topic_family or not subtopic_label:
            continue
        if published_at.tzinfo is None:
            published_at = published_at.replace(tzinfo=timezone.utc)
        analyses.append(
            AnalysisInput(
                analysis_id=analysis_id,
                news_event_id=news_event_id,
                published_at=published_at,
                topic_family=topic_family,
                subtopic_label=subtopic_label,
                topic_type=payload.get("topic_type"),
                direction=payload.get("direction"),
                summary=payload.get("summary"),
                affected_assets=payload.get("affected_assets") or [],
                relevance_score=float(relevance),
            )
        )
    return analyses, scanned, skipped_low


def _fetch_topics(conn, topic_family: str) -> list[dict[str, Any]]:
    sql = (
        "SELECT id, topic_key, display_name, summary, status "
        "FROM market_pulse_topics "
        "WHERE topic_family = %s AND status != 'archived'"
    )
    with conn.cursor() as cursor:
        cursor.execute(sql, (topic_family,))
        return [
            {
                "id": row[0],
                "topic_key": row[1],
                "display_name": row[2],
                "summary": row[3],
                "status": row[4],
            }
            for row in cursor.fetchall()
        ]


def _fetch_candidates(conn, topic_family: str) -> list[dict[str, Any]]:
    sql = (
        "SELECT id, candidate_key, candidate_label, topic_family, representative_subtopic, summary, "
        "evidence_count, avg_relevance_score, first_seen_at, last_seen_at "
        "FROM market_pulse_candidates "
        "WHERE topic_family = %s AND status = 'candidate'"
    )
    with conn.cursor() as cursor:
        cursor.execute(sql, (topic_family,))
        return [
            {
                "id": row[0],
                "candidate_key": row[1],
                "candidate_label": row[2],
                "topic_family": row[3],
                "representative_subtopic": row[4],
                "summary": row[5],
                "evidence_count": row[6] or 0,
                "avg_relevance_score": row[7],
                "first_seen_at": row[8],
                "last_seen_at": row[9],
            }
            for row in cursor.fetchall()
        ]


def _find_promoted_topic_by_candidate_key(conn, candidate_key: str) -> TopicMatch | None:
    sql = (
        "SELECT t.id, t.topic_key, t.display_name, t.summary "
        "FROM market_pulse_candidates c "
        "JOIN market_pulse_topics t ON t.id = c.promoted_topic_id "
        "WHERE c.candidate_key = %s AND c.status = 'promoted' AND c.promoted_topic_id IS NOT NULL"
    )
    with conn.cursor() as cursor:
        cursor.execute(sql, (candidate_key,))
        row = cursor.fetchone()
    if not row:
        return None
    return TopicMatch(
        topic_id=row[0],
        topic_key=row[1],
        display_name=row[2],
        summary=row[3],
        similarity=1.0,
    )


def find_best_topic_match(
    conn, topic_family: str, clustering_text: str, threshold: float
) -> TopicMatch | None:
    best: TopicMatch | None = None
    for row in _fetch_topics(conn, topic_family):
        rep_text = build_clustering_text(row["display_name"], row["summary"])
        similarity = compute_similarity(clustering_text, rep_text)
        if similarity >= threshold and (best is None or similarity > best.similarity):
            best = TopicMatch(
                topic_id=row["id"],
                topic_key=row["topic_key"],
                display_name=row["display_name"],
                summary=row["summary"],
                similarity=similarity,
            )
    return best


def find_best_candidate_match(
    conn, topic_family: str, clustering_text: str, threshold: float
) -> CandidateMatch | None:
    best: CandidateMatch | None = None
    for row in _fetch_candidates(conn, topic_family):
        rep_label = row["representative_subtopic"] or row["candidate_label"]
        rep_text = build_clustering_text(rep_label or "", row["summary"])
        similarity = compute_similarity(clustering_text, rep_text)
        if similarity >= threshold and (best is None or similarity > best.similarity):
            best = CandidateMatch(
                candidate_id=row["id"],
                candidate_key=row["candidate_key"],
                candidate_label=row["candidate_label"],
                topic_family=row["topic_family"],
                summary=row["summary"],
                representative_subtopic=row["representative_subtopic"],
                evidence_count=row["evidence_count"],
                avg_relevance_score=row["avg_relevance_score"],
                first_seen_at=row["first_seen_at"],
                last_seen_at=row["last_seen_at"],
                similarity=similarity,
            )
    return best


def _insert_candidate(conn, analysis: AnalysisInput) -> CandidateMatch:
    candidate_key = build_candidate_key(analysis.topic_family, analysis.subtopic_label)
    candidate_label = analysis.subtopic_label
    with conn.cursor() as cursor:
        try:
            cursor.execute(
                "INSERT INTO market_pulse_candidates "
                "(topic_family, candidate_key, candidate_label, representative_subtopic, summary, "
                "status, evidence_count, avg_relevance_score, first_seen_at, last_seen_at, created_at, updated_at) "
                "VALUES (%s, %s, %s, %s, %s, 'candidate', 0, NULL, %s, %s, NOW(), NOW()) "
                "RETURNING id",
                (
                    analysis.topic_family,
                    candidate_key,
                    candidate_label,
                    analysis.subtopic_label,
                    analysis.summary,
                    analysis.published_at,
                    analysis.published_at,
                ),
            )
            candidate_id = cursor.fetchone()[0]
        except errors.UniqueViolation:
            conn.rollback()
            cursor.execute(
                "SELECT id, candidate_label, representative_subtopic, summary, evidence_count, "
                "avg_relevance_score, first_seen_at, last_seen_at "
                "FROM market_pulse_candidates WHERE candidate_key = %s",
                (candidate_key,),
            )
            row = cursor.fetchone()
            candidate_id = row[0]
            candidate_label = row[1]
            representative_subtopic = row[2]
            summary = row[3]
            evidence_count = row[4]
            avg_relevance_score = row[5]
            first_seen_at = row[6]
            last_seen_at = row[7]
            conn.commit()
            return CandidateMatch(
                candidate_id=candidate_id,
                candidate_key=candidate_key,
                candidate_label=candidate_label,
                topic_family=analysis.topic_family,
                summary=summary,
                representative_subtopic=representative_subtopic,
                evidence_count=evidence_count or 0,
                avg_relevance_score=avg_relevance_score,
                first_seen_at=first_seen_at,
                last_seen_at=last_seen_at,
                similarity=1.0,
            )
    conn.commit()
    return CandidateMatch(
        candidate_id=candidate_id,
        candidate_key=candidate_key,
        candidate_label=candidate_label,
        topic_family=analysis.topic_family,
        summary=analysis.summary,
        representative_subtopic=analysis.subtopic_label,
        evidence_count=0,
        avg_relevance_score=None,
        first_seen_at=analysis.published_at,
        last_seen_at=analysis.published_at,
        similarity=1.0,
    )


def _update_candidate(conn, candidate: CandidateMatch, analysis: AnalysisInput) -> CandidateMatch:
    new_count = candidate.evidence_count + 1
    prev_avg = candidate.avg_relevance_score or 0.0
    new_avg = (prev_avg * candidate.evidence_count + analysis.relevance_score) / new_count
    rep_subtopic = candidate.representative_subtopic or analysis.subtopic_label
    summary = candidate.summary or analysis.summary
    first_seen = candidate.first_seen_at or analysis.published_at
    last_seen = max(candidate.last_seen_at or analysis.published_at, analysis.published_at)
    with conn.cursor() as cursor:
        cursor.execute(
            "UPDATE market_pulse_candidates "
            "SET evidence_count = %s, avg_relevance_score = %s, "
            "representative_subtopic = %s, summary = %s, "
            "first_seen_at = %s, last_seen_at = %s, updated_at = NOW() "
            "WHERE id = %s",
            (
                new_count,
                new_avg,
                rep_subtopic,
                summary,
                first_seen,
                last_seen,
                candidate.candidate_id,
            ),
        )
    conn.commit()
    return CandidateMatch(
        candidate_id=candidate.candidate_id,
        candidate_key=candidate.candidate_key,
        candidate_label=candidate.candidate_label,
        topic_family=candidate.topic_family,
        summary=summary,
        representative_subtopic=rep_subtopic,
        evidence_count=new_count,
        avg_relevance_score=new_avg,
        first_seen_at=first_seen,
        last_seen_at=last_seen,
        similarity=candidate.similarity,
    )


def _insert_mention(
    conn,
    *,
    topic_id: int | None,
    candidate_id: int | None,
    analysis: AnalysisInput,
    similarity_score: float | None,
    reasoning_summary: str | None,
) -> bool:
    with conn.cursor() as cursor:
        cursor.execute(
            "INSERT INTO market_pulse_topic_mentions "
            "(topic_id, candidate_id, news_event_id, llm_analysis_id, topic_family, subtopic_label, "
            "reasoning_summary, relevance_score, similarity_score, assigned_at, created_at) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW()) "
            "ON CONFLICT DO NOTHING",
            (
                topic_id,
                candidate_id,
                analysis.news_event_id,
                analysis.analysis_id,
                analysis.topic_family,
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


def _mirror_candidate_mentions_to_topic(conn, candidate_id: int, topic_id: int) -> int:
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT news_event_id, llm_analysis_id, topic_family, subtopic_label, reasoning_summary, "
            "relevance_score, similarity_score, assigned_at "
            "FROM market_pulse_topic_mentions WHERE candidate_id = %s",
            (candidate_id,),
        )
        rows = cursor.fetchall()

    inserted = 0
    for (
        news_event_id,
        llm_analysis_id,
        topic_family,
        subtopic_label,
        reasoning_summary,
        relevance_score,
        similarity_score,
        assigned_at,
    ) in rows:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO market_pulse_topic_mentions "
                "(topic_id, candidate_id, news_event_id, llm_analysis_id, topic_family, subtopic_label, "
                "reasoning_summary, relevance_score, similarity_score, assigned_at, created_at) "
                "VALUES (%s, NULL, %s, %s, %s, %s, %s, %s, %s, %s, NOW()) "
                "ON CONFLICT DO NOTHING",
                (
                    topic_id,
                    news_event_id,
                    llm_analysis_id,
                    topic_family,
                    subtopic_label,
                    reasoning_summary,
                    relevance_score,
                    similarity_score,
                    assigned_at or datetime.now(timezone.utc),
                ),
            )
            inserted += cursor.rowcount
        conn.commit()
    return inserted


def _update_assets_from_candidate_mentions(conn, candidate_id: int, topic_id: int) -> int:
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT la.raw_output, ne.published_at "
            "FROM market_pulse_topic_mentions mtm "
            "JOIN llm_analyses la ON la.id = mtm.llm_analysis_id "
            "JOIN news_events ne ON ne.id = mtm.news_event_id "
            "WHERE mtm.candidate_id = %s AND mtm.llm_analysis_id IS NOT NULL",
            (candidate_id,),
        )
        rows = cursor.fetchall()
    updated = 0
    for raw_output, published_at in rows:
        payload = _extract_market_payload(raw_output)
        if not payload:
            continue
        affected_assets = payload.get("affected_assets") or []
        if published_at.tzinfo is None:
            published_at = published_at.replace(tzinfo=timezone.utc)
        updated += _update_asset_links_from_assets(conn, topic_id, affected_assets, published_at)
    return updated


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


def _promote_candidate_if_ready(
    conn,
    candidate: CandidateMatch,
    analysis: AnalysisInput,
    now: datetime,
    min_evidence: int,
    min_avg_relevance: float,
    recent_hours: int,
) -> int | None:
    if candidate.evidence_count < min_evidence:
        return None
    if candidate.avg_relevance_score is None or candidate.avg_relevance_score < min_avg_relevance:
        return None
    if candidate.last_seen_at and candidate.last_seen_at < now - timedelta(hours=recent_hours):
        return None

    display_name = build_display_name(candidate.representative_subtopic or candidate.candidate_label)
    topic_key = build_topic_key(candidate.topic_family, candidate.representative_subtopic or candidate.candidate_label)
    summary = candidate.summary or analysis.summary
    direction = analysis.direction

    with conn.cursor() as cursor:
        try:
            cursor.execute(
                "INSERT INTO market_pulse_topics "
                "(topic_key, display_name, topic_family, topic_type, summary, direction, status, "
                "evidence_count, first_seen_at, last_seen_at, source_candidate_id, created_at, updated_at) "
                "VALUES (%s, %s, %s, %s, %s, %s, 'active', %s, %s, %s, %s, NOW(), NOW()) "
                "RETURNING id",
                (
                    topic_key,
                    display_name,
                    analysis.topic_family,
                    analysis.topic_type,
                    summary,
                    direction,
                    candidate.evidence_count,
                    candidate.first_seen_at or now,
                    candidate.last_seen_at or now,
                    candidate.candidate_id,
                ),
            )
            topic_id = cursor.fetchone()[0]
        except errors.UniqueViolation:
            conn.rollback()
            cursor.execute("SELECT id FROM market_pulse_topics WHERE topic_key = %s", (topic_key,))
            row = cursor.fetchone()
            topic_id = row[0] if row else None
            if topic_id is None:
                return None
    conn.commit()

    with conn.cursor() as cursor:
        cursor.execute(
            "UPDATE market_pulse_candidates "
            "SET status = 'promoted', promoted_topic_id = %s, updated_at = NOW() "
            "WHERE id = %s",
            (topic_id, candidate.candidate_id),
        )
    conn.commit()
    _mirror_candidate_mentions_to_topic(conn, candidate.candidate_id, topic_id)
    _update_assets_from_candidate_mentions(conn, candidate.candidate_id, topic_id)
    return topic_id


def aggregate_market_pulse(conn, now: datetime | None = None) -> dict[str, int]:
    logger = logging.getLogger(__name__)
    now = now or datetime.now(timezone.utc)

    min_relevance = float(os.getenv("MARKET_PULSE_MIN_RELEVANCE", "0.35"))
    topic_similarity_threshold = float(os.getenv("MARKET_PULSE_TOPIC_SIMILARITY", "0.5"))
    candidate_similarity_threshold = float(os.getenv("MARKET_PULSE_CANDIDATE_SIMILARITY", "0.4"))
    promote_min_evidence = int(os.getenv("MARKET_PULSE_PROMOTE_MIN_EVIDENCE", "2"))
    promote_min_relevance = float(os.getenv("MARKET_PULSE_PROMOTE_MIN_RELEVANCE", "0.55"))
    promote_recent_hours = int(os.getenv("MARKET_PULSE_PROMOTE_RECENT_HOURS", "48"))

    analyses, scanned, skipped_low = _build_analysis_inputs(conn, min_relevance)

    matched_topics = 0
    matched_candidates = 0
    candidates_created = 0
    candidates_promoted = 0
    mentions_created = 0
    asset_links_updated = 0

    for analysis in analyses:
        clustering_text = build_clustering_text(analysis.subtopic_label, analysis.summary)

        topic_match = find_best_topic_match(conn, analysis.topic_family, clustering_text, topic_similarity_threshold)
        if topic_match:
            matched_topics += 1
            inserted = _insert_mention(
                conn,
                topic_id=topic_match.topic_id,
                candidate_id=None,
                analysis=analysis,
                similarity_score=topic_match.similarity,
                reasoning_summary=analysis.summary,
            )
            if inserted:
                mentions_created += 1
                asset_links_updated += _update_asset_links(conn, topic_match.topic_id, analysis)
                _update_topic_metrics(conn, topic_match.topic_id, now)
            continue

        candidate_key = build_candidate_key(analysis.topic_family, analysis.subtopic_label)
        promoted_topic = _find_promoted_topic_by_candidate_key(conn, candidate_key)
        if promoted_topic:
            matched_topics += 1
            inserted = _insert_mention(
                conn,
                topic_id=promoted_topic.topic_id,
                candidate_id=None,
                analysis=analysis,
                similarity_score=promoted_topic.similarity,
                reasoning_summary=analysis.summary,
            )
            if inserted:
                mentions_created += 1
                asset_links_updated += _update_asset_links(conn, promoted_topic.topic_id, analysis)
                _update_topic_metrics(conn, promoted_topic.topic_id, now)
            continue

        candidate_match = find_best_candidate_match(
            conn, analysis.topic_family, clustering_text, candidate_similarity_threshold
        )
        if candidate_match:
            matched_candidates += 1
            candidate = candidate_match
        else:
            candidate = _insert_candidate(conn, analysis)
            candidates_created += 1

        inserted = _insert_mention(
            conn,
            topic_id=None,
            candidate_id=candidate.candidate_id,
            analysis=analysis,
            similarity_score=candidate.similarity,
            reasoning_summary=analysis.summary,
        )
        if inserted:
            mentions_created += 1

        if inserted:
            candidate = _update_candidate(conn, candidate, analysis)

        topic_id = _promote_candidate_if_ready(
            conn,
            candidate,
            analysis,
            now,
            promote_min_evidence,
            promote_min_relevance,
            promote_recent_hours,
        )
        if topic_id:
            candidates_promoted += 1
            inserted_topic = _insert_mention(
                conn,
                topic_id=topic_id,
                candidate_id=None,
                analysis=analysis,
                similarity_score=1.0,
                reasoning_summary=analysis.summary,
            )
            if inserted_topic:
                mentions_created += 1
                asset_links_updated += _update_asset_links(conn, topic_id, analysis)
                _update_topic_metrics(conn, topic_id, now)

    result = {
        "analyses_scanned": scanned,
        "analyses_skipped_low_relevance": skipped_low,
        "matched_existing_topics": matched_topics,
        "matched_candidates": matched_candidates,
        "candidates_created": candidates_created,
        "candidates_promoted": candidates_promoted,
        "mentions_created": mentions_created,
        "asset_links_updated": asset_links_updated,
    }

    logger.info(
        "market_pulse_aggregation_complete analyses_scanned=%s skipped_low_relevance=%s "
        "matched_topics=%s matched_candidates=%s candidates_created=%s candidates_promoted=%s "
        "mentions_created=%s asset_links_updated=%s",
        scanned,
        skipped_low,
        matched_topics,
        matched_candidates,
        candidates_created,
        candidates_promoted,
        mentions_created,
        asset_links_updated,
    )

    return result
