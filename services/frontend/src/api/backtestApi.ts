import { apiRequest } from "./apiClient";
import type { BacktestRun } from "../types";

const shouldMock = import.meta.env.VITE_API_MOCK === "true";

const mockBacktests: BacktestRun[] = [
  {
    id: "bt-001",
    strategy: "signal-alpha",
    totalReturn: 23.4,
    sharpeRatio: 1.87,
    maxDrawdown: -8.3,
    winRate: 68,
    ruleContribution: [
      { label: "Multi-source confirmation", accuracy: 78, frequency: 92 },
      { label: "Volume confirmation", accuracy: 71, frequency: 68 },
      { label: "Model consensus", accuracy: 82, frequency: 87 },
      { label: "Historical accuracy", accuracy: 75, frequency: 81 }
    ],
    attribution: [
      { label: "NVDA", value: 8.2 },
      { label: "TSLA", value: -2.1 },
      { label: "AAPL", value: 5.7 }
    ],
    falseAnalysis: {
      falsePositives: 12,
      falseNegatives: 8,
      totalErrors: 20
    }
  }
];

export async function listBacktests(): Promise<BacktestRun[]> {
  if (shouldMock) {
    return mockBacktests;
  }
  return apiRequest<BacktestRun[]>("/api/backtests");
}
