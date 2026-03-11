import { useState } from "react";

import NarrativeCard from "../../components/NarrativeCard";
import { marketNarratives } from "../../data/marketPulse";

const timeRanges = ["24H", "7D", "30D"] as const;
const assetClasses = ["All", "Equity", "Macro", "Commodity", "Crypto"] as const;
const sortOptions = ["Strength", "Momentum", "Recent"] as const;

function FilterGroup<T extends string>({
  label,
  options,
  value,
  onChange
}: {
  label: string;
  options: readonly T[];
  value: T;
  onChange: (next: T) => void;
}) {
  return (
    <div className="flex items-center gap-8">
      <span className="text-caption text-text-muted">{label}</span>
      <div className="flex items-center gap-8">
        {options.map((option) => (
          <button
            key={option}
            type="button"
            onClick={() => onChange(option)}
            className={[
              "rounded border px-12 py-6 text-label transition",
              option === value
                ? "border-border-default bg-bg-elevated text-text-primary"
                : "border-border-subtle bg-bg-surface text-text-secondary hover:bg-state-hover"
            ].join(" ")}
          >
            {option}
          </button>
        ))}
      </div>
    </div>
  );
}

export default function MarketPulsePage() {
  const [timeRange, setTimeRange] = useState<(typeof timeRanges)[number]>("7D");
  const [assetClass, setAssetClass] = useState<(typeof assetClasses)[number]>("All");
  const [sortBy, setSortBy] = useState<(typeof sortOptions)[number]>("Strength");

  return (
    <div className="flex flex-col gap-24">
      <header className="flex flex-col gap-8">
        <h1 className="text-2xl font-semibold tracking-tight text-text-primary">Market Pulse</h1>
        <p className="text-sm text-text-secondary">
          Track high-impact narratives, signal strength, and affected assets.
        </p>
      </header>

      <div className="flex flex-wrap items-center gap-16 rounded border border-border-subtle bg-bg-surface p-16">
        <FilterGroup label="Time" options={timeRanges} value={timeRange} onChange={setTimeRange} />
        <FilterGroup label="Asset Class" options={assetClasses} value={assetClass} onChange={setAssetClass} />
        <FilterGroup label="Sort" options={sortOptions} value={sortBy} onChange={setSortBy} />
      </div>

      <section className="grid grid-cols-1 gap-20 lg:grid-cols-2">
        {marketNarratives.map((narrative) => (
          <NarrativeCard key={narrative.id} narrative={narrative} />
        ))}
      </section>
    </div>
  );
}
