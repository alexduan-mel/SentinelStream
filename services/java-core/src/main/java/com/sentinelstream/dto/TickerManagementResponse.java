package com.sentinelstream.dto;

import java.util.List;

public record TickerManagementResponse(
    TickerManagementSummaryResponse summary,
    List<TickerManagementItemResponse> items
) {}
