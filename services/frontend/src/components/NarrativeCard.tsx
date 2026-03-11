import type { AssetClass, MarketNarrative, NarrativeDirection, NarrativeStatus } from "../types/marketPulse";

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

const assetBadgeStyle: Record<AssetClass, string> = {
  Equity: "text-text-secondary bg-bg-elevated border-border-default",
  Macro: "text-semantic-info bg-bg-elevated border-border-default",
  Commodity: "text-semantic-warning bg-bg-elevated border-border-default",
  Crypto: "text-text-secondary bg-bg-elevated border-border-default"
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
        width="18"
        height="18"
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
        width="18"
        height="18"
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
      width="18"
      height="18"
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
      <span className="text-[9px] uppercase tracking-widest text-text-muted/70">{label}</span>
      <span className={[("font-mono text-xl font-semibold"), valueClassName ?? "text-text-primary"].join(" ")}>
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

  return (
    <article
      className={[
        "group flex h-full flex-col gap-16 rounded-md border border-border-default border-l-2 bg-bg-surface p-20",
        "transition-all hover:border-border-subtle hover:bg-bg-elevated",
        directionBorder[narrative.direction]
      ].join(" ")}
    >
      <div className="flex items-start justify-between gap-12">
        <div className="flex min-w-0 items-start gap-8">
          <div className="mt-2">
            <DirectionIcon direction={narrative.direction} />
          </div>
          <div className="flex min-w-0 flex-col gap-8">
            <div className="flex min-w-0 items-center gap-8">
              <span className="truncate text-base font-semibold leading-snug text-text-primary">
                {narrative.title}
              </span>
            </div>
            <div className="flex flex-wrap items-center gap-8">
              <span
                className={[
                  "inline-flex items-center rounded border px-8 py-4 text-xs font-medium capitalize",
                  statusBadgeStyle[narrative.status]
                ].join(" ")}
              >
                {narrative.status.toLowerCase()}
              </span>
              <span
                className={[
                  "inline-flex items-center rounded border px-8 py-4 text-xs font-medium capitalize",
                  assetBadgeStyle[narrative.assetClass]
                ].join(" ")}
              >
                {narrative.assetClass.toLowerCase()}
              </span>
            </div>
          </div>
        </div>
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="mt-2 h-4 w-4 shrink-0 text-text-muted/40 transition-colors group-hover:text-semantic-info"
        >
          <path d="m9 18 6-6-6-6" />
        </svg>
      </div>

      <p className="text-xs text-text-secondary leading-relaxed">{narrative.summary}</p>

      <div className="grid grid-cols-3 gap-12 rounded border border-border-subtle bg-bg-elevated p-12">
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
          <span className="text-[9px] uppercase tracking-widest text-text-muted/70">Sources</span>
          <div className="flex items-baseline gap-6">
            <span className="font-mono text-xl font-semibold text-text-primary">
              {narrative.sourceCount}
            </span>
            {sourceDeltaLabel && <span className="text-[10px] font-mono text-semantic-info">{sourceDeltaLabel}</span>}
          </div>
        </div>
      </div>

      <div className="flex flex-wrap gap-6">
        {narrative.affectedAssets.map((asset, index) => (
          <button
            key={asset}
            className={[
              "rounded border px-8 py-4 text-[10px] font-mono font-medium transition",
              index === 0
                ? "border-border-default bg-bg-elevated text-text-primary"
                : "border-border-subtle bg-bg-surface text-text-muted"
            ].join(" ")}
            type="button"
          >
            {asset}
          </button>
        ))}
      </div>

      <div className="flex items-center justify-between text-[10px] text-text-muted/70">
        <span>Last update: {narrative.lastUpdatedLabel}</span>
        <span>Age: {narrative.ageLabel}</span>
      </div>
    </article>
  );
}
