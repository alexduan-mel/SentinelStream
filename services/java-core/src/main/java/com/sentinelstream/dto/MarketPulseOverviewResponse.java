package com.sentinelstream.dto;

import java.util.List;

import com.fasterxml.jackson.annotation.JsonProperty;

public record MarketPulseOverviewResponse(
    @JsonProperty("active_theme_count") int activeThemeCount,
    @JsonProperty("new_theme_count") int newThemeCount,
    @JsonProperty("strengthening_theme_count") int strengtheningThemeCount,
    @JsonProperty("top_cards") List<MarketPulseOverviewCardResponse> topCards
) {}
