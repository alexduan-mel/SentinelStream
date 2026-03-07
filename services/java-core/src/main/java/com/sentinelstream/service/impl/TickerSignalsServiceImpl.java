package com.sentinelstream.service.impl;

import java.util.List;

import org.springframework.stereotype.Service;

import com.sentinelstream.dto.SignalItemResponse;
import com.sentinelstream.dto.TickerSignalsResponse;
import com.sentinelstream.repository.TickerSignalsRepository;
import com.sentinelstream.service.TickerSignalsService;

@Service
public class TickerSignalsServiceImpl implements TickerSignalsService {
    private static final int DEFAULT_LIMIT = 50;
    private static final int MAX_LIMIT = 200;

    private final TickerSignalsRepository tickerSignalsRepository;

    public TickerSignalsServiceImpl(TickerSignalsRepository tickerSignalsRepository) {
        this.tickerSignalsRepository = tickerSignalsRepository;
    }

    @Override
    public TickerSignalsResponse getTickerSignals(
        String symbol,
        int limit,
        int offset,
        boolean includeRaw
    ) {
        int resolvedLimit = limit > 0 ? Math.min(limit, MAX_LIMIT) : DEFAULT_LIMIT;
        int resolvedOffset = Math.max(0, offset);
        List<SignalItemResponse> items = tickerSignalsRepository.fetchSignals(
            symbol,
            resolvedLimit,
            resolvedOffset,
            includeRaw
        );
        SignalItemResponse latest = tickerSignalsRepository.fetchLatest(symbol, includeRaw);
        long total = tickerSignalsRepository.countSignals(symbol);
        return new TickerSignalsResponse(symbol, latest, items, resolvedLimit, resolvedOffset, total);
    }
}
