package com.sentinelstream.entity;

import java.time.OffsetDateTime;
import java.util.UUID;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

@Entity
@Table(name = "market_pulse_topics")
public class MarketPulseTopicEntity {
    @Id
    private Long id;

    @Column(name = "topic_uuid", nullable = false)
    private UUID topicUuid;

    @Column(name = "topic_key", nullable = false)
    private String topicKey;

    @Column(name = "display_name", nullable = false)
    private String displayName;

    @Column(name = "topic_family", nullable = false)
    private String topicFamily;

    @Column(name = "sector")
    private String sector;

    @Column(name = "subtopic")
    private String subtopic;

    @Column(name = "topic_type")
    private String topicType;

    @Column(name = "direction")
    private String direction;

    @Column(name = "summary")
    private String summary;

    @Column(name = "status")
    private String status;

    @Column(name = "strength_score")
    private Double strengthScore;

    @Column(name = "novelty_score")
    private Double noveltyScore;

    @Column(name = "confidence_score")
    private Double confidenceScore;

    @Column(name = "evidence_count")
    private Integer evidenceCount;

    @Column(name = "first_seen_at")
    private OffsetDateTime firstSeenAt;

    @Column(name = "last_seen_at")
    private OffsetDateTime lastSeenAt;

    @Column(name = "last_clustered_at")
    private OffsetDateTime lastClusteredAt;

    @Column(name = "created_at")
    private OffsetDateTime createdAt;

    @Column(name = "updated_at")
    private OffsetDateTime updatedAt;

    protected MarketPulseTopicEntity() {
    }

    public Long getId() {
        return id;
    }

    public UUID getTopicUuid() {
        return topicUuid;
    }

    public String getTopicKey() {
        return topicKey;
    }

    public String getDisplayName() {
        return displayName;
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

    public String getTopicType() {
        return topicType;
    }

    public String getDirection() {
        return direction;
    }

    public String getSummary() {
        return summary;
    }

    public String getStatus() {
        return status;
    }

    public Double getStrengthScore() {
        return strengthScore;
    }

    public Double getNoveltyScore() {
        return noveltyScore;
    }

    public Double getConfidenceScore() {
        return confidenceScore;
    }

    public Integer getEvidenceCount() {
        return evidenceCount;
    }

    public OffsetDateTime getFirstSeenAt() {
        return firstSeenAt;
    }

    public OffsetDateTime getLastSeenAt() {
        return lastSeenAt;
    }

    public OffsetDateTime getLastClusteredAt() {
        return lastClusteredAt;
    }

    public OffsetDateTime getCreatedAt() {
        return createdAt;
    }

    public OffsetDateTime getUpdatedAt() {
        return updatedAt;
    }
}
