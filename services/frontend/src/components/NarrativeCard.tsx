import type { MarketNarrative, NarrativeDirection, NarrativeStatus } from "../lib/market-pulse/types";

interface NarrativeCardProps {
  narrative: MarketNarrative;
}

const directionStyle: Record<NarrativeDirection, string> = {
  bullish: "text-semantic-positive",
  bearish: "text-semantic-negative",
  neutral: "text-semantic-neutral"
};

const directionBorder: Record<NarrativeDirection, string> = {
  bullish: "border-l-semantic-positive",
  bearish: "border-l-semantic-negative",
  neutral: "border-l-border-default"
};

const statusBadgeStyle: Record<NarrativeStatus, string> = {
  Emerging: "text-semantic-info bg-bg-elevated border-border-default",
  Developing: "text-semantic-warning bg-bg-elevated border-border-default",
  Confirmed: "text-semantic-positive bg-bg-elevated border-border-default",
  Fading: "text-semantic-neutral bg-bg-elevated border-border-default"
};

const signalStrengthStyle = (value: number) => {
  if (value >= 80) return "text-semantic-negative";
  if (value >= 60) return "text-semantic-warning";
  return "text-text-muted";
};

const momentumStyle = (value: number) => {
  if (value > 0) return "text-semantic-positive";
  if (value < 0) return "text-semantic-negative";
  return "text-text-muted";
};

function DirectionIcon({ direction }: { direction: NarrativeDirection }) {
  const className = directionStyle[direction];
  if (direction === "bullish") {
    return (
      <svg
        width="14"
        height="14"
        viewBox="0 0 20 20"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className={className}
      >
        <path d="M5 11l5-5 5 5" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
        <path d="M10 6v9" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
      </svg>
    );
  }
  if (direction === "bearish") {
    return (
      <svg
        width="14"
        height="14"
        viewBox="0 0 20 20"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className={className}
      >
        <path d="M5 9l5 5 5-5" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
        <path d="M10 5v9" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
      </svg>
    );
  }
  return (
    <svg
      width="14"
      height="14"
      viewBox="0 0 20 20"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      <path d="M4 10h12" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
    </svg>
  );
}

function MetricItem({ label, value, valueClassName }: { label: string; value: string; valueClassName?: string }) {
  return (
    <div className="flex flex-col gap-4">
      <span className="text-[9px] uppercase tracking-widest text-text-muted/60">{label}</span>
      <span className={["font-mono text-xl font-bold", valueClassName ?? "text-text-primary"].join(" ")}>
        {value}
      </span>
    </div>
  );
}

export default function NarrativeCard({ narrative }: NarrativeCardProps) {
  const momentumValue = `${narrative.momentum > 0 ? "+" : ""}${narrative.momentum}`;
  const sourceDeltaLabel =
    typeof narrative.sourceDelta === "number"
      ? `${narrative.sourceDelta > 0 ? "+" : ""}${narrative.sourceDelta}`
      : null;
  const toTitleCase = (value: string) =>
    value
      .replace(/_/g, " ")
      .split(" ")
      .filter(Boolean)
      .map((part) => part.charAt(0).toUpperCase() + part.slice(1).toLowerCase())
      .join(" ");
  const taxonomyParts = [narrative.sector, narrative.subtopic]
    .map((value) => (value ? toTitleCase(value.trim()) : ""))
    .filter(Boolean);
  const taxonomyLabel = taxonomyParts.length > 0 ? taxonomyParts.join(" · ") : null;

  return (
    <article
      className={[
        "group flex h-full flex-col rounded-md border border-border-default bg-bg-surface p-20",
        "transition-all hover:border-border-subtle hover:bg-bg-elevated"
      ].join(" ")}
    >
      <div className="mb-8 flex items-center gap-8">
        <DirectionIcon direction={narrative.direction} />
        {taxonomyLabel && (
          <span className={["text-xs font-medium", directionStyle[narrative.direction]].join(" ")}>
            {taxonomyLabel}
          </span>
        )}
      </div>

      <div className="mb-12 flex items-start justify-between gap-12">
        <h3 className="text-base font-semibold leading-snug text-text-primary">{narrative.displayName}</h3>
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="mt-1 h-4 w-4 shrink-0 text-text-muted/40 transition-colors group-hover:text-semantic-info"
        >
          <path d="m9 18 6-6-6-6" />
        </svg>
      </div>

      <div className="mb-16">
        <span
          className={[
            "inline-flex items-center rounded border px-8 py-4 text-xs font-medium capitalize",
            statusBadgeStyle[narrative.status]
          ].join(" ")}
        >
          {narrative.status.toLowerCase()}
        </span>
      </div>

      <p className="mb-16 text-sm text-text-secondary/70 leading-relaxed">{narrative.summary}</p>

      <div className="mb-16 grid grid-cols-3 gap-12 rounded border border-border-subtle bg-bg-elevated p-12">
        <MetricItem
          label="Signal Strength"
          value={`${narrative.signalStrength} / 100`}
          valueClassName={signalStrengthStyle(narrative.signalStrength)}
        />
        <MetricItem
          label="Momentum"
          value={momentumValue}
          valueClassName={momentumStyle(narrative.momentum)}
        />
        <div className="flex flex-col gap-4">
          <span className="text-[9px] uppercase tracking-widest text-text-muted/60">Sources</span>
          <div className="flex items-baseline gap-8">
            <span className="font-mono text-xl font-bold text-text-primary">
              {narrative.sourceCount}
            </span>
            {sourceDeltaLabel && (
              <span className="text-[10px] font-mono text-semantic-positive">{sourceDeltaLabel}</span>
            )}
          </div>
        </div>
      </div>

      <div className="mb-12 flex flex-wrap gap-8">
        {narrative.affectedAssets.map((asset, index) => (
          <button
            key={asset}
            className={[
              "rounded border px-12 py-6 text-[10px] font-mono font-medium transition",
              index === 0
                ? "border-semantic-info/40 bg-semantic-info/10 text-semantic-info"
                : "border-border-subtle bg-bg-surface text-text-muted"
            ].join(" ")}
            type="button"
          >
            {asset}
          </button>
        ))}
      </div>

      <div className="flex items-center justify-between text-[10px] text-text-muted/50">
        <span>Last update: {narrative.lastUpdatedLabel}</span>
        <span>Age: {narrative.ageLabel}</span>
      </div>
    </article>
  );
}
