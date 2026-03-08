package com.sentinelstream.entity;

import java.time.OffsetDateTime;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

@Entity
@Table(name = "market_pulse_topics")
public class MarketPulseTopicEntity {
    @Id
    private Long id;

    @Column(name = "topic_key", nullable = false)
    private String topicKey;

    @Column(name = "display_name")
    private String displayName;

    @Column(name = "topic_type")
    private String topicType;

    @Column(name = "direction")
    private String direction;

    @Column(name = "summary")
    private String summary;

    @Column(name = "intensity_score")
    private Double intensityScore;

    @Column(name = "confidence_score")
    private Double confidenceScore;

    @Column(name = "evidence_count")
    private Integer evidenceCount;

    @Column(name = "status")
    private String status;

    @Column(name = "first_seen_at")
    private OffsetDateTime firstSeenAt;

    @Column(name = "last_seen_at")
    private OffsetDateTime lastSeenAt;

    @Column(name = "created_at")
    private OffsetDateTime createdAt;

    @Column(name = "updated_at")
    private OffsetDateTime updatedAt;

    protected MarketPulseTopicEntity() {
    }

    public Long getId() {
        return id;
    }

    public String getTopicKey() {
        return topicKey;
    }

    public String getDisplayName() {
        return displayName;
    }

    public String getTopicType() {
        return topicType;
    }

    public String getDirection() {
        return direction;
    }

    public String getSummary() {
        return summary;
    }

    public Double getIntensityScore() {
        return intensityScore;
    }

    public Double getConfidenceScore() {
        return confidenceScore;
    }

    public Integer getEvidenceCount() {
        return evidenceCount;
    }

    public String getStatus() {
        return status;
    }

    public OffsetDateTime getFirstSeenAt() {
        return firstSeenAt;
    }

    public OffsetDateTime getLastSeenAt() {
        return lastSeenAt;
    }

    public OffsetDateTime getCreatedAt() {
        return createdAt;
    }

    public OffsetDateTime getUpdatedAt() {
        return updatedAt;
    }
}
