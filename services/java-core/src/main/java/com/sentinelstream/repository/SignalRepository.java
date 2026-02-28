package com.sentinelstream.repository;

import java.util.List;
import java.util.UUID;

import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;

import com.sentinelstream.dto.SignalResponse;
import com.sentinelstream.entity.LlmAnalysisEntity;

public interface SignalRepository extends JpaRepository<LlmAnalysisEntity, UUID> {
    @Query(
        "select new com.sentinelstream.dto.SignalResponse(" +
            "ne.id, ne.title, ne.url, ne.source, ne.requestTicker, ne.publishedAt, " +
            "la.sentiment, la.confidence, la.summary" +
        ") " +
        "from LlmAnalysisEntity la " +
        "join NewsEventEntity ne on ne.id = la.newsEventId " +
        "where la.status = 'succeeded' " +
        "order by ne.publishedAt desc"
    )
    List<SignalResponse> findLatestSignals(Pageable pageable);
}
