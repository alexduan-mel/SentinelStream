package com.sentinelstream.entity;

import java.time.OffsetDateTime;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

@Entity
@Table(name = "market_pulse_topic_mentions")
public class MarketPulseTopicMentionEntity {
    @Id
    private Long id;

    @Column(name = "topic_id")
    private Long topicId;

    @Column(name = "news_event_id")
    private Long newsEventId;

    @Column(name = "relevance_score")
    private Double relevanceScore;

    @Column(name = "reasoning_summary")
    private String reasoningSummary;

    @Column(name = "created_at")
    private OffsetDateTime createdAt;

    protected MarketPulseTopicMentionEntity() {
    }

    public Long getId() {
        return id;
    }

    public Long getTopicId() {
        return topicId;
    }

    public Long getNewsEventId() {
        return newsEventId;
    }

    public Double getRelevanceScore() {
        return relevanceScore;
    }

    public String getReasoningSummary() {
        return reasoningSummary;
    }

    public OffsetDateTime getCreatedAt() {
        return createdAt;
    }
}
