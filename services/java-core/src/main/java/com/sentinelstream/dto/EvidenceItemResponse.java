package com.sentinelstream.dto;

import java.time.OffsetDateTime;

public record EvidenceItemResponse(
    Long id,
    String title,
    String url,
    String source,
    OffsetDateTime publishedAt,
    Double confidence
) {
}
