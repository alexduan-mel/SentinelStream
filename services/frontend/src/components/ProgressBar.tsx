interface ProgressBarProps {
  value: number;
  tone?: "positive" | "negative" | "warning" | "info" | "neutral";
}

const toneStyles: Record<NonNullable<ProgressBarProps["tone"]>, string> = {
  positive: "bg-semantic-positive",
  negative: "bg-semantic-negative",
  warning: "bg-semantic-warning",
  info: "bg-semantic-info",
  neutral: "bg-semantic-neutral"
};

export default function ProgressBar({ value, tone = "info" }: ProgressBarProps) {
  return (
    <div className="h-4 w-full rounded bg-border-subtle">
      <div
        className={["h-4 rounded", toneStyles[tone]].join(" ")}
        style={{ width: `${Math.max(0, Math.min(value, 100))}%` }}
      />
    </div>
  );
}
