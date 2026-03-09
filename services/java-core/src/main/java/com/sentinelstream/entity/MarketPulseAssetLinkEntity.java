package com.sentinelstream.entity;

import java.time.OffsetDateTime;
import java.util.UUID;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

@Entity
@Table(name = "market_pulse_asset_links")
public class MarketPulseAssetLinkEntity {
    @Id
    private Long id;

    @Column(name = "asset_link_uuid", nullable = false)
    private UUID assetLinkUuid;

    @Column(name = "topic_id")
    private Long topicId;

    @Column(name = "asset_symbol")
    private String assetSymbol;

    @Column(name = "asset_type")
    private String assetType;

    @Column(name = "relation_type")
    private String relationType;

    @Column(name = "confidence_score")
    private Double confidenceScore;

    @Column(name = "mention_count")
    private Integer mentionCount;

    @Column(name = "first_seen_at")
    private OffsetDateTime firstSeenAt;

    @Column(name = "last_seen_at")
    private OffsetDateTime lastSeenAt;

    @Column(name = "created_at")
    private OffsetDateTime createdAt;

    @Column(name = "updated_at")
    private OffsetDateTime updatedAt;

    protected MarketPulseAssetLinkEntity() {
    }

    public Long getId() {
        return id;
    }

    public UUID getAssetLinkUuid() {
        return assetLinkUuid;
    }

    public Long getTopicId() {
        return topicId;
    }

    public String getAssetSymbol() {
        return assetSymbol;
    }

    public String getAssetType() {
        return assetType;
    }

    public String getRelationType() {
        return relationType;
    }

    public Double getConfidenceScore() {
        return confidenceScore;
    }

    public Integer getMentionCount() {
        return mentionCount;
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
