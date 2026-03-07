import { apiRequest } from "./apiClient";
import type { Signal, SignalDetail, SignalEvidenceItem } from "../types";
import { normalizeSentiment } from "../utils/sentiment";

interface BackendSignalResponse {
  id: number;
  title: string;
  url: string;
  source: string;
  requestTicker?: string | null;
  publishedAt: string;
  sentiment: string | null;
  confidence: number | null;
  summary: string | null;
  highConfidence: boolean;
}

interface BackendEvidenceItemResponse {
  id: number;
  title: string;
  url: string;
  source: string;
  publishedAt: string;
  confidence: number | null;
}

interface BackendSignalDetailResponse {
  analysisId: string;
  ticker: string;
  sentiment: string | null;
  confidence: number | null;
  summary: string | null;
  publishedAt: string;
  title: string;
  url: string;
  source: string;
  evidenceItems: BackendEvidenceItemResponse[];
}

const shouldMock = import.meta.env.VITE_API_MOCK === "true";

const mockSignals: Signal[] = [
  {
    id: "sig-001",
    ticker: "NVDA",
    sentiment: "positive",
    title: "Strong institutional buying detected with positive earnings revision",
    description: "Strong institutional buying detected with positive earnings revision",
    confidence: 0.87,
    timestamp: "09:23 PM",
    tags: ["Equity", "Watchlist"],
    highConfidence: true
  },
  {
    id: "sig-002",
    ticker: "TSLA",
    sentiment: "negative",
    title: "Delivery miss signals demand weakness, margin pressure expected",
    description: "Delivery miss signals demand weakness, margin pressure expected",
    confidence: 0.79,
    timestamp: "08:47 PM",
    tags: ["Equity", "Watchlist"],
    highConfidence: false
  },
  {
    id: "sig-003",
    ticker: "AAPL",
    sentiment: "positive",
    title: "Product launch momentum building, supply chain indicators positive",
    description: "Product launch momentum building, supply chain indicators positive",
    confidence: 0.81,
    timestamp: "07:12 PM",
    tags: ["Equity", "Watchlist"],
    highConfidence: true
  }
];

const mockSignalDetail: SignalDetail = {
  id: "sig-001",
  analysisId: "sig-001",
  ticker: "NVDA",
  sentiment: "positive",
  confidence: 0.87,
  publishedAt: "2026/02/21 12:33:15",
  summary: "Strong institutional buying detected with positive earnings revision",
  evidenceItems: [
    {
      id: "ev-1",
      source: "Reuters",
      headline: "NVIDIA receives upgraded price target from major investment banks",
      timestamp: "2026/02/21 20:15:00",
      confidence: 0.92
    },
    {
      id: "ev-2",
      source: "SEC Filings",
      headline: "Institutional ownership increased by 4.2% in recent filings",
      timestamp: "2026/02/21 19:45:00",
      confidence: 0.88
    }
  ]
};

const pad = (value: number) => String(value).padStart(2, "0");

const formatTime = (value: string) => {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "--";
  }
  return date.toLocaleTimeString("en-US", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false
  });
};

const formatDateTime = (value: string) => {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "--";
  }
  return [
    `${date.getFullYear()}/${pad(date.getMonth() + 1)}/${pad(date.getDate())}`,
    `${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`
  ].join(" ");
};

const mapSignal = (item: BackendSignalResponse): Signal => {
  const confidence = item.confidence ?? 0;
  return {
    id: String(item.id),
    ticker: (item.requestTicker || "").toUpperCase() || "NEWS",
    sentiment: normalizeSentiment(item.sentiment),
    title: item.title,
    description: item.summary || item.title,
    confidence,
    timestamp: formatTime(item.publishedAt),
    tags: ["Equity", "Watchlist"],
    highConfidence: item.highConfidence || confidence >= 0.8
  };
};

const mapEvidenceItem = (item: BackendEvidenceItemResponse): SignalEvidenceItem => {
  return {
    id: String(item.id),
    source: item.source,
    headline: item.title,
    timestamp: formatDateTime(item.publishedAt),
    confidence: item.confidence ?? 0
  };
};

const mapSignalDetail = (item: BackendSignalDetailResponse): SignalDetail => {
  return {
    id: item.analysisId,
    analysisId: item.analysisId,
    ticker: item.ticker,
    sentiment: normalizeSentiment(item.sentiment),
    confidence: item.confidence ?? 0,
    publishedAt: formatDateTime(item.publishedAt),
    summary: item.summary || item.title,
    evidenceItems: (item.evidenceItems || []).map(mapEvidenceItem)
  };
};

const mapDetailToSignal = (detail: SignalDetail): Signal => {
  return {
    id: detail.id,
    ticker: detail.ticker,
    sentiment: detail.sentiment,
    title: detail.summary,
    description: detail.summary,
    confidence: detail.confidence,
    timestamp: detail.publishedAt.split(" ")[1] ?? "--",
    tags: ["Equity", "Watchlist"],
    highConfidence: detail.confidence >= 0.8
  };
};

export async function listSignals(): Promise<Signal[]> {
  if (shouldMock) {
    return mockSignals;
  }
  const data = await apiRequest<BackendSignalResponse[]>("/api/signals");
  return data.map(mapSignal);
}

export async function getSignal(id: string): Promise<Signal> {
  const detail = await getSignalDetail(id);
  return mapDetailToSignal(detail);
}

export async function getSignalDetail(id: string): Promise<SignalDetail> {
  if (shouldMock) {
    return mockSignalDetail;
  }
  const item = await apiRequest<BackendSignalDetailResponse>(`/api/signals/${id}`);
  return mapSignalDetail(item);
}
