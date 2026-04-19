package com.sentinelstream.entity;

import java.time.OffsetDateTime;
import java.util.UUID;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

@Entity
@Table(name = "market_pulse_topic_mentions")
public class MarketPulseTopicMentionEntity {
    @Id
    private Long id;

    @Column(name = "mention_uuid", nullable = false)
    private UUID mentionUuid;

    @Column(name = "topic_id")
    private Long topicId;

    @Column(name = "news_event_id")
    private Long newsEventId;

    @Column(name = "llm_analysis_id")
    private Long llmAnalysisId;

    @Column(name = "topic_family")
    private String topicFamily;

    @Column(name = "sector")
    private String sector;

    @Column(name = "subtopic")
    private String subtopic;

    @Column(name = "subtopic_label")
    private String subtopicLabel;

    @Column(name = "relevance_score")
    private Double relevanceScore;

    @Column(name = "similarity_score")
    private Double similarityScore;

    @Column(name = "reasoning_summary")
    private String reasoningSummary;

    @Column(name = "assigned_at")
    private OffsetDateTime assignedAt;

    @Column(name = "created_at")
    private OffsetDateTime createdAt;

    protected MarketPulseTopicMentionEntity() {
    }

    public Long getId() {
        return id;
    }

    public UUID getMentionUuid() {
        return mentionUuid;
    }

    public Long getTopicId() {
        return topicId;
    }

    public Long getNewsEventId() {
        return newsEventId;
    }

    public Long getLlmAnalysisId() {
        return llmAnalysisId;
    }

    public String getTopicFamily() {
        return topicFamily;
    }

    public String getSector() {
        return sector;
    }

    public String getSubtopic() {
        return subtopic;
    }

    public String getSubtopicLabel() {
        return subtopicLabel;
    }

    public Double getRelevanceScore() {
        return relevanceScore;
    }

    public Double getSimilarityScore() {
        return similarityScore;
    }

    public String getReasoningSummary() {
        return reasoningSummary;
    }

    public OffsetDateTime getAssignedAt() {
        return assignedAt;
    }

    public OffsetDateTime getCreatedAt() {
        return createdAt;
    }
}
