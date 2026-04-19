import { useCallback, useMemo } from "react";
import { Link, useParams } from "react-router-dom";

import EvidenceList from "../../components/EvidenceList";
import ModelAgreementCard from "../../components/ModelAgreementCard";
import RuleChecklistCard from "../../components/RuleChecklistCard";
import SignalHeaderCard from "../../components/SignalHeaderCard";
import SignalLineageCard from "../../components/SignalLineageCard";
import { getTickerSignals } from "../../api/tickersApi";
import { useAsyncData } from "../../hooks/useAsyncData";
import type { Sentiment } from "../../utils/sentiment";

const ruleChecklist = [
  {
    id: "rule-1",
    label: "Multi-source confirmation",
    description: "Signal confirmed by 3+ independent sources",
    weight: "30%"
  },
  {
    id: "rule-2",
    label: "Volume confirmation",
    description: "Trading volume above 120% of average",
    weight: "20%"
  },
  {
    id: "rule-3",
    label: "Model consensus",
    description: "Agreement score > 0.8",
    weight: "25%"
  },
  {
    id: "rule-4",
    label: "Historical accuracy",
    description: "Similar signals 72% accurate",
    weight: "25%"
  }
];

const modelAgreement: Array<{
  id: string;
  model: string;
  sentiment: Sentiment;
  confidence: number;
  agreement: number;
}> = [
  {
    id: "model-1",
    model: "GPT-4",
    sentiment: "positive",
    confidence: 0.89,
    agreement: 0.92
  },
  {
    id: "model-2",
    model: "Claude",
    sentiment: "positive",
    confidence: 0.85,
    agreement: 0.88
  },
  {
    id: "model-3",
    model: "Gemini",
    sentiment: "positive",
    confidence: 0.87,
    agreement: 0.9
  }
];

const formatDateTime = (value: string) => {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "--";
  }
  const pad = (num: number) => String(num).padStart(2, "0");
  return [
    `${date.getFullYear()}/${pad(date.getMonth() + 1)}/${pad(date.getDate())}`,
    `${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`
  ].join(" ");
};

export default function SignalDetailPage() {
  const { symbol, id } = useParams();
  const ticker = (symbol ?? id ?? "").trim().toUpperCase();
  const loadSignals = useCallback(
    () =>
      ticker
        ? getTickerSignals(ticker, { limit: 50, offset: 0, includeRaw: true })
        : Promise.resolve({ ticker: "", latest: null, items: [], limit: 50, offset: 0, total: 0 }),
    [ticker]
  );
  const { data, error, loading } = useAsyncData(loadSignals);

  const latest = data?.latest ?? null;
  const evidenceItems = useMemo(
    () =>
      (data?.items ?? []).map((item) => ({
        id: item.analysisId,
        publisher: item.news.publisher ?? "Unknown",
        headline: item.news.title,
        timestamp: formatDateTime(item.publishedAt),
        signalConfidence: item.signalConfidence,
        analyses: item.analyses
      })),
    [data?.items]
  );

  return (
    <div className="flex flex-col gap-24">
      <Link to="/monitor" className="inline-flex items-center gap-8 text-sm text-text-secondary hover:text-text-primary">
        <svg
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className="text-text-muted"
        >
          <path
            d="M15 18l-6-6 6-6"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
        Back to Monitor
      </Link>

      {!ticker ? (
        <div className="rounded border border-border-subtle bg-bg-surface p-20 text-body text-text-secondary">
          Invalid ticker.
        </div>
      ) : loading ? (
        <div className="rounded border border-border-subtle bg-bg-surface p-20 text-body text-text-secondary">
          Loading signal...
        </div>
      ) : error ? (
        <div className="rounded border border-semantic-negative/40 bg-bg-surface p-20 text-body text-semantic-negative">
          Failed to load signal for {ticker}: {error}
        </div>
      ) : !latest ? (
        <div className="rounded border border-border-subtle bg-bg-surface p-20 text-body text-text-secondary">
          No related signal found for {ticker} yet.
        </div>
      ) : (
      <div className="grid grid-cols-12 gap-24">
        <section className="col-span-8 flex flex-col gap-16">
          <SignalHeaderCard
            ticker={latest.ticker}
            sentiment={latest.analyses[0]?.sentiment ?? "neutral"}
            publishedAt={formatDateTime(latest.publishedAt)}
            summary={latest.analyses[0]?.summary ?? latest.news.title}
            tags={["Equity", "Watchlist"]}
            confidence={latest.signalConfidence}
          />

          <EvidenceList items={evidenceItems} />
        </section>

        <aside className="col-span-4 flex flex-col gap-16">
          <RuleChecklistCard items={ruleChecklist} />
          <ModelAgreementCard items={modelAgreement} />
          <SignalLineageCard origin="Ticker" mappedTickers={[latest.ticker]} />
        </aside>
      </div>
      )}
    </div>
  );
}
