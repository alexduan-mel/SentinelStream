package com.sentinelstream.dto;

import java.time.OffsetDateTime;

import com.fasterxml.jackson.annotation.JsonProperty;

public record TickerManagementItemResponse(
    String symbol,
    String name,
    String exchange,
    String status,
    @JsonProperty("news_enabled") boolean newsEnabled,
    @JsonProperty("filings_enabled") boolean filingsEnabled,
    @JsonProperty("job_status") String jobStatus,
    @JsonProperty("last_sync_at") OffsetDateTime lastSyncAt,
    @JsonProperty("signal_count") int signalCount
) {}
