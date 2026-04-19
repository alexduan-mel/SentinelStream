package com.sentinelstream.service.impl;

import java.util.List;
import java.time.OffsetDateTime;
import java.time.ZoneOffset;

import org.springframework.stereotype.Service;

import com.sentinelstream.dto.MarketPulseOverviewResponse;
import com.sentinelstream.dto.MarketPulseNarrativeResponse;
import com.sentinelstream.dto.MarketPulseTopicCardResponse;
import com.sentinelstream.dto.MarketPulseTopicDetailResponse;
import com.sentinelstream.repository.MarketPulseRepository;
import com.sentinelstream.service.MarketPulseService;

@Service
public class MarketPulseServiceImpl implements MarketPulseService {
    private final MarketPulseRepository marketPulseRepository;

    public MarketPulseServiceImpl(MarketPulseRepository marketPulseRepository) {
        this.marketPulseRepository = marketPulseRepository;
    }

    @Override
    public MarketPulseOverviewResponse getOverview(int topLimit) {
        return marketPulseRepository.fetchOverview(topLimit);
    }

    @Override
    public List<MarketPulseTopicCardResponse> listTopics() {
        return marketPulseRepository.fetchTopics();
    }

    @Override
    public MarketPulseTopicDetailResponse getTopicDetail(long id) {
        return marketPulseRepository.fetchTopicDetail(id);
    }

    @Override
    public List<MarketPulseNarrativeResponse> listNarratives(String range, String assetClass, String sort) {
        OffsetDateTime now = OffsetDateTime.now(ZoneOffset.UTC);
        OffsetDateTime since = switch (range) {
            case "24h" -> now.minusHours(24);
            case "30d" -> now.minusDays(30);
            default -> now.minusDays(7);
        };
        return marketPulseRepository.fetchNarratives(since, assetClass, sort);
    }
}
