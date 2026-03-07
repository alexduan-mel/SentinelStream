interface MetricTileProps {
  label: string;
  value: string;
  meta?: string;
  tone?: "positive" | "negative" | "warning" | "info" | "neutral";
}

const toneStyles: Record<NonNullable<MetricTileProps["tone"]>, string> = {
  positive: "text-semantic-positive",
  negative: "text-semantic-negative",
  warning: "text-semantic-warning",
  info: "text-semantic-info",
  neutral: "text-semantic-neutral"
};

export default function MetricTile({ label, value, meta, tone = "neutral" }: MetricTileProps) {
  return (
    <div className="rounded-md border border-border-default bg-bg-surface p-16">
      <div className="text-caption text-text-muted">{label}</div>
      <div className={["text-h2", toneStyles[tone]].join(" ")}>{value}</div>
      {meta && <div className="text-caption text-text-muted">{meta}</div>}
    </div>
  );
}
