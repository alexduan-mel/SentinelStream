import { apiRequest } from "./apiClient";
import type { Topic } from "../types";

const shouldMock = import.meta.env.VITE_API_MOCK === "true";

const mockTopics: Topic[] = [
  {
    id: "topic-001",
    name: "Federal Reserve Rate Policy Shift Signals",
    tags: ["Monetary Policy", "Inflation", "Bond Markets"],
    status: "Confirmed",
    score: 8.7,
    progress: 78,
    sources: "24 sources"
  },
  {
    id: "topic-002",
    name: "AI Infrastructure Spending Surge",
    tags: ["AI Infrastructure", "Datacenter", "Semiconductor"],
    status: "Upgraded",
    score: 9.2,
    progress: 84,
    sources: "31 sources"
  },
  {
    id: "topic-003",
    name: "Emerging Market Currency Volatility",
    tags: ["Currency", "Emerging Markets", "Capital Flows"],
    status: "Emerging",
    score: 7.1,
    progress: 62,
    sources: "18 sources"
  }
];

export async function listTopics(): Promise<Topic[]> {
  if (shouldMock) {
    return mockTopics;
  }
  return apiRequest<Topic[]>("/api/topics");
}
