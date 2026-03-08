package com.sentinelstream.dto;

import java.time.OffsetDateTime;
import java.util.List;

import com.fasterxml.jackson.annotation.JsonProperty;

public record MarketPulseTopicDetailResponse(
    Long id,
    @JsonProperty("topic_key") String topicKey,
    @JsonProperty("display_name") String displayName,
    @JsonProperty("topic_type") String topicType,
    String direction,
    String status,
    @JsonProperty("intensity_score") Double intensityScore,
    String summary,
    @JsonProperty("affected_assets") List<String> affectedAssets,
    @JsonProperty("evidence_count") Integer evidenceCount,
    @JsonProperty("first_seen_at") OffsetDateTime firstSeenAt,
    @JsonProperty("last_seen_at") OffsetDateTime lastSeenAt,
    List<MarketPulseEvidenceResponse> evidence
) {}
