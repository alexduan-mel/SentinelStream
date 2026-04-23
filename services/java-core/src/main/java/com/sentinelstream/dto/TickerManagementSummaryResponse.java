package com.sentinelstream.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

public record TickerManagementSummaryResponse(
    @JsonProperty("total_tickers") int totalTickers,
    int active,
    int paused,
    int errors
) {}
