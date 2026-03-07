package com.sentinelstream.repository;

import java.sql.ResultSet;
import java.sql.SQLException;
import java.time.OffsetDateTime;
import java.util.List;
import java.util.UUID;

import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.core.RowMapper;
import org.springframework.stereotype.Repository;

import com.sentinelstream.dto.EvidenceItemResponse;
import com.sentinelstream.dto.SignalDetailResponse;

@Repository
public class SignalDetailRepository {
    private final JdbcTemplate jdbcTemplate;

    public SignalDetailRepository(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    public SignalDetailResponse fetchSignalDetail(long id) {
        String sql = """
            SELECT ne.request_ticker,
                   ne.title,
                   ne.url,
                   ne.source,
                   ne.published_at,
                   la.analysis_uuid,
                   la.sentiment,
                   la.confidence,
                   la.summary
            FROM news_events ne
            JOIN llm_analyses la ON la.news_event_id = ne.id
            WHERE la.status = 'succeeded'
              AND ne.id = ?
              AND la.entities @> to_jsonb(ARRAY[ne.request_ticker])
            ORDER BY la.updated_at DESC
            LIMIT 1
            """;
        List<SignalDetailResponse> results = jdbcTemplate.query(sql, new SignalDetailRowMapper(), id);
        return results.isEmpty() ? null : results.get(0);
    }

    public List<EvidenceItemResponse> fetchEvidenceItems(String ticker) {
        String sql = """
            SELECT ne.id,
                   ne.title,
                   ne.url,
                   ne.source,
                   ne.published_at,
                   la.confidence
            FROM news_events ne
            JOIN llm_analyses la ON la.news_event_id = ne.id
            WHERE la.status = 'succeeded'
              AND ne.request_ticker = ?
              AND la.entities @> to_jsonb(ARRAY[?::text])
            ORDER BY ne.published_at DESC
            """;
        return jdbcTemplate.query(sql, new EvidenceRowMapper(), ticker, ticker);
    }

    private static final class SignalDetailRowMapper implements RowMapper<SignalDetailResponse> {
        @Override
        public SignalDetailResponse mapRow(ResultSet rs, int rowNum) throws SQLException {
            return new SignalDetailResponse(
                (UUID) rs.getObject("analysis_uuid"),
                rs.getString("request_ticker"),
                rs.getString("sentiment"),
                (Double) rs.getObject("confidence"),
                rs.getString("summary"),
                rs.getObject("published_at", OffsetDateTime.class),
                rs.getString("title"),
                rs.getString("url"),
                rs.getString("source"),
                List.of()
            );
        }
    }

    private static final class EvidenceRowMapper implements RowMapper<EvidenceItemResponse> {
        @Override
        public EvidenceItemResponse mapRow(ResultSet rs, int rowNum) throws SQLException {
            return new EvidenceItemResponse(
                (Long) rs.getObject("id"),
                rs.getString("title"),
                rs.getString("url"),
                rs.getString("source"),
                rs.getObject("published_at", OffsetDateTime.class),
                (Double) rs.getObject("confidence")
            );
        }
    }
}
