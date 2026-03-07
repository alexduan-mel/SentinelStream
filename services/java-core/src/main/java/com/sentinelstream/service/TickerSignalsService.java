package com.sentinelstream.service;

import com.sentinelstream.dto.TickerSignalsResponse;

public interface TickerSignalsService {
    TickerSignalsResponse getTickerSignals(String symbol, int limit, int offset, boolean includeRaw);
}
