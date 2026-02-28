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
