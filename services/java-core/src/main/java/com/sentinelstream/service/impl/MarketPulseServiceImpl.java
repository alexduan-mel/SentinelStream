package com.sentinelstream.service.impl;

import java.util.List;

import org.springframework.stereotype.Service;

import com.sentinelstream.dto.MarketPulseOverviewResponse;
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
}
