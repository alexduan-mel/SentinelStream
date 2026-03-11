export type NarrativeDirection = "bullish" | "bearish" | "neutral";
export type NarrativeStatus = "Emerging" | "Developing" | "Confirmed" | "Fading";
export type AssetClass = "Equity" | "Macro" | "Commodity" | "Crypto";

export interface MarketNarrative {
  id: string;
  title: string;
  summary: string;
  direction: NarrativeDirection;
  status: NarrativeStatus;
  assetClass: AssetClass;
  signalStrength: number;
  momentum: number;
  sourceCount: number;
  sourceDelta?: number;
  affectedAssets: string[];
  lastUpdatedLabel: string;
  ageLabel: string;
}
