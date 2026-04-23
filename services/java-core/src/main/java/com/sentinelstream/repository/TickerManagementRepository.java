package com.sentinelstream.repository;

import java.sql.ResultSet;
import java.sql.SQLException;
import java.time.OffsetDateTime;
import java.util.List;

import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.core.RowMapper;
import org.springframework.stereotype.Repository;

import com.sentinelstream.dto.TickerManagementItemResponse;

@Repository
public class TickerManagementRepository {
    private final JdbcTemplate jdbcTemplate;

    public TickerManagementRepository(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    public List<TickerManagementItemResponse> fetchTickerItems() {
        String sql = """
            WITH latest_news AS (
              SELECT ne.request_ticker AS symbol, MAX(ne.published_at) AS last_sync_at
              FROM news_events ne
              WHERE ne.request_ticker IS NOT NULL
              GROUP BY ne.request_ticker
            ),
            signal_counts AS (
              SELECT ne.request_ticker AS symbol, COUNT(*)::int AS signal_count
              FROM llm_analyses la
              JOIN news_events ne ON ne.id = la.news_event_id
              WHERE la.status = 'succeeded'
                AND ne.request_ticker IS NOT NULL
                AND la.entities @> to_jsonb(ARRAY[ne.request_ticker])
              GROUP BY ne.request_ticker
            ),
            job_status AS (
              SELECT ne.request_ticker AS symbol,
                     BOOL_OR(aj.status IN ('pending', 'running')) AS has_running,
                     BOOL_OR(aj.status = 'failed') AS has_failed
              FROM analysis_jobs aj
              JOIN news_events ne ON ne.id = aj.news_event_id
              WHERE aj.job_type IN ('llm_analysis_company', 'llm_analysis')
                AND ne.request_ticker IS NOT NULL
              GROUP BY ne.request_ticker
            )
            SELECT t.symbol,
                   t.name,
                   t.exchange,
                   CASE
                     WHEN COALESCE(js.has_failed, FALSE) THEN 'error'
                     WHEN COALESCE(js.has_running, FALSE) THEN 'active'
                     WHEN ln.last_sync_at IS NULL THEN 'paused'
                     WHEN ln.last_sync_at < NOW() - INTERVAL '7 days' THEN 'paused'
                     ELSE 'active'
                   END AS status,
                   TRUE AS news_enabled,
                   FALSE AS filings_enabled,
                   CASE
                     WHEN COALESCE(js.has_running, FALSE) THEN 'running'
                     WHEN COALESCE(js.has_failed, FALSE) THEN 'failed'
                     ELSE 'idle'
                   END AS job_status,
                   ln.last_sync_at,
                   COALESCE(sc.signal_count, 0) AS signal_count
            FROM tickers t
            LEFT JOIN latest_news ln ON ln.symbol = t.symbol
            LEFT JOIN signal_counts sc ON sc.symbol = t.symbol
            LEFT JOIN job_status js ON js.symbol = t.symbol
            ORDER BY t.symbol ASC
            """;
        return jdbcTemplate.query(sql, new TickerManagementRowMapper());
    }

    public TickerManagementItemResponse upsertTicker(String symbol, String name, String exchange) {
        String sql = """
            INSERT INTO tickers (symbol, name, exchange)
            VALUES (?, NULLIF(?, ''), NULLIF(?, ''))
            ON CONFLICT (symbol) DO UPDATE SET
              name = COALESCE(NULLIF(EXCLUDED.name, ''), tickers.name),
              exchange = COALESCE(NULLIF(EXCLUDED.exchange, ''), tickers.exchange)
            RETURNING symbol, name, exchange
            """;
        return jdbcTemplate.queryForObject(
            sql,
            (rs, rowNum) -> new TickerManagementItemResponse(
                rs.getString("symbol"),
                rs.getString("name"),
                rs.getString("exchange"),
                "active",
                true,
                false,
                "idle",
                null,
                0
            ),
            symbol,
            name,
            exchange
        );
    }

    public int deleteTicker(String symbol) {
        String sql = "DELETE FROM tickers WHERE symbol = ?";
        return jdbcTemplate.update(sql, symbol);
    }

    private static final class TickerManagementRowMapper implements RowMapper<TickerManagementItemResponse> {
        @Override
        public TickerManagementItemResponse mapRow(ResultSet rs, int rowNum) throws SQLException {
            return new TickerManagementItemResponse(
                rs.getString("symbol"),
                rs.getString("name"),
                rs.getString("exchange"),
                rs.getString("status"),
                rs.getBoolean("news_enabled"),
                rs.getBoolean("filings_enabled"),
                rs.getString("job_status"),
                rs.getObject("last_sync_at", OffsetDateTime.class),
                rs.getInt("signal_count")
            );
        }
    }
}
