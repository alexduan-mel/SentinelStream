package com.sentinelstream.repository;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.sql.Connection;
import java.sql.DriverManager;
import java.time.OffsetDateTime;
import java.time.ZoneOffset;
import java.util.List;
import java.util.UUID;

import org.junit.jupiter.api.Assumptions;
import org.junit.jupiter.api.Test;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.datasource.SingleConnectionDataSource;

import com.sentinelstream.dto.MarketPulseOverviewResponse;
import com.sentinelstream.dto.MarketPulseTopicCardResponse;
import com.sentinelstream.dto.MarketPulseTopicDetailResponse;

public class MarketPulseRepositoryTest {
    private Connection openConnection() throws Exception {
        String host = System.getenv("POSTGRES_HOST");
        String port = System.getenv("POSTGRES_PORT");
        String db = System.getenv("POSTGRES_DB");
        String user = System.getenv("POSTGRES_USER");
        String pass = System.getenv("POSTGRES_PASSWORD");
        Assumptions.assumeTrue(
            host != null && db != null && user != null && pass != null,
            "POSTGRES_* env vars not set"
        );
        String url = "jdbc:postgresql://" + host + ":" + (port == null ? "5432" : port) + "/" + db;
        return DriverManager.getConnection(url, user, pass);
    }

    @Test
    void testMarketPulseOverviewTopicsAndDetail() throws Exception {
        try (Connection conn = openConnection()) {
            JdbcTemplate jdbcTemplate = new JdbcTemplate(new SingleConnectionDataSource(conn, true));

            OffsetDateTime now = OffsetDateTime.now(ZoneOffset.UTC);
            Long event1 = jdbcTemplate.queryForObject(
                "INSERT INTO news_events (news_id, trace_id, provider, publisher, published_at, ingested_at, title, url, content, tickers, raw_payload, scope) "
                    + "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?::jsonb, ?::jsonb, ?) RETURNING id",
                Long.class,
                UUID.randomUUID().toString(),
                UUID.randomUUID().toString(),
                "finnhub",
                "Reuters",
                now.minusHours(2),
                now,
                "Market update 1",
                "https://example.com/1",
                "Body",
                "[]",
                "{}",
                "market"
            );
            Long event2 = jdbcTemplate.queryForObject(
                "INSERT INTO news_events (news_id, trace_id, provider, publisher, published_at, ingested_at, title, url, content, tickers, raw_payload, scope) "
                    + "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?::jsonb, ?::jsonb, ?) RETURNING id",
                Long.class,
                UUID.randomUUID().toString(),
                UUID.randomUUID().toString(),
                "finnhub",
                "Reuters",
                now.minusHours(1),
                now,
                "Market update 2",
                "https://example.com/2",
                "Body",
                "[]",
                "{}",
                "market"
            );

            Long topicId = jdbcTemplate.queryForObject(
                "INSERT INTO market_pulse_topics (topic_key, display_name, topic_type, direction, summary, status, evidence_count, first_seen_at, last_seen_at, intensity_score) "
                    + "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?) RETURNING id",
                Long.class,
                "memory_pricing",
                "Memory pricing",
                "sector",
                "neutral",
                "Prices stabilized",
                "new",
                2,
                now.minusHours(2),
                now.minusHours(1),
                0.8
            );

            jdbcTemplate.update(
                "INSERT INTO market_pulse_topic_mentions (topic_id, news_event_id, relevance_score, reasoning_summary) VALUES (?, ?, ?, ?)",
                topicId,
                event1,
                0.6,
                "Mention 1"
            );
            jdbcTemplate.update(
                "INSERT INTO market_pulse_topic_mentions (topic_id, news_event_id, relevance_score, reasoning_summary) VALUES (?, ?, ?, ?)",
                topicId,
                event2,
                0.7,
                "Mention 2"
            );

            jdbcTemplate.update(
                "INSERT INTO market_pulse_asset_links (topic_id, asset_symbol, asset_type, relation_type, confidence_score) VALUES (?, ?, ?, ?, ?)",
                topicId,
                "MU",
                "equity",
                "affected",
                0.9
            );
            jdbcTemplate.update(
                "INSERT INTO market_pulse_asset_links (topic_id, asset_symbol, asset_type, relation_type, confidence_score) VALUES (?, ?, ?, ?, ?)",
                topicId,
                "WDC",
                "equity",
                "affected",
                0.8
            );

            MarketPulseRepository repository = new MarketPulseRepository(jdbcTemplate);

            MarketPulseOverviewResponse overview = repository.fetchOverview(5);
            assertEquals(1, overview.activeThemeCount());
            assertEquals(1, overview.newThemeCount());
            assertEquals(0, overview.strengtheningThemeCount());
            assertEquals(1, overview.topCards().size());
            assertEquals("memory_pricing", overview.topCards().get(0).topicKey());
            assertEquals(2, overview.topCards().get(0).evidenceCount());

            List<MarketPulseTopicCardResponse> topics = repository.fetchTopics();
            assertEquals(1, topics.size());
            MarketPulseTopicCardResponse topicCard = topics.get(0);
            assertEquals("memory_pricing", topicCard.topicKey());
            assertEquals(2, topicCard.affectedAssets().size());
            assertTrue(topicCard.affectedAssets().contains("MU"));

            MarketPulseTopicDetailResponse detail = repository.fetchTopicDetail(topicId);
            assertNotNull(detail);
            assertEquals(2, detail.evidence().size());
            assertEquals(event2, detail.evidence().get(0).newsEventId());

            jdbcTemplate.update("DELETE FROM market_pulse_asset_links WHERE topic_id = ?", topicId);
            jdbcTemplate.update("DELETE FROM market_pulse_topic_mentions WHERE topic_id = ?", topicId);
            jdbcTemplate.update("DELETE FROM market_pulse_topics WHERE id = ?", topicId);
            jdbcTemplate.update("DELETE FROM news_events WHERE id = ?", event1);
            jdbcTemplate.update("DELETE FROM news_events WHERE id = ?", event2);
        }
    }
}
