import ProgressBar from "./ProgressBar";
import type { Sentiment } from "../utils/sentiment";
import { getSentimentMeta } from "../utils/sentiment";

interface ModelAgreementItem {
  id: string;
  model: string;
  sentiment: Sentiment;
  confidence: number;
  agreement: number;
}

interface ModelAgreementCardProps {
  items: ModelAgreementItem[];
}

export default function ModelAgreementCard({ items }: ModelAgreementCardProps) {
  return (
    <section className="rounded-md border border-border-default bg-bg-surface p-16">
      <h3 className="text-h3">Model Agreement</h3>
      <div className="mt-16 flex flex-col gap-16">
        {items.map((item) => {
          const sentimentMeta = getSentimentMeta(item.sentiment);
          return (
            <div key={item.id} className="flex flex-col gap-8">
              <div className="flex items-center justify-between">
                <div className="text-body text-text-primary">{item.model}</div>
                <div className={["text-caption font-medium", sentimentMeta.colorClass].join(" ")}>
                  {sentimentMeta.label}
                </div>
              </div>
              <div className="flex flex-col gap-8">
                <div className="flex items-center justify-between text-caption text-text-muted">
                  <span>Confidence</span>
                  <span className="tabular-nums">{Math.round(item.confidence * 100)}%</span>
                </div>
                <ProgressBar value={item.confidence * 100} tone="info" />
              </div>
              <div className="flex flex-col gap-8">
                <div className="flex items-center justify-between text-caption text-text-muted">
                  <span>Agreement</span>
                  <span className="tabular-nums">{Math.round(item.agreement * 100)}%</span>
                </div>
                <ProgressBar value={item.agreement * 100} tone="positive" />
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
