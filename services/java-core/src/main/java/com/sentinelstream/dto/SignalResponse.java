package com.sentinelstream.dto;

import java.time.OffsetDateTime;

public record SignalResponse(
    Long id,
    String title,
    String url,
    String source,
    String requestTicker,
    OffsetDateTime publishedAt,
    String sentiment,
    Double confidence,
    String summary,
    boolean highConfidence
) {
    public SignalResponse(
        Long id,
        String title,
        String url,
        String source,
        String requestTicker,
        OffsetDateTime publishedAt,
        String sentiment,
        Double confidence,
        String summary
    ) {
        this(
            id,
            title,
            url,
            source,
            requestTicker,
            publishedAt,
            sentiment,
            confidence,
            summary,
            confidence != null && confidence >= 0.8
        );
    }
}
