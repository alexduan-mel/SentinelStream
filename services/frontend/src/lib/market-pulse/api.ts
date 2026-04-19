import { apiRequest } from "../../api/apiClient";
import { formatAgeLabel, formatLastUpdatedLabel } from "./formatters";
import { getMockNarratives } from "./mock";
import type {
  AssetClass,
  MarketNarrative,
  MarketNarrativeQuery,
  NarrativeDirection,
  NarrativeStatus,
  RawNarrative,
  RawAssetClass,
  RawDirection,
  RawStatus
} from "./types";

const statusMap: Record<RawStatus, NarrativeStatus> = {
  emerging: "Emerging",
  developing: "Developing",
  confirmed: "Confirmed",
  fading: "Fading"
};

const assetClassMap: Record<RawAssetClass, AssetClass> = {
  equity: "Equity",
  macro: "Macro",
  commodity: "Commodity",
  crypto: "Crypto"
};

const allowedDirections: NarrativeDirection[] = ["bullish", "bearish", "neutral"];

const toDirection = (value: RawDirection | string | null | undefined): NarrativeDirection => {
  if (value && allowedDirections.includes(value as NarrativeDirection)) {
    return value as NarrativeDirection;
  }
  return "neutral";
};

const toStatus = (value: RawStatus | string | null | undefined): NarrativeStatus => {
  if (value && value in statusMap) {
    return statusMap[value as RawStatus];
  }
  return "Emerging";
};

const toAssetClass = (value: RawAssetClass | string | null | undefined): AssetClass => {
  if (value && value in assetClassMap) {
    return assetClassMap[value as RawAssetClass];
  }
  return "Macro";
};

const toNumber = (value: unknown, fallback = 0) => {
  if (typeof value === "number" && Number.isFinite(value)) {
    return value;
  }
  return fallback;
};

const toStringArray = (value: unknown): string[] => {
  if (!Array.isArray(value)) return [];
  return value.filter((item) => typeof item === "string" && item.trim()).map((item) => item.trim());
};

const mapRawNarrative = (raw: RawNarrative, index: number, now: Date): MarketNarrative => {
  const lastUpdated = raw.last_updated_at;
  const ageBase = raw.first_seen_at ?? lastUpdated;
  return {
    id: raw.id || `narrative-${index}`,
    displayName: raw.title?.trim() || "Untitled Narrative",
    summary: raw.summary?.trim() || "",
    direction: toDirection(raw.direction),
    status: toStatus(raw.status),
    assetClass: toAssetClass(raw.asset_class),
    sector: raw.sector ? raw.sector.toString().trim() : undefined,
    subtopic: raw.subtopic ? raw.subtopic.toString().trim() : undefined,
    signalStrength: Math.round(toNumber(raw.signal_strength, 0)),
    momentum: Math.round(toNumber(raw.momentum, 0)),
    sourceCount: Math.round(toNumber(raw.source_count, 0)),
    sourceDelta: raw.source_delta ?? undefined,
    affectedAssets: toStringArray(raw.affected_assets),
    lastUpdatedLabel: formatLastUpdatedLabel(lastUpdated),
    ageLabel: formatAgeLabel(ageBase, now)
  };
};

const buildQuery = (query: MarketNarrativeQuery) => {
  const params = new URLSearchParams();
  if (query.range) params.set("range", query.range);
  if (query.assetClass) params.set("assetClass", query.assetClass);
  if (query.sort) params.set("sort", query.sort);
  const suffix = params.toString();
  return suffix ? `?${suffix}` : "";
};

export async function getMarketNarratives(query: MarketNarrativeQuery = {}): Promise<MarketNarrative[]> {
  const now = new Date();
  const path = `/api/market-pulse/narratives${buildQuery(query)}`;
  const allowMockFallback =
    (import.meta.env.VITE_MARKET_PULSE_MOCK ?? "").toLowerCase() === "true";
  try {
    const raw = await apiRequest<RawNarrative[]>(path);
    return raw.map((item, index) => mapRawNarrative(item, index, now));
  } catch (error) {
    if (!allowMockFallback) {
      throw error;
    }
    const fallback = getMockNarratives(query);
    return fallback.map((item, index) => mapRawNarrative(item, index, now));
  }
}
