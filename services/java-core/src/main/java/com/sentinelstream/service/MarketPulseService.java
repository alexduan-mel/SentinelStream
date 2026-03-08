package com.sentinelstream.service;

import java.util.List;

import com.sentinelstream.dto.MarketPulseOverviewResponse;
import com.sentinelstream.dto.MarketPulseTopicCardResponse;
import com.sentinelstream.dto.MarketPulseTopicDetailResponse;

public interface MarketPulseService {
    MarketPulseOverviewResponse getOverview(int topLimit);

    List<MarketPulseTopicCardResponse> listTopics();

    MarketPulseTopicDetailResponse getTopicDetail(long id);
}
