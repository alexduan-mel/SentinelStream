package com.sentinelstream.dto;

import java.time.OffsetDateTime;

import com.fasterxml.jackson.annotation.JsonProperty;

public record MarketPulseEvidenceResponse(
    @JsonProperty("news_event_id") Long newsEventId,
    String title,
    String publisher,
    @JsonProperty("published_at") OffsetDateTime publishedAt,
    String url
) {}
