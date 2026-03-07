import { apiRequest } from "./apiClient";
import type { IngestionRun, SystemSnapshot } from "../types";

const shouldMock = import.meta.env.VITE_API_MOCK === "true";

const mockRuns: IngestionRun[] = [
  {
    id: "run-101",
    startedAt: "2026-02-21T21:28:00Z",
    status: "succeeded",
    fetchedCount: 248,
    insertedCount: 128,
    dedupedCount: 120,
    durationSeconds: 18,
    metrics: {
      ingestionLatencySec: 1.2,
      modelAgreementPct: 84,
      rulePassRatePct: 76
    }
  },
  {
    id: "run-102",
    startedAt: "2026-02-21T21:24:30Z",
    status: "succeeded",
    fetchedCount: 156,
    insertedCount: 98,
    dedupedCount: 58,
    durationSeconds: 21
  },
  {
    id: "run-103",
    startedAt: "2026-02-21T21:20:10Z",
    status: "running",
    fetchedCount: 92,
    insertedCount: 0,
    dedupedCount: 0,
    durationSeconds: 8
  }
];

const mockSnapshot: SystemSnapshot = {
  metrics: [
    { label: "Ingestion Runs", value: "847", meta: "All-time executions", tone: "info" },
    { label: "Scheduler Uptime", value: "99.87%", meta: "Last 30 days", tone: "positive" },
    { label: "LLM Calls/Hour", value: "342", meta: "Current rate", tone: "info" },
    { label: "Avg Latency", value: "1.2s", meta: "End-to-end processing", tone: "info" },
    { label: "Error Rate", value: "2.00%", meta: "Last hour", tone: "warning" },
    { label: "System Uptime", value: "99.94%", meta: "Current month", tone: "positive" }
  ],
  operations: [
    {
      title: "Market pulse ingestion cycle completed",
      time: "09:28:00 PM",
      details: ["articlesProcessed: 248", "topicsCreated: 12", "duration: 18s"],
      status: "Ingestion",
      tone: "positive"
    },
    {
      title: "Running LLM inference on 12 pending signals",
      time: "09:27:15 PM",
      details: ["processed: 8", "remaining: 4"],
      status: "Model",
      tone: "info"
    },
    {
      title: "Watchlist news pipeline completed",
      time: "09:24:30 PM",
      details: ["articlesProcessed: 156", "signalsGenerated: 9", "duration: 21s"],
      status: "Ingestion",
      tone: "positive"
    }
  ],
  pipelineStatus: [
    { label: "Watchlist Ingestion", value: "Active", tone: "positive" },
    { label: "Market Pulse Ingestion", value: "Active", tone: "positive" },
    { label: "LLM Analysis Engine", value: "Processing", tone: "info" },
    { label: "Rule Validator", value: "Ready", tone: "positive" },
    { label: "Signal Publisher", value: "Ready", tone: "positive" }
  ],
  dbHealth: [
    { label: "Connection Pool", value: "32/50" },
    { label: "Query Latency (p95)", value: "84ms" },
    { label: "Replication Lag", value: "<1ms" },
    { label: "Storage Used", value: "12.4GB / 100GB" }
  ],
  ingestionRuns: mockRuns
};

export async function listIngestionRuns(): Promise<IngestionRun[]> {
  if (shouldMock) {
    return mockRuns;
  }
  return apiRequest<IngestionRun[]>("/api/system/ingestion-runs");
}

export async function getSystemSnapshot(): Promise<SystemSnapshot> {
  if (shouldMock) {
    return mockSnapshot;
  }
  const ingestionRuns = await listIngestionRuns();
  return {
    metrics: [],
    operations: [],
    pipelineStatus: [],
    dbHealth: [],
    ingestionRuns
  };
}
