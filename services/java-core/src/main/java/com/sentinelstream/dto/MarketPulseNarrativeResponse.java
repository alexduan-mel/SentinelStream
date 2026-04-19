package com.sentinelstream.dto;

import java.time.OffsetDateTime;
import java.util.List;

import com.fasterxml.jackson.annotation.JsonProperty;

public record MarketPulseNarrativeResponse(
    Long id,
    String title,
    String summary,
    String direction,
    String status,
    @JsonProperty("asset_class") String assetClass,
    String sector,
    String subtopic,
    @JsonProperty("signal_strength") Double signalStrength,
    Double momentum,
    @JsonProperty("source_count") Integer sourceCount,
    @JsonProperty("source_delta") Integer sourceDelta,
    @JsonProperty("affected_assets") List<String> affectedAssets,
    @JsonProperty("last_updated_at") OffsetDateTime lastUpdatedAt,
    @JsonProperty("first_seen_at") OffsetDateTime firstSeenAt
) {}
