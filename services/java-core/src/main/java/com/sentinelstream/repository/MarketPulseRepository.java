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
                   COUNT(*) FILTER (WHERE status = 'new') AS new_theme_count,
                   COUNT(*) FILTER (WHERE status = 'strengthening') AS strengthening_theme_count
            FROM market_pulse_topics
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
                   t.intensity_score,
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

    private List<MarketPulseOverviewCardResponse> fetchOverviewCards(Integer limit) {
        String sql = """
            SELECT t.id,
                   t.topic_key,
                   t.display_name,
                   t.status,
                   t.intensity_score,
                   t.summary,
                   t.evidence_count,
                   t.last_seen_at,
                   COALESCE(array_remove(array_agg(DISTINCT l.asset_symbol ORDER BY l.asset_symbol), NULL), '{}')
                     AS affected_assets
            FROM market_pulse_topics t
            LEFT JOIN market_pulse_asset_links l ON l.topic_id = t.id
            GROUP BY t.id
            ORDER BY t.intensity_score DESC NULLS LAST, t.last_seen_at DESC NULLS LAST
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
                   t.intensity_score,
                   t.summary,
                   t.evidence_count,
                   t.last_seen_at,
                   COALESCE(array_remove(array_agg(DISTINCT l.asset_symbol ORDER BY l.asset_symbol), NULL), '{}')
                     AS affected_assets
            FROM market_pulse_topics t
            LEFT JOIN market_pulse_asset_links l ON l.topic_id = t.id
            GROUP BY t.id
            ORDER BY t.intensity_score DESC NULLS LAST, t.last_seen_at DESC NULLS LAST
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
}
