package com.sentinelstream.dto;

public record TickerUpsertRequest(
    String symbol,
    String name,
    String exchange
) {}
