import type { MarketNarrativeQuery, RawNarrative } from "./types";

const hoursAgo = (hours: number) => new Date(Date.now() - hours * 60 * 60 * 1000).toISOString();
const daysAgo = (days: number) => new Date(Date.now() - days * 24 * 60 * 60 * 1000).toISOString();

const baseMockNarratives = (): RawNarrative[] => [
  {
    id: "mp-001",
    title: "AI Infrastructure Capex Surge",
    summary:
      "Hyperscalers signal sustained GPU buildouts as supply tightens, lifting long-cycle infrastructure demand.",
    direction: "bullish",
    status: "developing",
    asset_class: "equity",
    signal_strength: 94,
    momentum: 12,
    source_count: 47,
    source_delta: 9,
    affected_assets: ["NVDA", "AMD", "AVGO", "TSM", "SMCI"],
    last_updated_at: hoursAgo(3),
    first_seen_at: hoursAgo(9)
  },
  {
    id: "mp-002",
    title: "EV Demand Plateau in Europe",
    summary:
      "Pricing pressure and subsidy rollbacks temper near-term demand growth across mass-market EV models.",
    direction: "bearish",
    status: "confirmed",
    asset_class: "equity",
    signal_strength: 82,
    momentum: -8,
    source_count: 39,
    source_delta: 5,
    affected_assets: ["TSLA", "VWAGY", "STLA", "RIVN"],
    last_updated_at: hoursAgo(5),
    first_seen_at: daysAgo(1)
  },
  {
    id: "mp-003",
    title: "Crypto Regulatory Crackdown",
    summary:
      "Regulators tighten exchange oversight and stablecoin disclosures, raising compliance costs and volatility.",
    direction: "bearish",
    status: "emerging",
    asset_class: "crypto",
    signal_strength: 76,
    momentum: 6,
    source_count: 21,
    source_delta: 4,
    affected_assets: ["BTC", "ETH", "COIN"],
    last_updated_at: hoursAgo(6),
    first_seen_at: daysAgo(2)
  },
  {
    id: "mp-004",
    title: "US Regional Banking Stress",
    summary:
      "Deposit beta and CRE exposure keep funding costs elevated despite easing rate expectations.",
    direction: "bearish",
    status: "developing",
    asset_class: "equity",
    signal_strength: 88,
    momentum: -5,
    source_count: 33,
    source_delta: 7,
    affected_assets: ["KRE", "WAL", "ZION", "FHN"],
    last_updated_at: hoursAgo(7),
    first_seen_at: daysAgo(3)
  },
  {
    id: "mp-005",
    title: "OPEC Supply Discipline",
    summary:
      "Quota adherence and export monitoring tighten near-term balances, supporting crude pricing resilience.",
    direction: "bullish",
    status: "confirmed",
    asset_class: "commodity",
    signal_strength: 79,
    momentum: 4,
    source_count: 28,
    source_delta: 2,
    affected_assets: ["CL", "XOM", "CVX", "SHEL"],
    last_updated_at: hoursAgo(8),
    first_seen_at: daysAgo(4)
  },
  {
    id: "mp-006",
    title: "China Growth Stabilization Hopes",
    summary:
      "Targeted credit easing and property support underpin tentative stabilization signals in PMI data.",
    direction: "neutral",
    status: "fading",
    asset_class: "macro",
    signal_strength: 58,
    momentum: 0,
    source_count: 17,
    source_delta: -3,
    affected_assets: ["FXI", "EEM", "HG", "CNY"],
    last_updated_at: hoursAgo(10),
    first_seen_at: daysAgo(5)
  }
];

const applyRangeFilter = (items: RawNarrative[], range?: MarketNarrativeQuery["range"]) => {
  if (!range) return items;
  const now = Date.now();
  const cutoffMs = range === "24h" ? 24 * 60 * 60 * 1000 : range === "7d" ? 7 * 24 * 60 * 60 * 1000 : 30 * 24 * 60 * 60 * 1000;
  return items.filter((item) => {
    const ts = new Date(item.last_updated_at).getTime();
    return Number.isFinite(ts) ? now - ts <= cutoffMs : true;
  });
};

const applyAssetFilter = (items: RawNarrative[], assetClass?: MarketNarrativeQuery["assetClass"]) => {
  if (!assetClass || assetClass === "all") return items;
  return items.filter((item) => item.asset_class === assetClass);
};

const applySort = (items: RawNarrative[], sort?: MarketNarrativeQuery["sort"]) => {
  const sorted = [...items];
  if (sort === "momentum") {
    return sorted.sort((a, b) => b.momentum - a.momentum);
  }
  if (sort === "recent") {
    return sorted.sort((a, b) => new Date(b.last_updated_at).getTime() - new Date(a.last_updated_at).getTime());
  }
  return sorted.sort((a, b) => b.signal_strength - a.signal_strength);
};

export const getMockNarratives = (query: MarketNarrativeQuery = {}) => {
  const base = baseMockNarratives();
  const filtered = applyAssetFilter(applyRangeFilter(base, query.range), query.assetClass);
  return applySort(filtered, query.sort);
};
