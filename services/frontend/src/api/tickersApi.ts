import { apiRequest } from "./apiClient";
import type { AnalysisResult, TickerSignalsResponse, TickerSignalItem } from "../types";
import { normalizeSentiment } from "../utils/sentiment";

interface BackendAnalysis {
  provider: string;
  model: string;
  sentiment: string | null;
  confidence: number | null;
  summary: string | null;
  createdAt: string;
}

interface BackendSignalItem {
  analysisId: string;
  ticker: string;
  publishedAt: string;
  news: {
    title: string;
    url: string;
    publisher: string | null;
  };
  signalConfidence?: number | null;
  analyses?: BackendAnalysis[];
  sentiment?: string | null;
  confidence?: number | null;
  summary?: string | null;
}

interface BackendTickerSignalsResponse {
  ticker: string;
  latest: BackendSignalItem | null;
  items: BackendSignalItem[];
  limit: number;
  offset: number;
  total: number;
}

const shouldMock = import.meta.env.VITE_API_MOCK === "true";

const mockItem: TickerSignalItem = {
  analysisId: "sig-001",
  ticker: "NVDA",
  publishedAt: "2026-02-21T12:33:15Z",
  news: {
    title: "NVIDIA receives upgraded price target from major investment banks",
    url: "https://example.com",
    publisher: "Reuters"
  },
  signalConfidence: 0.87,
  analyses: [
    {
      provider: "OpenAI",
      model: "GPT-4",
      sentiment: "positive",
      confidence: 0.87,
      summary: "Strong institutional buying and pricing power support a bullish outlook.",
      createdAt: "2026-02-21T12:34:00Z"
    }
  ]
};

const mockResponse: TickerSignalsResponse = {
  ticker: "NVDA",
  latest: mockItem,
  items: [
    mockItem,
    {
      ...mockItem,
      analysisId: "sig-002",
      signalConfidence: 0.84,
      analyses: [
        {
          provider: "OpenAI",
          model: "GPT-4",
          sentiment: "positive",
          confidence: 0.84,
          summary: "Institutional ownership increased by 4.2% in recent filings.",
          createdAt: "2026-02-21T10:45:30Z"
        }
      ],
      publishedAt: "2026-02-21T10:45:00Z",
      news: {
        title: "Institutional ownership increased by 4.2% in recent filings",
        url: "https://example.com/filings",
        publisher: "SEC Filings"
      }
    }
  ],
  limit: 50,
  offset: 0,
  total: 2
};

const mapAnalysis = (analysis: BackendAnalysis): AnalysisResult => ({
  provider: analysis.provider,
  model: analysis.model,
  sentiment: normalizeSentiment(analysis.sentiment),
  confidence: analysis.confidence ?? 0,
  summary: analysis.summary ?? "",
  createdAt: analysis.createdAt
});

const mapSignalItem = (item: BackendSignalItem): TickerSignalItem => {
  const analyses = (item.analyses ?? []).map(mapAnalysis);
  if (analyses.length === 0 && item.sentiment) {
    analyses.push({
      provider: "OpenAI",
      model: "Primary",
      sentiment: normalizeSentiment(item.sentiment),
      confidence: item.confidence ?? 0,
      summary: item.summary ?? "",
      createdAt: item.publishedAt
    });
  }
  const signalConfidence = item.signalConfidence ?? analyses[0]?.confidence ?? 0;
  return {
    analysisId: item.analysisId,
    ticker: item.ticker,
    publishedAt: item.publishedAt,
    news: item.news,
    signalConfidence,
    analyses
  };
};

const mapResponse = (response: BackendTickerSignalsResponse): TickerSignalsResponse => ({
  ticker: response.ticker,
  latest: response.latest ? mapSignalItem(response.latest) : null,
  items: response.items.map(mapSignalItem),
  limit: response.limit,
  offset: response.offset,
  total: response.total
});

export async function getTickerSignals(
  symbol: string,
  options: { limit?: number; offset?: number; includeRaw?: boolean } = {}
): Promise<TickerSignalsResponse> {
  if (shouldMock) {
    return mockResponse;
  }
  const params = new URLSearchParams();
  if (options.limit) {
    params.set("limit", String(options.limit));
  }
  if (options.offset) {
    params.set("offset", String(options.offset));
  }
  if (options.includeRaw) {
    params.set("includeRaw", "true");
  }
  const query = params.toString();
  const path = query ? `/api/tickers/${symbol}/signals?${query}` : `/api/tickers/${symbol}/signals`;
  const data = await apiRequest<BackendTickerSignalsResponse>(path);
  return mapResponse(data);
}
