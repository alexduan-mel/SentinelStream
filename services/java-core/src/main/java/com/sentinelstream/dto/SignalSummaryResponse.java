package com.sentinelstream.dto;

import java.time.OffsetDateTime;
import java.util.UUID;

public record SignalSummaryResponse(
    UUID analysisId,
    String ticker,
    String sentiment,
    Double confidence,
    String summary,
    OffsetDateTime publishedAt,
    String title,
    String url,
    String source
) {
}
