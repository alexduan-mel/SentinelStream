import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";

import NarrativeCard from "../../components/NarrativeCard";
import { getMarketNarratives } from "../../lib/market-pulse/api";
import type { MarketNarrative, MarketNarrativeQuery } from "../../lib/market-pulse/types";

const timeRanges = [
  { label: "24H", value: "24h" },
  { label: "7D", value: "7d" },
  { label: "30D", value: "30d" }
] as const;
const assetClasses = [
  { label: "All", value: "all" },
  { label: "Equity", value: "equity" },
  { label: "Macro", value: "macro" },
  { label: "Commodity", value: "commodity" },
  { label: "Crypto", value: "crypto" }
] as const;
const sortOptions = [
  { label: "Strength", value: "strength" },
  { label: "Momentum", value: "momentum" },
  { label: "Recent", value: "recent" }
] as const;

function FilterGroup<T extends string>({
  label,
  options,
  value,
  onChange
}: {
  label: string;
  options: readonly { label: string; value: T }[];
  value: T;
  onChange: (next: T) => void;
}) {
  return (
    <div className="flex items-center gap-8">
      <span className="text-caption text-text-muted">{label}</span>
      <div className="flex items-center gap-8">
        {options.map((option) => (
          <button
            key={option.value}
            type="button"
            onClick={() => onChange(option.value)}
            className={[
              "rounded border px-12 py-6 text-label transition",
              option.value === value
                ? "border-border-default bg-bg-elevated text-text-primary"
                : "border-border-subtle bg-bg-surface text-text-secondary hover:bg-state-hover"
            ].join(" ")}
          >
            {option.label}
          </button>
        ))}
      </div>
    </div>
  );
}

export default function MarketPulsePage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [narratives, setNarratives] = useState<MarketNarrative[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const query = useMemo<MarketNarrativeQuery>(() => {
    const range = (searchParams.get("range") as MarketNarrativeQuery["range"]) ?? "7d";
    const assetClass = (searchParams.get("assetClass") as MarketNarrativeQuery["assetClass"]) ?? "all";
    const sort = (searchParams.get("sort") as MarketNarrativeQuery["sort"]) ?? "strength";
    return { range, assetClass, sort };
  }, [searchParams]);

  useEffect(() => {
    let isMounted = true;
    setLoading(true);
    setError(null);
    getMarketNarratives(query)
      .then((data) => {
        if (!isMounted) return;
        setNarratives(data);
      })
      .catch((err) => {
        if (!isMounted) return;
        setError(err instanceof Error ? err.message : "Failed to load narratives.");
      })
      .finally(() => {
        if (!isMounted) return;
        setLoading(false);
      });
    return () => {
      isMounted = false;
    };
  }, [query]);

  const updateQuery = (next: Partial<MarketNarrativeQuery>) => {
    const params = new URLSearchParams(searchParams);
    if (next.range) params.set("range", next.range);
    if (next.assetClass) params.set("assetClass", next.assetClass);
    if (next.sort) params.set("sort", next.sort);
    setSearchParams(params);
  };

  return (
    <div className="flex flex-col gap-24">
      <header className="flex flex-col gap-8">
        <h1 className="text-2xl font-semibold tracking-tight text-text-primary">Market Pulse</h1>
        <p className="text-sm text-text-secondary">
          Track high-impact narratives, signal strength, and affected assets.
        </p>
      </header>

      <div className="flex flex-wrap items-center gap-16 rounded border border-border-subtle bg-bg-surface p-16">
        <FilterGroup
          label="Time"
          options={timeRanges}
          value={query.range ?? "7d"}
          onChange={(value) => updateQuery({ range: value })}
        />
        <FilterGroup
          label="Asset Class"
          options={assetClasses}
          value={query.assetClass ?? "all"}
          onChange={(value) => updateQuery({ assetClass: value })}
        />
        <FilterGroup
          label="Sort"
          options={sortOptions}
          value={query.sort ?? "strength"}
          onChange={(value) => updateQuery({ sort: value })}
        />
      </div>

      {loading ? (
        <div className="rounded border border-border-subtle bg-bg-surface p-24 text-text-secondary">
          Loading market narratives...
        </div>
      ) : error ? (
        <div className="rounded border border-semantic-negative/40 bg-bg-surface p-24 text-semantic-negative">
          {error}
        </div>
      ) : narratives.length === 0 ? (
        <div className="rounded border border-border-subtle bg-bg-surface p-24 text-text-secondary">
          No narratives found for the selected filters.
        </div>
      ) : (
        <section className="grid grid-cols-1 gap-20 lg:grid-cols-2">
          {narratives.map((narrative) => (
            <NarrativeCard key={narrative.id} narrative={narrative} />
          ))}
        </section>
      )}
    </div>
  );
}
