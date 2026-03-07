package com.sentinelstream.dto;

import java.time.OffsetDateTime;
import java.util.List;
import java.util.UUID;

import com.fasterxml.jackson.databind.JsonNode;

public record SignalItemResponse(
    UUID analysisId,
    String ticker,
    String sentiment,
    Double confidence,
    String summary,
    OffsetDateTime publishedAt,
    NewsSummaryResponse news,
    List<String> entities,
    JsonNode rawOutput
) {
}
