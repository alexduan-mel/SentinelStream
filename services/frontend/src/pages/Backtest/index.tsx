import { useCallback } from "react";

import Card from "../../components/Card";
import MetricTile from "../../components/MetricTile";
import ProgressBar from "../../components/ProgressBar";
import { listBacktests } from "../../api/backtestApi";
import { useAsyncData } from "../../hooks/useAsyncData";

export default function BacktestPage() {
  const loadBacktests = useCallback(() => listBacktests(), []);
  const { data } = useAsyncData(loadBacktests);
  const run = data?.[0];

  const metrics = [
    { label: "Total Return", value: run ? `${run.totalReturn.toFixed(1)}%` : "--", tone: "positive" as const },
    { label: "Sharpe Ratio", value: run ? run.sharpeRatio.toFixed(2) : "--", tone: "info" as const },
    { label: "Max Drawdown", value: run ? `${run.maxDrawdown.toFixed(1)}%` : "--", tone: "negative" as const },
    { label: "Win Rate", value: run ? `${run.winRate}%` : "--", tone: "positive" as const }
  ];

  const ruleContribution = run?.ruleContribution ?? [];
  const attribution = run?.attribution ?? [];
  const falseAnalysis = run?.falseAnalysis;

  return (
    <div className="flex flex-col gap-24">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-text-primary">Backtest & Evaluation</h1>
        <p className="text-sm text-text-secondary font-normal">Performance analysis and signal attribution</p>
      </div>

      <div className="grid grid-cols-4 gap-24">
        {metrics.map((metric) => (
          <MetricTile key={metric.label} label={metric.label} value={metric.value} tone={metric.tone} />
        ))}
      </div>

      <div className="grid grid-cols-12 gap-24">
        <Card title="Performance Curve" className="col-span-8">
          <div className="flex h-64 items-end justify-between text-caption text-text-muted">
            {"Jan Feb Mar Apr May Jun".split(" ").map((month) => (
              <div key={month}>{month}</div>
            ))}
          </div>
          <div className="mt-16 h-64 rounded-md border border-border-subtle bg-bg-elevated" />
        </Card>
        <Card title="Rule Contribution" className="col-span-4">
          <div className="flex flex-col gap-16">
            {ruleContribution.map((rule) => (
              <div key={rule.label} className="flex flex-col gap-8">
                <div className="text-body text-text-primary">{rule.label}</div>
                <div className="text-caption text-text-muted">Accuracy</div>
                <ProgressBar value={rule.accuracy} tone="positive" />
                <div className="text-caption text-text-muted">Frequency</div>
                <ProgressBar value={rule.frequency} tone="info" />
              </div>
            ))}
          </div>
        </Card>
      </div>

      <div className="grid grid-cols-12 gap-24">
        <Card title="Signal Attribution" className="col-span-8">
          <div className="flex flex-col gap-16">
            {attribution.map((row) => (
              <div key={row.label} className="flex items-center justify-between">
                <div className="text-body text-text-primary">{row.label}</div>
                <div className="w-64">
                  <ProgressBar value={Math.min(Math.abs(row.value) * 10, 100)} tone={row.value >= 0 ? "positive" : "negative"} />
                </div>
                <div className={row.value >= 0 ? "text-semantic-positive" : "text-semantic-negative"}>
                  {row.value > 0 ? "+" : ""}
                  {row.value.toFixed(1)}%
                </div>
              </div>
            ))}
          </div>
        </Card>
        <Card title="False Analysis" className="col-span-4">
          <div className="flex flex-col gap-12">
            <div className="rounded-md border border-border-subtle bg-bg-elevated p-16">
              <div className="text-caption text-text-muted">False Positives</div>
              <div className="text-h2 text-semantic-negative">
                {falseAnalysis ? falseAnalysis.falsePositives : "--"}
              </div>
            </div>
            <div className="rounded-md border border-border-subtle bg-bg-elevated p-16">
              <div className="text-caption text-text-muted">False Negatives</div>
              <div className="text-h2 text-semantic-warning">
                {falseAnalysis ? falseAnalysis.falseNegatives : "--"}
              </div>
            </div>
            <div className="text-caption text-text-muted">
              Total Errors {falseAnalysis ? falseAnalysis.totalErrors : "--"}
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}
