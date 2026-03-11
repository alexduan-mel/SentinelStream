export type NarrativeDirection = "bullish" | "bearish" | "neutral";
export type NarrativeStatus = "Emerging" | "Developing" | "Confirmed" | "Fading";
export type AssetClass = "Equity" | "Macro" | "Commodity" | "Crypto";

export interface MarketNarrative {
  id: string;
  displayName: string;
  summary: string;
  direction: NarrativeDirection;
  status: NarrativeStatus;
  assetClass: AssetClass;
  sector?: string;
  subtopic?: string;
  signalStrength: number;
  momentum: number;
  sourceCount: number;
  sourceDelta?: number;
  affectedAssets: string[];
  lastUpdatedLabel: string;
  ageLabel: string;
}

export type RawDirection = "bullish" | "bearish" | "neutral";
export type RawStatus = "emerging" | "developing" | "confirmed" | "fading";
export type RawAssetClass = "equity" | "macro" | "commodity" | "crypto";

export interface RawNarrative {
  id: string;
  title: string;
  summary: string;
  direction: RawDirection;
  status: RawStatus;
  asset_class: RawAssetClass;
  sector?: string | null;
  subtopic?: string | null;
  signal_strength: number;
  momentum: number;
  source_count: number;
  source_delta?: number | null;
  affected_assets: string[];
  last_updated_at: string;
  first_seen_at?: string | null;
}

export interface MarketNarrativeQuery {
  range?: "24h" | "7d" | "30d";
  assetClass?: "all" | "equity" | "macro" | "commodity" | "crypto";
  sort?: "strength" | "momentum" | "recent";
}
