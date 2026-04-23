package com.sentinelstream.service.impl;

import java.util.List;

import org.springframework.stereotype.Service;

import com.sentinelstream.dto.TickerManagementItemResponse;
import com.sentinelstream.dto.TickerManagementResponse;
import com.sentinelstream.dto.TickerManagementSummaryResponse;
import com.sentinelstream.repository.TickerManagementRepository;
import com.sentinelstream.service.TickerManagementService;

@Service
public class TickerManagementServiceImpl implements TickerManagementService {
    private final TickerManagementRepository tickerManagementRepository;

    public TickerManagementServiceImpl(TickerManagementRepository tickerManagementRepository) {
        this.tickerManagementRepository = tickerManagementRepository;
    }

    @Override
    public TickerManagementResponse getTickers() {
        List<TickerManagementItemResponse> items = tickerManagementRepository.fetchTickerItems();
        int total = items.size();
        int active = 0;
        int paused = 0;
        int errors = 0;
        for (TickerManagementItemResponse item : items) {
            String status = item.status() == null ? "" : item.status().trim().toLowerCase();
            if ("error".equals(status)) {
                errors += 1;
            } else if ("paused".equals(status)) {
                paused += 1;
            } else {
                active += 1;
            }
        }
        TickerManagementSummaryResponse summary = new TickerManagementSummaryResponse(total, active, paused, errors);
        return new TickerManagementResponse(summary, items);
    }

    @Override
    public TickerManagementItemResponse upsertTicker(String symbol, String name, String exchange) {
        return tickerManagementRepository.upsertTicker(symbol, name, exchange);
    }

    @Override
    public boolean deleteTicker(String symbol) {
        return tickerManagementRepository.deleteTicker(symbol) > 0;
    }
}
