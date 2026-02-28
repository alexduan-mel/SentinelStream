package com.sentinelstream.repository;

import java.sql.ResultSet;
import java.sql.SQLException;
import java.time.OffsetDateTime;
import java.util.List;
import java.util.UUID;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.core.RowMapper;
import org.springframework.stereotype.Repository;

import com.sentinelstream.dto.MonitorRowResponse;
import com.sentinelstream.dto.SignalSummaryResponse;

@Repository
public class MonitorRepository {
    private static final Logger LOGGER = LoggerFactory.getLogger(MonitorRepository.class);

    private final JdbcTemplate jdbcTemplate;

    public MonitorRepository(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    public List<MonitorRowResponse> fetchMonitorSnapshot() {
        String sql = """
            SELECT t.symbol AS ticker,
                   s.analysis_uuid AS analysis_id,
                   s.sentiment,
                   s.confidence,
                   s.summary,
                   s.published_at,
                   s.title,
                   s.url,
                   s.source
            FROM tickers t
            LEFT JOIN LATERAL (
                SELECT la.analysis_uuid,
                       la.sentiment,
                       la.confidence,
                       la.summary,
                       ne.published_at,
                       ne.title,
                       ne.url,
                       ne.source
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
        LOGGER.info("monitor_snapshot_sql={}", sql);
        return jdbcTemplate.query(sql, new MonitorRowMapper());
    }

    private static final class MonitorRowMapper implements RowMapper<MonitorRowResponse> {
        @Override
        public MonitorRowResponse mapRow(ResultSet rs, int rowNum) throws SQLException {
            String ticker = rs.getString("ticker");
            UUID analysisId = (UUID) rs.getObject("analysis_id");
            if (analysisId == null) {
                return new MonitorRowResponse(ticker, null);
            }
            SignalSummaryResponse signal = new SignalSummaryResponse(
                analysisId,
                ticker,
                rs.getString("sentiment"),
                (Double) rs.getObject("confidence"),
                rs.getString("summary"),
                rs.getObject("published_at", OffsetDateTime.class),
                rs.getString("title"),
                rs.getString("url"),
                rs.getString("source")
            );
            return new MonitorRowResponse(ticker, signal);
        }
    }
}
