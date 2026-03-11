package com.sentinelstream.repository;

import java.sql.Array;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.time.OffsetDateTime;
import java.util.ArrayList;
import java.util.List;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.core.RowMapper;
import org.springframework.stereotype.Repository;

import com.sentinelstream.dto.MarketPulseEvidenceResponse;
import com.sentinelstream.dto.MarketPulseNarrativeResponse;
import com.sentinelstream.dto.MarketPulseOverviewCardResponse;
import com.sentinelstream.dto.MarketPulseOverviewResponse;
import com.sentinelstream.dto.MarketPulseTopicCardResponse;
import com.sentinelstream.dto.MarketPulseTopicDetailResponse;

@Repository
public class MarketPulseRepository {
    private static final Logger LOGGER = LoggerFactory.getLogger(MarketPulseRepository.class);

    private final JdbcTemplate jdbcTemplate;

    public MarketPulseRepository(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    public MarketPulseOverviewResponse fetchOverview(int topLimit) {
        String countSql = """
            SELECT COUNT(*) AS active_theme_count,
                   COUNT(*) FILTER (WHERE status = 'candidate') AS new_theme_count,
                   COUNT(*) FILTER (WHERE status = 'strengthening') AS strengthening_theme_count
            FROM market_pulse_topics
            WHERE status != 'archived'
            """;
        LOGGER.info("market_pulse_overview_count_sql={}", countSql);
        var counts = jdbcTemplate.queryForObject(countSql, (rs, rowNum) -> new int[] {
            rs.getInt("active_theme_count"),
            rs.getInt("new_theme_count"),
            rs.getInt("strengthening_theme_count")
        });

        List<MarketPulseOverviewCardResponse> topCards = fetchOverviewCards(topLimit);
        return new MarketPulseOverviewResponse(
            counts != null ? counts[0] : 0,
            counts != null ? counts[1] : 0,
            counts != null ? counts[2] : 0,
            topCards
        );
    }

    public List<MarketPulseTopicCardResponse> fetchTopics() {
        return fetchTopicCards(null);
    }

    public MarketPulseTopicDetailResponse fetchTopicDetail(long id) {
        String sql = """
            SELECT t.id,
                   t.topic_key,
                   t.display_name,
                   t.topic_type,
                   t.direction,
                   t.status,
                   t.strength_score AS intensity_score,
                   t.summary,
                   t.evidence_count,
                   t.first_seen_at,
                   t.last_seen_at,
                   COALESCE(array_remove(array_agg(DISTINCT l.asset_symbol ORDER BY l.asset_symbol), NULL), '{}')
                     AS affected_assets
            FROM market_pulse_topics t
            LEFT JOIN market_pulse_asset_links l ON l.topic_id = t.id
            WHERE t.id = ?
            GROUP BY t.id
            """;
        LOGGER.info("market_pulse_detail_sql={}", sql);
        List<MarketPulseTopicDetailResponse> topics = jdbcTemplate.query(
            sql,
            new MarketPulseDetailMapper(),
            id
        );
        if (topics.isEmpty()) {
            return null;
        }
        MarketPulseTopicDetailResponse base = topics.get(0);

        String evidenceSql = """
            SELECT mtm.news_event_id,
                   ne.title,
                   ne.publisher,
                   ne.published_at,
                   ne.url
            FROM market_pulse_topic_mentions mtm
            JOIN news_events ne ON ne.id = mtm.news_event_id
            WHERE mtm.topic_id = ?
            ORDER BY ne.published_at DESC
            LIMIT 10
            """;
        List<MarketPulseEvidenceResponse> evidence = jdbcTemplate.query(
            evidenceSql,
            new MarketPulseEvidenceMapper(),
            id
        );

        return new MarketPulseTopicDetailResponse(
            base.id(),
            base.topicKey(),
            base.displayName(),
            base.topicType(),
            base.direction(),
            base.status(),
            base.intensityScore(),
            base.summary(),
            base.affectedAssets(),
            base.evidenceCount(),
            base.firstSeenAt(),
            base.lastSeenAt(),
            evidence
        );
    }

    public List<MarketPulseNarrativeResponse> fetchNarratives(OffsetDateTime since, String assetClass, String sort) {
        String assetClassCase = """
            CASE
              WHEN LOWER(COALESCE(t.topic_type, '')) IN ('macro','geopolitics','policy') THEN 'macro'
              WHEN LOWER(COALESCE(t.topic_type, '')) IN ('commodity','commodities') THEN 'commodity'
              WHEN LOWER(COALESCE(t.topic_type, '')) = 'crypto' THEN 'crypto'
              WHEN LOWER(COALESCE(t.topic_family, '')) = 'macro' THEN 'macro'
              WHEN LOWER(COALESCE(t.topic_family, '')) = 'crypto' THEN 'crypto'
              WHEN LOWER(COALESCE(t.sector, '')) = 'macro' THEN 'macro'
              WHEN LOWER(COALESCE(t.sector, '')) IN ('energy','materials') THEN 'commodity'
              ELSE 'equity'
            END
            """;
        String directionCase = """
            CASE
              WHEN LOWER(COALESCE(t.direction, '')) IN ('positive','bullish') THEN 'bullish'
              WHEN LOWER(COALESCE(t.direction, '')) IN ('negative','bearish') THEN 'bearish'
              ELSE 'neutral'
            END
            """;
        String statusCase = """
            CASE
              WHEN t.status = 'candidate' THEN 'emerging'
              WHEN t.status = 'strengthening' THEN 'developing'
              WHEN t.status = 'active' THEN 'confirmed'
              WHEN t.status = 'fading' THEN 'fading'
              ELSE 'emerging'
            END
            """;
        StringBuilder sql = new StringBuilder("""
            SELECT t.id,
                   t.display_name AS title,
                   t.summary,
            """);
        sql.append(directionCase).append(" AS direction, ");
        sql.append(statusCase).append(" AS status, ");
        sql.append(assetClassCase).append(" AS asset_class, ");
        sql.append("""
                   t.sector AS sector,
                   t.subtopic AS subtopic,
                   COALESCE(t.strength_score, 0) AS signal_strength,
                   COALESCE(t.novelty_score, 0) AS momentum,
                   t.evidence_count AS source_count,
                   NULL::INTEGER AS source_delta,
                   t.last_seen_at AS last_updated_at,
                   t.first_seen_at AS first_seen_at,
                   COALESCE(array_remove(array_agg(DISTINCT l.asset_symbol ORDER BY l.asset_symbol), NULL), '{}')
                     AS affected_assets
            FROM market_pulse_topics t
            LEFT JOIN market_pulse_asset_links l ON l.topic_id = t.id
            WHERE t.status != 'archived'
            """);
        List<Object> params = new ArrayList<>();
        if (since != null) {
            sql.append(" AND t.last_seen_at >= ? ");
            params.add(since);
        }
        if (assetClass != null && !"all".equals(assetClass)) {
            sql.append(" AND ").append(assetClassCase).append(" = ? ");
            params.add(assetClass);
        }
        sql.append(" GROUP BY t.id ");
        if ("momentum".equals(sort)) {
            sql.append(" ORDER BY momentum DESC NULLS LAST, signal_strength DESC NULLS LAST ");
        } else if ("recent".equals(sort)) {
            sql.append(" ORDER BY t.last_seen_at DESC NULLS LAST ");
        } else {
            sql.append(" ORDER BY signal_strength DESC NULLS LAST, t.last_seen_at DESC NULLS LAST ");
        }
        LOGGER.info("market_pulse_narratives_sql={}", sql);
        return jdbcTemplate.query(sql.toString(), new MarketPulseNarrativeMapper(), params.toArray());
    }

    private List<MarketPulseOverviewCardResponse> fetchOverviewCards(Integer limit) {
        String sql = """
            SELECT t.id,
                   t.topic_key,
                   t.display_name,
                   t.status,
                   t.strength_score AS intensity_score,
                   t.summary,
                   t.evidence_count,
                   t.last_seen_at,
                   COALESCE(array_remove(array_agg(DISTINCT l.asset_symbol ORDER BY l.asset_symbol), NULL), '{}')
                     AS affected_assets
            FROM market_pulse_topics t
            LEFT JOIN market_pulse_asset_links l ON l.topic_id = t.id
            GROUP BY t.id
            ORDER BY t.strength_score DESC NULLS LAST, t.last_seen_at DESC NULLS LAST
            """;
        if (limit != null) {
            sql += " LIMIT " + limit;
        }
        LOGGER.info("market_pulse_overview_cards_sql={}", sql);
        return jdbcTemplate.query(sql, new MarketPulseOverviewCardMapper());
    }

    private List<MarketPulseTopicCardResponse> fetchTopicCards(Integer limit) {
        String sql = """
            SELECT t.id,
                   t.topic_key,
                   t.display_name,
                   t.topic_type,
                   t.direction,
                   t.status,
                   t.strength_score AS intensity_score,
                   t.summary,
                   t.evidence_count,
                   t.last_seen_at,
                   COALESCE(array_remove(array_agg(DISTINCT l.asset_symbol ORDER BY l.asset_symbol), NULL), '{}')
                     AS affected_assets
            FROM market_pulse_topics t
            LEFT JOIN market_pulse_asset_links l ON l.topic_id = t.id
            GROUP BY t.id
            ORDER BY t.strength_score DESC NULLS LAST, t.last_seen_at DESC NULLS LAST
            """;
        if (limit != null) {
            sql += " LIMIT " + limit;
        }
        LOGGER.info("market_pulse_topics_sql={}", sql);
        return jdbcTemplate.query(sql, new MarketPulseTopicCardMapper());
    }

    private static List<String> readStringArray(ResultSet rs, String column) throws SQLException {
        Array array = rs.getArray(column);
        if (array == null) {
            return List.of();
        }
        Object value = array.getArray();
        if (!(value instanceof Object[] items)) {
            return List.of();
        }
        List<String> result = new ArrayList<>();
        for (Object item : items) {
            if (item == null) {
                continue;
            }
            result.add(item.toString());
        }
        return result;
    }

    private static final class MarketPulseTopicCardMapper implements RowMapper<MarketPulseTopicCardResponse> {
        @Override
        public MarketPulseTopicCardResponse mapRow(ResultSet rs, int rowNum) throws SQLException {
            return new MarketPulseTopicCardResponse(
                rs.getLong("id"),
                rs.getString("topic_key"),
                rs.getString("display_name"),
                rs.getString("topic_type"),
                rs.getString("direction"),
                rs.getString("status"),
                (Double) rs.getObject("intensity_score"),
                rs.getString("summary"),
                readStringArray(rs, "affected_assets"),
                (Integer) rs.getObject("evidence_count"),
                rs.getObject("last_seen_at", OffsetDateTime.class)
            );
        }
    }

    private static final class MarketPulseOverviewCardMapper implements RowMapper<MarketPulseOverviewCardResponse> {
        @Override
        public MarketPulseOverviewCardResponse mapRow(ResultSet rs, int rowNum) throws SQLException {
            return new MarketPulseOverviewCardResponse(
                rs.getLong("id"),
                rs.getString("topic_key"),
                rs.getString("display_name"),
                rs.getString("status"),
                (Double) rs.getObject("intensity_score"),
                rs.getString("summary"),
                readStringArray(rs, "affected_assets"),
                (Integer) rs.getObject("evidence_count"),
                rs.getObject("last_seen_at", OffsetDateTime.class)
            );
        }
    }

    private static final class MarketPulseDetailMapper implements RowMapper<MarketPulseTopicDetailResponse> {
        @Override
        public MarketPulseTopicDetailResponse mapRow(ResultSet rs, int rowNum) throws SQLException {
            return new MarketPulseTopicDetailResponse(
                rs.getLong("id"),
                rs.getString("topic_key"),
                rs.getString("display_name"),
                rs.getString("topic_type"),
                rs.getString("direction"),
                rs.getString("status"),
                (Double) rs.getObject("intensity_score"),
                rs.getString("summary"),
                readStringArray(rs, "affected_assets"),
                (Integer) rs.getObject("evidence_count"),
                rs.getObject("first_seen_at", OffsetDateTime.class),
                rs.getObject("last_seen_at", OffsetDateTime.class),
                List.of()
            );
        }
    }

    private static final class MarketPulseEvidenceMapper implements RowMapper<MarketPulseEvidenceResponse> {
        @Override
        public MarketPulseEvidenceResponse mapRow(ResultSet rs, int rowNum) throws SQLException {
            return new MarketPulseEvidenceResponse(
                rs.getLong("news_event_id"),
                rs.getString("title"),
                rs.getString("publisher"),
                rs.getObject("published_at", OffsetDateTime.class),
                rs.getString("url")
            );
        }
    }

    private static final class MarketPulseNarrativeMapper implements RowMapper<MarketPulseNarrativeResponse> {
        @Override
        public MarketPulseNarrativeResponse mapRow(ResultSet rs, int rowNum) throws SQLException {
            return new MarketPulseNarrativeResponse(
                rs.getLong("id"),
                rs.getString("title"),
                rs.getString("summary"),
                rs.getString("direction"),
                rs.getString("status"),
                rs.getString("asset_class"),
                rs.getString("sector"),
                rs.getString("subtopic"),
                (Double) rs.getObject("signal_strength"),
                (Double) rs.getObject("momentum"),
                (Integer) rs.getObject("source_count"),
                (Integer) rs.getObject("source_delta"),
                readStringArray(rs, "affected_assets"),
                rs.getObject("last_updated_at", OffsetDateTime.class),
                rs.getObject("first_seen_at", OffsetDateTime.class)
            );
        }
    }
}
