import { useState } from "react";

import ModelResultBlock from "./ModelResultBlock";
import ProgressBar from "./ProgressBar";
import { getSentimentMeta } from "../utils/sentiment";
import type { AnalysisResult } from "../types";

export interface EvidenceItem {
  id: string;
  publisher: string;
  headline: string;
  timestamp: string;
  signalConfidence: number;
  analyses: AnalysisResult[];
}

interface EvidenceListProps {
  items: EvidenceItem[];
}

export default function EvidenceList({ items }: EvidenceListProps) {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  return (
    <section className="rounded-md border border-border-default bg-bg-surface p-24">
      <h3 className="text-h3">Evidence</h3>
      {items.length === 0 ? (
        <div className="mt-16 rounded-md border border-border-subtle bg-bg-elevated p-16 text-caption text-text-muted">
          No evidence available
        </div>
      ) : (
        <div className="mt-16 flex flex-col gap-12">
          {items.map((item) => {
            const isExpanded = expandedId === item.id;
            const primaryAnalysis = item.analyses[0];
            const sentimentMeta = primaryAnalysis
              ? getSentimentMeta(primaryAnalysis.sentiment)
              : getSentimentMeta("neutral");
            return (
              <div key={item.id} className="flex flex-col gap-12 rounded-md bg-bg-elevated p-20">
                <button
                  type="button"
                  className="flex w-full items-center justify-between gap-16 text-left"
                  onClick={() => setExpandedId(isExpanded ? null : item.id)}
                >
                  <div className="flex flex-col gap-4">
                    <span className="text-label text-semantic-info">{item.publisher}</span>
                    <span className="text-body text-text-primary">{item.headline}</span>
                    <span className="text-caption text-text-muted">{item.timestamp}</span>
                  </div>
                  <div className="flex w-64 flex-col items-end gap-8">
                    <span className={["text-caption font-medium", sentimentMeta.colorClass].join(" ")}>
                      {sentimentMeta.label}
                    </span>
                    <ProgressBar value={item.signalConfidence * 100} tone="info" />
                    <span className="text-caption text-text-muted tabular-nums">
                      {Math.round(item.signalConfidence * 100)}%
                    </span>
                  </div>
                </button>
                {isExpanded && (
                  <div className="rounded-md border border-border-subtle bg-bg-surface">
                    <div className="px-16 pt-12 text-caption font-semibold uppercase tracking-tight text-text-muted">
                      LLM Analyses
                    </div>
                    {item.analyses.length === 0 ? (
                      <div className="px-16 pb-16 pt-12 text-caption text-text-muted">No analysis available</div>
                    ) : (
                      <div className="divide-y divide-border-subtle">
                        {item.analyses.map((analysis) => (
                          <ModelResultBlock key={`${item.id}-${analysis.model}`} analysis={analysis} />
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
}
