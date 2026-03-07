import type { ReactNode } from "react";

type ChipTone = "positive" | "negative" | "warning" | "info" | "neutral" | "default";

interface ChipProps {
  children: ReactNode;
  tone?: ChipTone;
  className?: string;
}

const toneStyles: Record<ChipTone, string> = {
  positive: "text-semantic-positive",
  negative: "text-semantic-negative",
  warning: "text-semantic-warning",
  info: "text-semantic-info",
  neutral: "text-semantic-neutral",
  default: "text-text-secondary"
};

export default function Chip({ children, tone = "default", className = "" }: ChipProps) {
  return (
    <span
      className={[
        "inline-flex w-fit items-center gap-4 rounded-sm border border-border-default bg-bg-elevated px-8 py-4 text-label",
        toneStyles[tone],
        className
      ].join(" ")}
    >
      {children}
    </span>
  );
}
