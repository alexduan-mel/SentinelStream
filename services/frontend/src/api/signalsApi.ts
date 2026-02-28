import { apiRequest } from "./apiClient";
import type { Signal } from "../types";
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

const formatTime = (value: string) => {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "--";
  }
  return date.toLocaleTimeString("en-US", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: true
  });
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

export async function listSignals(): Promise<Signal[]> {
  if (shouldMock) {
    return mockSignals;
  }
  const data = await apiRequest<BackendSignalResponse[]>("/api/signals");
  return data.map(mapSignal);
}

export async function getSignal(id: string): Promise<Signal> {
  if (shouldMock) {
    const signal = mockSignals.find((item) => item.id === id);
    if (!signal) {
      throw new Error("Signal not found");
    }
    return signal;
  }
  const item = await apiRequest<BackendSignalResponse>(`/api/signals/${id}`);
  return mapSignal(item);
}
