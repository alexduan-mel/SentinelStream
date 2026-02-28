export type Sentiment = "positive" | "negative" | "neutral";

export type SentimentIcon = "up" | "down" | "none";

export interface SentimentMeta {
  label: string;
  icon: SentimentIcon;
  colorClass: string;
}

const sentimentMetaMap: Record<Sentiment, SentimentMeta> = {
  positive: {
    label: "Bullish",
    icon: "up",
    colorClass: "text-semantic-positive"
  },
  negative: {
    label: "Bearish",
    icon: "down",
    colorClass: "text-semantic-negative"
  },
  neutral: {
    label: "Neutral",
    icon: "none",
    colorClass: "text-text-muted"
  }
};

export function getSentimentMeta(sentiment: Sentiment): SentimentMeta {
  return sentimentMetaMap[sentiment];
}

export function normalizeSentiment(value: string | null | undefined): Sentiment {
  const normalized = (value ?? "").toLowerCase();
  if (normalized === "positive" || normalized === "bullish") {
    return "positive";
  }
  if (normalized === "negative" || normalized === "bearish") {
    return "negative";
  }
  if (normalized === "neutral") {
    return "neutral";
  }
  return "neutral";
}
