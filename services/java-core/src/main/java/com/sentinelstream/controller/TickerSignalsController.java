package com.sentinelstream.controller;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.sentinelstream.dto.TickerSignalsResponse;
import com.sentinelstream.service.TickerSignalsService;

@RestController
@RequestMapping("/api/tickers")
public class TickerSignalsController {
    private final TickerSignalsService tickerSignalsService;

    public TickerSignalsController(TickerSignalsService tickerSignalsService) {
        this.tickerSignalsService = tickerSignalsService;
    }

    @GetMapping("/{symbol}/signals")
    public ResponseEntity<TickerSignalsResponse> getTickerSignals(
        @PathVariable("symbol") String symbol,
        @RequestParam(name = "limit", defaultValue = "50") int limit,
        @RequestParam(name = "offset", defaultValue = "0") int offset,
        @RequestParam(name = "includeRaw", defaultValue = "false") boolean includeRaw
    ) {
        return ResponseEntity.ok(tickerSignalsService.getTickerSignals(symbol, limit, offset, includeRaw));
    }
}
