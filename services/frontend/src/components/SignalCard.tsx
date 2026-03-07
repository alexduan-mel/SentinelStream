import Chip from "./Chip";
import type { Sentiment } from "../utils/sentiment";
import { getSentimentMeta } from "../utils/sentiment";

interface SignalCardProps {
  ticker: string;
  sentiment: Sentiment;
  title: string;
  description: string;
  confidence: number;
  timestamp: string;
  tags: string[];
  highConfidence?: boolean;
}

export default function SignalCard({
  ticker,
  sentiment,
  title,
  description,
  confidence,
  timestamp,
  tags,
  highConfidence = false
}: SignalCardProps) {
  const sentimentMeta = getSentimentMeta(sentiment);
  const arrowPath =
    sentimentMeta.icon === "up"
      ? ["M7 7h10v10", "M7 17 17 7"]
      : sentimentMeta.icon === "down"
        ? ["M7 17h10V7", "M7 7 17 17"]
        : [];

  return (
    <div
      className={[
        "rounded-md border bg-bg-surface p-16",
        highConfidence ? "border-semantic-info" : "border-border-default"
      ].join(" ")}
    >
      <div className="flex flex-col gap-12">
        {highConfidence && (
          <span className="inline-flex w-fit items-center rounded-sm border border-semantic-positive/40 bg-semantic-positive/20 px-8 py-4 text-xs text-semantic-positive">
            High Confidence
          </span>
        )}

        <div className="flex items-start justify-between">
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
              <span
                className={["text-sm font-medium", sentimentMeta.colorClass].join(" ")}
              >
                {sentimentMeta.label}
              </span>
            </div>
            <span className="text-lg font-bold tracking-tight text-white">{ticker}</span>
          </div>
          <div className="flex items-center gap-8">
            <svg
              width="16"
              height="16"
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
            <span className="text-sm text-text-secondary font-normal tabular-nums">
              {Math.round(confidence * 100)}%
            </span>
          </div>
        </div>

        <p className="text-sm text-text-secondary font-normal">{description}</p>

        <div className="flex items-center justify-between">
          <div className="flex items-center gap-8">
            {tags.map((tag) => (
              <Chip key={tag} tone="neutral">
                {tag}
              </Chip>
            ))}
          </div>
          <span className="text-sm text-text-muted font-normal">{timestamp}</span>
        </div>
      </div>
    </div>
  );
}
