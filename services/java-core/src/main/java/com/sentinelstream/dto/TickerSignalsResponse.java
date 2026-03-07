package com.sentinelstream.dto;

import java.util.List;

public record TickerSignalsResponse(
    String ticker,
    SignalItemResponse latest,
    List<SignalItemResponse> items,
    int limit,
    int offset,
    long total
) {
}
