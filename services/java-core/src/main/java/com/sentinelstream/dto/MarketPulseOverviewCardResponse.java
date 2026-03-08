package com.sentinelstream.dto;

import java.time.OffsetDateTime;
import java.util.List;

import com.fasterxml.jackson.annotation.JsonProperty;

public record MarketPulseOverviewCardResponse(
    Long id,
    @JsonProperty("topic_key") String topicKey,
    @JsonProperty("display_name") String displayName,
    String status,
    @JsonProperty("intensity_score") Double intensityScore,
    String summary,
    @JsonProperty("affected_assets") List<String> affectedAssets,
    @JsonProperty("evidence_count") Integer evidenceCount,
    @JsonProperty("last_seen_at") OffsetDateTime lastSeenAt
) {}
