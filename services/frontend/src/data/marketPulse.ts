import type { MarketNarrative } from "../types/marketPulse";

export const marketNarratives: MarketNarrative[] = [
  {
    id: "mp-001",
    title: "AI Infrastructure Capex Surge",
    summary:
      "Hyperscalers signal sustained GPU buildouts as supply tightens, lifting long-cycle infrastructure demand.",
    direction: "bullish",
    status: "Developing",
    assetClass: "Equity",
    signalStrength: 94,
    momentum: 12,
    sourceCount: 47,
    sourceDelta: 9,
    affectedAssets: ["NVDA", "AMD", "AVGO", "TSM", "SMCI"],
    lastUpdatedLabel: "01:00 AM",
    ageLabel: "3h"
  },
  {
    id: "mp-002",
    title: "EV Demand Plateau in Europe",
    summary:
      "Pricing pressure and subsidy rollbacks temper near-term demand growth across mass-market EV models.",
    direction: "bearish",
    status: "Confirmed",
    assetClass: "Equity",
    signalStrength: 82,
    momentum: -8,
    sourceCount: 39,
    sourceDelta: 5,
    affectedAssets: ["TSLA", "VWAGY", "STLA", "RIVN"],
    lastUpdatedLabel: "12:35 AM",
    ageLabel: "5h"
  },
  {
    id: "mp-003",
    title: "Crypto Regulatory Crackdown",
    summary:
      "Regulators tighten exchange oversight and stablecoin disclosures, raising compliance costs and volatility.",
    direction: "bearish",
    status: "Emerging",
    assetClass: "Crypto",
    signalStrength: 76,
    momentum: 6,
    sourceCount: 21,
    sourceDelta: 4,
    affectedAssets: ["BTC", "ETH", "COIN"],
    lastUpdatedLabel: "11:20 PM",
    ageLabel: "6h"
  },
  {
    id: "mp-004",
    title: "US Regional Banking Stress",
    summary:
      "Deposit beta and CRE exposure keep funding costs elevated despite easing rate expectations.",
    direction: "bearish",
    status: "Developing",
    assetClass: "Equity",
    signalStrength: 88,
    momentum: -5,
    sourceCount: 33,
    sourceDelta: 7,
    affectedAssets: ["KRE", "WAL", "ZION", "FHN"],
    lastUpdatedLabel: "10:10 PM",
    ageLabel: "7h"
  },
  {
    id: "mp-005",
    title: "OPEC Supply Discipline",
    summary:
      "Quota adherence and export monitoring tighten near-term balances, supporting crude pricing resilience.",
    direction: "bullish",
    status: "Confirmed",
    assetClass: "Commodity",
    signalStrength: 79,
    momentum: 4,
    sourceCount: 28,
    sourceDelta: 2,
    affectedAssets: ["CL", "XOM", "CVX", "SHEL"],
    lastUpdatedLabel: "09:45 PM",
    ageLabel: "8h"
  },
  {
    id: "mp-006",
    title: "China Growth Stabilization Hopes",
    summary:
      "Targeted credit easing and property support underpin tentative stabilization signals in PMI data.",
    direction: "neutral",
    status: "Fading",
    assetClass: "Macro",
    signalStrength: 58,
    momentum: 0,
    sourceCount: 17,
    sourceDelta: -3,
    affectedAssets: ["FXI", "EEM", "HG", "CNY"],
    lastUpdatedLabel: "08:10 PM",
    ageLabel: "10h"
  }
];
