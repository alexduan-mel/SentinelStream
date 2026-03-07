import Chip from "./Chip";
import type { Sentiment } from "../utils/sentiment";
import { getSentimentMeta } from "../utils/sentiment";

interface SignalHeaderCardProps {
  ticker: string;
  sentiment: Sentiment;
  publishedAt: string;
  summary: string;
  tags: string[];
  confidence: number;
}

const arrowPaths = {
  up: ["M7 7h10v10", "M7 17 17 7"],
  down: ["M7 17h10V7", "M7 7 17 17"]
};

export default function SignalHeaderCard({
  ticker,
  sentiment,
  publishedAt,
  summary,
  tags,
  confidence
}: SignalHeaderCardProps) {
  const sentimentMeta = getSentimentMeta(sentiment);
  const arrowPath = sentimentMeta.icon === "up" ? arrowPaths.up : arrowPaths.down;

  return (
    <section className="rounded-md border border-border-default bg-bg-surface p-24">
      <div className="flex items-start justify-between gap-24">
        <div className="flex flex-col gap-12">
          <div className="flex items-center gap-12">
            <div className="flex items-center gap-8">
              {sentimentMeta.icon !== "none" && (
                <svg
                  width="16"
                  height="16"
                  viewBox="0 0 24 24"
                  fill="none"
                  xmlns="http://www.w3.org/2000/svg"
                  className={sentimentMeta.colorClass}
                >
                  {arrowPath.map((d) => (
                    <path
                      key={d}
                      d={d}
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  ))}
                </svg>
              )}
              <span className={["text-sm font-medium", sentimentMeta.colorClass].join(" ")}>
                {sentimentMeta.label}
              </span>
            </div>
            <span className="text-lg font-bold tracking-tight text-white">{ticker}</span>
          </div>
          <div className="text-caption text-text-muted">{publishedAt}</div>
          <p className="text-body text-text-secondary">{summary}</p>
          <div className="flex items-center gap-8">
            {tags.map((tag) => (
              <Chip key={tag} tone="neutral">
                {tag}
              </Chip>
            ))}
          </div>
        </div>

        <div className="flex flex-col items-end gap-8">
          <div className="flex items-center gap-8 text-caption text-text-secondary">
            <svg
              width="14"
              height="14"
              viewBox="0 0 24 24"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
              className="text-semantic-info"
            >
              <path
                d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
            Verified
          </div>
          <div className="text-h2 text-text-primary tabular-nums">{Math.round(confidence * 100)}%</div>
          <div className="text-caption text-text-muted">confidence</div>
        </div>
      </div>
    </section>
  );
}
