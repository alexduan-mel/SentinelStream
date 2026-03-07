package com.sentinelstream.dto;

import java.time.OffsetDateTime;
import java.util.List;
import java.util.UUID;

public record SignalDetailResponse(
    UUID analysisId,
    String ticker,
    String sentiment,
    Double confidence,
    String summary,
    OffsetDateTime publishedAt,
    String title,
    String url,
    String source,
    List<EvidenceItemResponse> evidenceItems
) {
}
