package com.sentinelstream.dto;

public record MonitorRowResponse(
    String ticker,
    SignalSummaryResponse signal
) {
}
