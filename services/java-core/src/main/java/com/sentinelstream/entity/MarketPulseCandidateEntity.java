package com.sentinelstream.entity;

import java.time.OffsetDateTime;
import java.util.UUID;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

@Entity
@Table(name = "market_pulse_candidates")
public class MarketPulseCandidateEntity {
    @Id
    private Long id;

    @Column(name = "candidate_uuid", nullable = false)
    private UUID candidateUuid;

    @Column(name = "topic_family", nullable = false)
    private String topicFamily;

    @Column(name = "candidate_key", nullable = false)
    private String candidateKey;

    @Column(name = "candidate_label", nullable = false)
    private String candidateLabel;

    @Column(name = "representative_subtopic")
    private String representativeSubtopic;

    @Column(name = "summary")
    private String summary;

    @Column(name = "status")
    private String status;

    @Column(name = "evidence_count")
    private Integer evidenceCount;

    @Column(name = "avg_relevance_score")
    private Double avgRelevanceScore;

    @Column(name = "centroid_embedding")
    private String centroidEmbedding;

    @Column(name = "first_seen_at")
    private OffsetDateTime firstSeenAt;

    @Column(name = "last_seen_at")
    private OffsetDateTime lastSeenAt;

    @Column(name = "promoted_topic_id")
    private Long promotedTopicId;

    @Column(name = "created_at")
    private OffsetDateTime createdAt;

    @Column(name = "updated_at")
    private OffsetDateTime updatedAt;

    protected MarketPulseCandidateEntity() {
    }

    public Long getId() {
        return id;
    }

    public UUID getCandidateUuid() {
        return candidateUuid;
    }

    public String getTopicFamily() {
        return topicFamily;
    }

    public String getCandidateKey() {
        return candidateKey;
    }

    public String getCandidateLabel() {
        return candidateLabel;
    }

    public String getRepresentativeSubtopic() {
        return representativeSubtopic;
    }

    public String getSummary() {
        return summary;
    }

    public String getStatus() {
        return status;
    }

    public Integer getEvidenceCount() {
        return evidenceCount;
    }

    public Double getAvgRelevanceScore() {
        return avgRelevanceScore;
    }

    public String getCentroidEmbedding() {
        return centroidEmbedding;
    }

    public OffsetDateTime getFirstSeenAt() {
        return firstSeenAt;
    }

    public OffsetDateTime getLastSeenAt() {
        return lastSeenAt;
    }

    public Long getPromotedTopicId() {
        return promotedTopicId;
    }

    public OffsetDateTime getCreatedAt() {
        return createdAt;
    }

    public OffsetDateTime getUpdatedAt() {
        return updatedAt;
    }
}
