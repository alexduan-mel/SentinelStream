package com.sentinelstream.controller;

import java.util.List;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.server.ResponseStatusException;

import com.sentinelstream.dto.MarketPulseOverviewResponse;
import com.sentinelstream.dto.MarketPulseTopicCardResponse;
import com.sentinelstream.dto.MarketPulseTopicDetailResponse;
import com.sentinelstream.service.MarketPulseService;

import static org.springframework.http.HttpStatus.NOT_FOUND;

@RestController
@RequestMapping({"/api/market-pulse", "/market-pulse"})
public class MarketPulseController {
    private final MarketPulseService marketPulseService;

    public MarketPulseController(MarketPulseService marketPulseService) {
        this.marketPulseService = marketPulseService;
    }

    @GetMapping("/overview")
    public ResponseEntity<MarketPulseOverviewResponse> overview(
        @RequestParam(name = "top", defaultValue = "5") int top
    ) {
        return ResponseEntity.ok(marketPulseService.getOverview(top));
    }

    @GetMapping("/topics")
    public ResponseEntity<List<MarketPulseTopicCardResponse>> listTopics() {
        return ResponseEntity.ok(marketPulseService.listTopics());
    }

    @GetMapping("/topics/{id}")
    public ResponseEntity<MarketPulseTopicDetailResponse> getTopicDetail(@PathVariable("id") long id) {
        MarketPulseTopicDetailResponse detail = marketPulseService.getTopicDetail(id);
        if (detail == null) {
            throw new ResponseStatusException(NOT_FOUND, "market_pulse_topic_not_found");
        }
        return ResponseEntity.ok(detail);
    }
}
