package com.sentinelstream.controller;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.server.ResponseStatusException;

import com.sentinelstream.dto.TickerManagementItemResponse;
import com.sentinelstream.dto.TickerManagementResponse;
import com.sentinelstream.dto.TickerUpsertRequest;
import com.sentinelstream.service.TickerManagementService;

import static org.springframework.http.HttpStatus.BAD_REQUEST;
import static org.springframework.http.HttpStatus.NOT_FOUND;

@RestController
@RequestMapping("/api/tickers")
public class TickerManagementController {
    private final TickerManagementService tickerManagementService;

    public TickerManagementController(TickerManagementService tickerManagementService) {
        this.tickerManagementService = tickerManagementService;
    }

    @GetMapping
    public ResponseEntity<TickerManagementResponse> getTickers() {
        return ResponseEntity.ok(tickerManagementService.getTickers());
    }

    @PostMapping
    public ResponseEntity<TickerManagementItemResponse> upsertTicker(@RequestBody TickerUpsertRequest request) {
        if (request == null || request.symbol() == null || request.symbol().trim().isEmpty()) {
            throw new ResponseStatusException(BAD_REQUEST, "ticker_symbol_required");
        }
        String symbol = request.symbol().trim().toUpperCase();
        if (!symbol.matches("^[A-Z0-9._-]{1,16}$")) {
            throw new ResponseStatusException(BAD_REQUEST, "ticker_symbol_invalid");
        }
        String name = request.name() == null ? "" : request.name().trim();
        String exchange = request.exchange() == null ? "" : request.exchange().trim().toUpperCase();
        TickerManagementItemResponse saved = tickerManagementService.upsertTicker(symbol, name, exchange);
        return ResponseEntity.ok(saved);
    }

    @DeleteMapping("/{symbol}")
    public ResponseEntity<Void> deleteTicker(@PathVariable("symbol") String symbol) {
        String normalized = symbol == null ? "" : symbol.trim().toUpperCase();
        if (normalized.isEmpty()) {
            throw new ResponseStatusException(BAD_REQUEST, "ticker_symbol_required");
        }
        if (!tickerManagementService.deleteTicker(normalized)) {
            throw new ResponseStatusException(NOT_FOUND, "ticker_not_found");
        }
        return ResponseEntity.noContent().build();
    }
}
