import { useCallback } from "react";

import Card from "../../components/Card";
import SignalCard from "../../components/SignalCard";
import { listSignals } from "../../api/signalsApi";
import { useAsyncData } from "../../hooks/useAsyncData";

const filters = ["Ticker", "Sentiment", "Confidence", "Date Range"];

export default function SignalsPage() {
  const loadSignals = useCallback(() => listSignals(), []);
  const { data } = useAsyncData(loadSignals);
  const signals = data ?? [];

  return (
    <div className="flex flex-col gap-24">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-text-primary">Signals</h1>
        <p className="text-sm text-text-secondary font-normal">All trading signals from watchlist pipeline</p>
      </div>
      <div className="flex items-center gap-8">
        {filters.map((label) => (
          <button
            key={label}
            className="rounded-pill border border-border-default bg-bg-surface px-12 py-8 text-label text-text-secondary hover:bg-state-hover"
          >
            {label}
          </button>
        ))}
      </div>
      <div className="grid grid-cols-2 gap-24">
        {signals.map((signal) => (
          <SignalCard key={signal.id} {...signal} />
        ))}
      </div>
      <Card title="Signals Table" subtitle="Table placeholder">
        <div className="grid grid-cols-4 gap-12 text-caption text-text-muted">
          <div>Signal</div>
          <div>Sentiment</div>
          <div>Confidence</div>
          <div>Timestamp</div>
        </div>
        <div className="mt-12 rounded-md border border-border-subtle bg-bg-elevated p-16 text-caption text-text-muted">
          No rows to display
        </div>
      </Card>
    </div>
  );
}
