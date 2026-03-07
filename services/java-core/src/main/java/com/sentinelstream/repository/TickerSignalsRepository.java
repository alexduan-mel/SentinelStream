package com.sentinelstream.repository;

import java.sql.ResultSet;
import java.sql.SQLException;
import java.time.OffsetDateTime;
import java.util.Collections;
import java.util.List;
import java.util.UUID;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.core.RowMapper;
import org.springframework.stereotype.Repository;

import com.sentinelstream.dto.NewsSummaryResponse;
import com.sentinelstream.dto.SignalItemResponse;

@Repository
public class TickerSignalsRepository {
    private static final TypeReference<List<String>> STRING_LIST = new TypeReference<>() {};

    private final JdbcTemplate jdbcTemplate;
    private final ObjectMapper objectMapper;

    public TickerSignalsRepository(JdbcTemplate jdbcTemplate, ObjectMapper objectMapper) {
        this.jdbcTemplate = jdbcTemplate;
        this.objectMapper = objectMapper;
    }

    public List<SignalItemResponse> fetchSignals(
        String ticker,
        int limit,
        int offset,
        boolean includeRaw
    ) {
        String selectRaw = includeRaw ? ", la.raw_output\n" : "\n";
        String sql = """
            SELECT la.analysis_uuid,
                   ne.request_ticker,
                   la.sentiment,
                   la.confidence,
                   la.summary,
                   ne.published_at,
                   ne.title,
                   ne.url,
                   ne.source,
                   la.entities
            """
            + selectRaw
            + """
            FROM llm_analyses la
            JOIN news_events ne ON ne.id = la.news_event_id
            WHERE la.status = 'succeeded'
              AND ne.request_ticker = ?
              AND la.entities @> to_jsonb(ARRAY[?::text])
            ORDER BY ne.published_at DESC
            LIMIT ? OFFSET ?
            """;
        return jdbcTemplate.query(
            sql,
            new SignalRowMapper(includeRaw, objectMapper),
            ticker,
            ticker,
            limit,
            offset
        );
    }

    public SignalItemResponse fetchLatest(String ticker, boolean includeRaw) {
        List<SignalItemResponse> items = fetchSignals(ticker, 1, 0, includeRaw);
        return items.isEmpty() ? null : items.get(0);
    }

    public long countSignals(String ticker) {
        String sql = """
            SELECT COUNT(*)
            FROM llm_analyses la
            JOIN news_events ne ON ne.id = la.news_event_id
            WHERE la.status = 'succeeded'
              AND ne.request_ticker = ?
              AND la.entities @> to_jsonb(ARRAY[?::text])
            """;
        Long count = jdbcTemplate.queryForObject(sql, Long.class, ticker, ticker);
        return count == null ? 0 : count;
    }

    private static final class SignalRowMapper implements RowMapper<SignalItemResponse> {
        private final boolean includeRaw;
        private final ObjectMapper objectMapper;

        private SignalRowMapper(boolean includeRaw, ObjectMapper objectMapper) {
            this.includeRaw = includeRaw;
            this.objectMapper = objectMapper;
        }

        @Override
        public SignalItemResponse mapRow(ResultSet rs, int rowNum) throws SQLException {
            UUID analysisId = (UUID) rs.getObject("analysis_uuid");
            String ticker = rs.getString("request_ticker");
            String sentiment = rs.getString("sentiment");
            Double confidence = (Double) rs.getObject("confidence");
            String summary = rs.getString("summary");
            OffsetDateTime publishedAt = rs.getObject("published_at", OffsetDateTime.class);
            NewsSummaryResponse news = new NewsSummaryResponse(
                rs.getString("title"),
                rs.getString("url"),
                rs.getString("source")
            );
            List<String> entities = readEntities(rs.getString("entities"));
            JsonNode rawOutput = null;
            if (includeRaw) {
                rawOutput = readJsonNode(rs.getString("raw_output"));
            }
            return new SignalItemResponse(
                analysisId,
                ticker,
                sentiment,
                confidence,
                summary,
                publishedAt,
                news,
                entities,
                rawOutput
            );
        }

        private List<String> readEntities(String value) {
            if (value == null || value.isBlank()) {
                return Collections.emptyList();
            }
            try {
                return objectMapper.readValue(value, STRING_LIST);
            } catch (Exception ex) {
                return Collections.emptyList();
            }
        }

        private JsonNode readJsonNode(String value) {
            if (value == null || value.isBlank()) {
                return null;
            }
            try {
                return objectMapper.readTree(value);
            } catch (Exception ex) {
                return null;
            }
        }
    }
}
