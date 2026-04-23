import type { Sentiment } from "../utils/sentiment";

export interface Signal {
  id: string;
  ticker: string;
  sentiment: Sentiment;
  title: string;
  description: string;
  confidence: number;
  timestamp: string;
  tags: string[];
  highConfidence?: boolean;
}

export interface SignalEvidenceItem {
  id: string;
  publisher: string;
  headline: string;
  timestamp: string;
  confidence: number;
}

export interface SignalDetail {
  id: string;
  analysisId: string;
  ticker: string;
  sentiment: Sentiment;
  confidence: number;
  publishedAt: string;
  summary: string;
  evidenceItems: SignalEvidenceItem[];
}

export interface NewsSummary {
  title: string;
  url: string;
  publisher: string | null;
}

export interface AnalysisResult {
  provider: string;
  model: string;
  sentiment: Sentiment;
  confidence: number;
  summary: string;
  createdAt: string;
}

export interface TickerSignalItem {
  analysisId: string;
  ticker: string;
  publishedAt: string;
  news: NewsSummary;
  signalConfidence: number;
  analyses: AnalysisResult[];
}

export interface TickerSignalsResponse {
  ticker: string;
  latest: TickerSignalItem | null;
  items: TickerSignalItem[];
  limit: number;
  offset: number;
  total: number;
}

export type TickerRowStatus = "active" | "paused" | "error";
export type TickerJobStatus = "running" | "idle" | "failed";

export interface TickerManagementSummary {
  totalTickers: number;
  active: number;
  paused: number;
  errors: number;
}

export interface TickerManagementItem {
  symbol: string;
  name: string;
  exchange: string;
  status: TickerRowStatus;
  newsEnabled: boolean;
  filingsEnabled: boolean;
  jobStatus: TickerJobStatus;
  lastSyncAt: string | null;
  signalCount: number;
}

export interface TickerManagementResponse {
  summary: TickerManagementSummary;
  items: TickerManagementItem[];
}

export interface Topic {
  id: string;
  name: string;
  tags: string[];
  status: string;
  score: number;
  progress: number;
  sources?: string;
}

export interface IngestionRun {
  id: string;
  startedAt: string;
  status: "running" | "succeeded" | "failed";
  fetchedCount: number;
  insertedCount: number;
  dedupedCount: number;
  durationSeconds?: number;
  metrics?: {
    ingestionLatencySec?: number;
    modelAgreementPct?: number;
    rulePassRatePct?: number;
  };
}

export interface BacktestRun {
  id: string;
  strategy: string;
  totalReturn: number;
  sharpeRatio: number;
  maxDrawdown: number;
  winRate: number;
  ruleContribution: BacktestRule[];
  attribution: BacktestAttribution[];
  falseAnalysis: FalseAnalysis;
}

export interface BacktestRule {
  label: string;
  accuracy: number;
  frequency: number;
}

export interface BacktestAttribution {
  label: string;
  value: number;
}

export interface FalseAnalysis {
  falsePositives: number;
  falseNegatives: number;
  totalErrors: number;
}

export interface SystemMetric {
  label: string;
  value: string;
  meta?: string;
  tone?: "positive" | "negative" | "warning" | "info" | "neutral";
}

export interface SystemOperation {
  title: string;
  time: string;
  details: string[];
  status: string;
  tone?: "positive" | "negative" | "warning" | "info" | "neutral";
}

export interface SystemStatusItem {
  label: string;
  value: string;
  tone?: "positive" | "negative" | "warning" | "info" | "neutral";
}

export interface DbHealthItem {
  label: string;
  value: string;
}

export interface SystemSnapshot {
  metrics: SystemMetric[];
  operations: SystemOperation[];
  pipelineStatus: SystemStatusItem[];
  dbHealth: DbHealthItem[];
  ingestionRuns: IngestionRun[];
}
