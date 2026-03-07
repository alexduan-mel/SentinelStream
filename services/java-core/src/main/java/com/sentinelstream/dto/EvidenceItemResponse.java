package com.sentinelstream.dto;

import java.time.OffsetDateTime;

public record EvidenceItemResponse(
    Long id,
    String title,
    String url,
    String publisher,
    OffsetDateTime publishedAt,
    Double confidence
) {
}
