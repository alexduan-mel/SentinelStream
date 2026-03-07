import Chip from "./Chip";

interface SignalLineageCardProps {
  origin: string;
  mappedTickers: string[];
}

export default function SignalLineageCard({ origin, mappedTickers }: SignalLineageCardProps) {
  return (
    <section className="rounded-md border border-border-default bg-bg-surface p-16">
      <h3 className="text-h3">Signal Lineage</h3>
      <div className="mt-16 flex flex-col gap-12">
        <div>
          <div className="text-caption text-text-muted">Origin</div>
          <div className="text-body text-text-primary">{origin}</div>
        </div>
        <div>
          <div className="text-caption text-text-muted">Mapped Tickers</div>
          <div className="mt-8 flex flex-wrap gap-8">
            {mappedTickers.map((ticker) => (
              <Chip key={ticker} tone="neutral">
                {ticker}
              </Chip>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
