package com.sentinelstream.entity;

import java.time.OffsetDateTime;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

@Entity
@Table(name = "news_events")
public class NewsEventEntity {
    @Id
    private Long id;

    @Column(nullable = false)
    private String title;

    @Column(nullable = false)
    private String url;

    @Column(nullable = false)
    private String source;

    @Column(name = "request_ticker")
    private String requestTicker;

    @Column(name = "published_at", nullable = false)
    private OffsetDateTime publishedAt;

    protected NewsEventEntity() {
    }

    public Long getId() {
        return id;
    }

    public String getTitle() {
        return title;
    }

    public String getUrl() {
        return url;
    }

    public String getSource() {
        return source;
    }

    public String getRequestTicker() {
        return requestTicker;
    }

    public OffsetDateTime getPublishedAt() {
        return publishedAt;
    }
}
