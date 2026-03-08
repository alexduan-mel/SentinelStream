package com.sentinelstream.entity;

import java.time.OffsetDateTime;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

@Entity
@Table(name = "market_pulse_asset_links")
public class MarketPulseAssetLinkEntity {
    @Id
    private Long id;

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

    @Column(name = "created_at")
    private OffsetDateTime createdAt;

    protected MarketPulseAssetLinkEntity() {
    }

    public Long getId() {
        return id;
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

    public OffsetDateTime getCreatedAt() {
        return createdAt;
    }
}
