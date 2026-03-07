package com.sentinelstream.repository;

import java.sql.ResultSet;
import java.sql.SQLException;
import java.time.OffsetDateTime;
import java.util.List;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.core.RowMapper;
import org.springframework.stereotype.Repository;

import com.sentinelstream.dto.SignalResponse;

@Repository
public class SignalSnapshotRepository {
    private static final Logger LOGGER = LoggerFactory.getLogger(SignalSnapshotRepository.class);

    private final JdbcTemplate jdbcTemplate;

    public SignalSnapshotRepository(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    public List<SignalResponse> fetchLatestSignalsByTicker() {
        String sql = """
            SELECT t.symbol AS request_ticker,
                   s.id,
                   s.title,
                   s.url,
                   s.source,
                   s.published_at,
                   s.sentiment,
                   s.confidence,
                   s.summary
            FROM tickers t
            LEFT JOIN LATERAL (
                SELECT ne.id,
                       ne.title,
                       ne.url,
                       ne.source,
                       ne.published_at,
                       la.sentiment,
                       la.confidence,
                       la.summary
                FROM news_events ne
                JOIN llm_analyses la ON la.news_event_id = ne.id
                WHERE la.status = 'succeeded'
                  AND ne.request_ticker = t.symbol
                  AND la.entities @> to_jsonb(ARRAY[t.symbol])
                ORDER BY ne.published_at DESC
                LIMIT 1
            ) s ON true
            ORDER BY t.symbol ASC
            """;
        LOGGER.info("signals_snapshot_sql={}", sql);
        return jdbcTemplate.query(sql, new SignalRowMapper());
    }

    private static final class SignalRowMapper implements RowMapper<SignalResponse> {
        @Override
        public SignalResponse mapRow(ResultSet rs, int rowNum) throws SQLException {
            return new SignalResponse(
                (Long) rs.getObject("id"),
                rs.getString("title"),
                rs.getString("url"),
                rs.getString("source"),
                rs.getString("request_ticker"),
                rs.getObject("published_at", OffsetDateTime.class),
                rs.getString("sentiment"),
                (Double) rs.getObject("confidence"),
                rs.getString("summary")
            );
        }
    }
}
