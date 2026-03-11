import { useCallback } from "react";
import { Link } from "react-router-dom";

import Card from "../../components/Card";
import Chip from "../../components/Chip";
import ProgressBar from "../../components/ProgressBar";
import SignalCard from "../../components/SignalCard";
import { listSignals } from "../../api/signalsApi";
import { listTopics } from "../../api/topicsApi";
import { getSystemSnapshot } from "../../api/systemApi";
import { useAsyncData } from "../../hooks/useAsyncData";

export default function MonitorPage() {
  const loadSignals = useCallback(() => listSignals(), []);
  const loadTopics = useCallback(() => listTopics(), []);
  const loadSystem = useCallback(() => getSystemSnapshot(), []);

  const { data: signalsData } = useAsyncData(loadSignals);
  const { data: topicsData } = useAsyncData(loadTopics);
  const { data: systemData } = useAsyncData(loadSystem);

  const signals = signalsData ?? [];
  const topics = topicsData ?? [];
  const latestRun = systemData?.ingestionRuns[0];

  const systemHealth = [
    {
      label: "Ingestion Latency",
      value: latestRun?.metrics?.ingestionLatencySec
        ? `${latestRun.metrics.ingestionLatencySec.toFixed(1)}s`
        : "--"
    },
    {
      label: "Model Agreement",
      value: latestRun?.metrics?.modelAgreementPct ? `${latestRun.metrics.modelAgreementPct}%` : "--"
    },
    {
      label: "Rule Pass Rate",
      value: latestRun?.metrics?.rulePassRatePct ? `${latestRun.metrics.rulePassRatePct}%` : "--"
    }
  ];

  return (
    <div className="flex flex-col gap-24">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-text-primary">Monitor</h1>
          <p className="text-sm text-text-secondary font-normal">Real-time signal verification and market pulse</p>
        </div>
        <div className="flex items-center gap-8">
          {"All Sources,All Types,All Assets".split(",").map((label) => (
            <button
              key={label}
              className="rounded border border-border-default bg-bg-surface px-12 py-8 text-label text-text-secondary hover:bg-state-hover"
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-12 gap-24">
        <section className="col-span-8 flex flex-col gap-16">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-semibold text-text-primary">Verified Signals</h2>
              <p className="text-sm text-text-secondary font-normal">2 verified · {signals.length} total</p>
            </div>
            <button className="rounded border border-border-default bg-bg-surface px-12 py-8 text-label text-text-secondary hover:bg-state-hover">
              Newest
            </button>
          </div>
          <div className="flex flex-col gap-12">
            {signals.map((signal) => (
              <Link key={signal.id} to={`/ticker/${signal.ticker}`} className="block">
                <SignalCard {...signal} />
              </Link>
            ))}
          </div>
        </section>

        <aside className="col-span-4 flex flex-col gap-16">
          <Card title="Market Pulse" action={<Chip tone="neutral">Newest</Chip>}>
            <div className="flex flex-col gap-12">
              {topics.map((item) => (
                <div key={item.id} className="rounded border border-border-subtle bg-bg-elevated p-16">
                  <div className="flex items-start justify-between">
                    <div className="flex flex-col gap-8">
                      <div className="text-body text-text-primary">{item.name}</div>
                      <div className="flex flex-wrap gap-8">
                        {item.tags.map((tag) => (
                          <Chip key={tag} tone="neutral">
                            {tag}
                          </Chip>
                        ))}
                        {item.sources && <Chip tone="info">{item.sources}</Chip>}
                      </div>
                    </div>
                    <div className="text-label text-semantic-warning">{item.score.toFixed(1)}</div>
                  </div>
                  <div className="mt-12">
                    <ProgressBar value={item.progress} tone="positive" />
                  </div>
                </div>
              ))}
            </div>
          </Card>

          <Card title="System Health" action={<Chip tone="positive">Operational</Chip>}>
            <div className="flex flex-col gap-12">
              {systemHealth.map((metric) => (
                <div key={metric.label} className="flex items-center justify-between">
                  <span className="text-caption text-text-muted">{metric.label}</span>
                  <span className="text-label text-semantic-positive">{metric.value}</span>
                </div>
              ))}
              <div className="text-caption text-text-muted">Last update 09:24 PM</div>
            </div>
          </Card>
        </aside>
      </div>
    </div>
  );
}
