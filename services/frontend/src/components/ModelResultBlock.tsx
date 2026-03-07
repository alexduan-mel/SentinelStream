import ProgressBar from "./ProgressBar";
import type { AnalysisResult } from "../types";
import { getSentimentMeta } from "../utils/sentiment";

interface ModelResultBlockProps {
  analysis: AnalysisResult;
}

export default function ModelResultBlock({ analysis }: ModelResultBlockProps) {
  const sentimentMeta = getSentimentMeta(analysis.sentiment);
  const badgeTone =
    analysis.sentiment === "positive"
      ? "bg-semantic-positive/20 text-semantic-positive"
      : analysis.sentiment === "negative"
        ? "bg-semantic-negative/20 text-semantic-negative"
        : "bg-semantic-neutral/20 text-semantic-neutral";

  return (
    <div className="flex items-start justify-between gap-16 px-16 py-12">
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-12">
          <span className="text-body font-semibold text-text-primary">{analysis.provider}</span>
          <span className="text-caption text-text-muted">{analysis.model}</span>
        </div>
        <p className="mt-8 text-body text-text-secondary">{analysis.summary}</p>
      </div>
      <div className="flex w-64 flex-col items-end gap-8">
        <span className={["rounded-sm px-8 py-4 text-caption font-medium", badgeTone].join(" ")}>
          {sentimentMeta.label}
        </span>
        <ProgressBar value={analysis.confidence * 100} tone="info" />
        <span className="text-caption text-text-muted tabular-nums">
          {Math.round(analysis.confidence * 100)}%
        </span>
      </div>
    </div>
  );
}
