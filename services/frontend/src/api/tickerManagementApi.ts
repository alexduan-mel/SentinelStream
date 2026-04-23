import { apiRequest } from "./apiClient";
import type {
  TickerJobStatus,
  TickerManagementItem,
  TickerManagementResponse,
  TickerManagementSummary,
  TickerRowStatus
} from "../types";

interface BackendTickerManagementSummary {
  total_tickers: number;
  active: number;
  paused: number;
  errors: number;
}

interface BackendTickerManagementItem {
  symbol: string;
  name: string | null;
  exchange: string | null;
  status: string | null;
  news_enabled: boolean;
  filings_enabled: boolean;
  job_status: string | null;
  last_sync_at: string | null;
  signal_count: number | null;
}

interface BackendTickerManagementResponse {
  summary: BackendTickerManagementSummary;
  items: BackendTickerManagementItem[];
}

interface TickerUpsertPayload {
  symbol: string;
  name?: string;
  exchange?: string;
}

const normalizeStatus = (value: string | null): TickerRowStatus => {
  const lowered = (value ?? "").toLowerCase();
  if (lowered === "paused") return "paused";
  if (lowered === "error") return "error";
  return "active";
};

const normalizeJobStatus = (value: string | null): TickerJobStatus => {
  const lowered = (value ?? "").toLowerCase();
  if (lowered === "running") return "running";
  if (lowered === "failed") return "failed";
  return "idle";
};

const mapSummary = (summary: BackendTickerManagementSummary): TickerManagementSummary => ({
  totalTickers: summary.total_tickers ?? 0,
  active: summary.active ?? 0,
  paused: summary.paused ?? 0,
  errors: summary.errors ?? 0
});

const mapItem = (item: BackendTickerManagementItem): TickerManagementItem => ({
  symbol: (item.symbol ?? "").toUpperCase(),
  name: (item.name ?? "").trim(),
  exchange: (item.exchange ?? "").trim().toUpperCase(),
  status: normalizeStatus(item.status),
  newsEnabled: Boolean(item.news_enabled),
  filingsEnabled: Boolean(item.filings_enabled),
  jobStatus: normalizeJobStatus(item.job_status),
  lastSyncAt: item.last_sync_at,
  signalCount: typeof item.signal_count === "number" ? item.signal_count : 0
});

export async function getTickerManagement(): Promise<TickerManagementResponse> {
  const data = await apiRequest<BackendTickerManagementResponse>("/api/tickers");
  return {
    summary: mapSummary(data.summary),
    items: (data.items ?? []).map(mapItem)
  };
}

export async function addTicker(payload: TickerUpsertPayload): Promise<TickerManagementItem> {
  const body = {
    symbol: payload.symbol.trim().toUpperCase(),
    name: (payload.name ?? "").trim(),
    exchange: (payload.exchange ?? "").trim().toUpperCase()
  };
  const data = await apiRequest<BackendTickerManagementItem>("/api/tickers", {
    method: "POST",
    body: JSON.stringify(body)
  });
  return mapItem(data);
}

export async function deleteTicker(symbol: string): Promise<void> {
  await apiRequest<void>(`/api/tickers/${encodeURIComponent(symbol.trim().toUpperCase())}`, {
    method: "DELETE"
  });
}
