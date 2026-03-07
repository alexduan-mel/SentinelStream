package com.sentinelstream.entity;

import java.util.UUID;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

@Entity
@Table(name = "llm_analyses")
public class LlmAnalysisEntity {
    @Id
    @Column(name = "analysis_uuid")
    private UUID analysisUuid;

    @Column(name = "news_event_id", nullable = false)
    private Long newsEventId;

    private String sentiment;

    private Double confidence;

    private String summary;

    @Column(nullable = false)
    private String status;

    protected LlmAnalysisEntity() {
    }

    public UUID getAnalysisUuid() {
        return analysisUuid;
    }

    public Long getNewsEventId() {
        return newsEventId;
    }

    public String getSentiment() {
        return sentiment;
    }

    public Double getConfidence() {
        return confidence;
    }

    public String getSummary() {
        return summary;
    }

    public String getStatus() {
        return status;
    }
}
