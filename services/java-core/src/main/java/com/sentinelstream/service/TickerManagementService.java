package com.sentinelstream.service;

import com.sentinelstream.dto.TickerManagementItemResponse;
import com.sentinelstream.dto.TickerManagementResponse;

public interface TickerManagementService {
    TickerManagementResponse getTickers();

    TickerManagementItemResponse upsertTicker(String symbol, String name, String exchange);

    boolean deleteTicker(String symbol);
}
