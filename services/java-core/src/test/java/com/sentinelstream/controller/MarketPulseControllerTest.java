package com.sentinelstream.controller;

import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import java.time.OffsetDateTime;
import java.util.List;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.test.web.servlet.MockMvc;

import com.sentinelstream.dto.MarketPulseEvidenceResponse;
import com.sentinelstream.dto.MarketPulseOverviewCardResponse;
import com.sentinelstream.dto.MarketPulseOverviewResponse;
import com.sentinelstream.dto.MarketPulseTopicCardResponse;
import com.sentinelstream.dto.MarketPulseTopicDetailResponse;
import com.sentinelstream.service.MarketPulseService;

@WebMvcTest(MarketPulseController.class)
class MarketPulseControllerTest {
    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private MarketPulseService marketPulseService;

    @Test
    void overviewResponseShape() throws Exception {
        MarketPulseOverviewResponse overview = new MarketPulseOverviewResponse(
            2,
            1,
            1,
            List.of(
                new MarketPulseOverviewCardResponse(
                    1L,
                    "memory_pricing",
                    "Memory pricing",
                    "new",
                    0.7,
                    "Prices stabilized",
                    List.of("MU", "WDC"),
                    3,
                    OffsetDateTime.parse("2026-03-08T12:00:00Z")
                )
            )
        );
        when(marketPulseService.getOverview(5)).thenReturn(overview);

        mockMvc.perform(get("/api/market-pulse/overview"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.active_theme_count").value(2))
            .andExpect(jsonPath("$.new_theme_count").value(1))
            .andExpect(jsonPath("$.strengthening_theme_count").value(1))
            .andExpect(jsonPath("$.top_cards[0].topic_key").value("memory_pricing"))
            .andExpect(jsonPath("$.top_cards[0].affected_assets[0]").value("MU"));
    }

    @Test
    void topicsResponseShape() throws Exception {
        List<MarketPulseTopicCardResponse> topics = List.of(
            new MarketPulseTopicCardResponse(
                1L,
                "memory_pricing",
                "Memory pricing",
                "sector",
                "neutral",
                "ongoing",
                0.6,
                "Prices stabilized",
                List.of("MU"),
                2,
                OffsetDateTime.parse("2026-03-08T12:00:00Z")
            )
        );
        when(marketPulseService.listTopics()).thenReturn(topics);

        mockMvc.perform(get("/api/market-pulse/topics"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$[0].topic_key").value("memory_pricing"))
            .andExpect(jsonPath("$[0].topic_type").value("sector"))
            .andExpect(jsonPath("$[0].affected_assets[0]").value("MU"));
    }

    @Test
    void topicDetailResponseShape() throws Exception {
        MarketPulseTopicDetailResponse detail = new MarketPulseTopicDetailResponse(
            1L,
            "memory_pricing",
            "Memory pricing",
            "sector",
            "neutral",
            "ongoing",
            0.6,
            "Prices stabilized",
            List.of("MU"),
            2,
            OffsetDateTime.parse("2026-03-07T12:00:00Z"),
            OffsetDateTime.parse("2026-03-08T12:00:00Z"),
            List.of(
                new MarketPulseEvidenceResponse(
                    101L,
                    "Headline",
                    "Reuters",
                    OffsetDateTime.parse("2026-03-08T11:00:00Z"),
                    "https://example.com"
                )
            )
        );
        when(marketPulseService.getTopicDetail(1L)).thenReturn(detail);

        mockMvc.perform(get("/api/market-pulse/topics/1"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.topic_key").value("memory_pricing"))
            .andExpect(jsonPath("$.affected_assets[0]").value("MU"))
            .andExpect(jsonPath("$.evidence[0].news_event_id").value(101));
    }
}
