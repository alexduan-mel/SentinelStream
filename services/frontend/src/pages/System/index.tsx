import { useCallback } from "react";

import Card from "../../components/Card";
import Chip from "../../components/Chip";
import MetricTile from "../../components/MetricTile";
import { getSystemSnapshot } from "../../api/systemApi";
import { useAsyncData } from "../../hooks/useAsyncData";

export default function SystemPage() {
  const loadSystem = useCallback(() => getSystemSnapshot(), []);
  const { data } = useAsyncData(loadSystem);

  const metrics = data?.metrics ?? [];
  const operations = data?.operations ?? [];
  const pipelineStatus = data?.pipelineStatus ?? [];
  const dbHealth = data?.dbHealth ?? [];

  return (
    <div className="flex flex-col gap-24">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-text-primary">System Operations</h1>
        <p className="text-sm text-text-secondary font-normal">Infrastructure, ingestion, and processing metrics</p>
      </div>

      <div className="grid grid-cols-6 gap-24">
        {metrics.map((metric) => (
          <MetricTile
            key={metric.label}
            label={metric.label}
            value={metric.value}
            meta={metric.meta}
            tone={metric.tone}
          />
        ))}
      </div>

      <div className="grid grid-cols-12 gap-24">
        <Card title="Recent Operations" className="col-span-8">
          <div className="flex flex-col gap-12">
            {operations.map((operation) => (
              <div
                key={operation.title}
                className="rounded-md border border-border-subtle bg-bg-elevated p-16"
              >
                <div className="flex items-start justify-between">
                  <div>
                    <div className="text-body text-text-primary">{operation.title}</div>
                    <div className="text-caption text-text-muted">{operation.time}</div>
                  </div>
                  <Chip tone={operation.tone}>{operation.status}</Chip>
                </div>
                <div className="mt-12 grid grid-cols-3 gap-12 text-caption text-text-muted">
                  {operation.details.map((detail) => (
                    <div key={detail}>{detail}</div>
                  ))}
                </div>
              </div>
            ))}
          </div>
          <div className="mt-16 border-t border-border-subtle pt-16">
            <div className="mb-12 text-label text-text-secondary">Ingestion Runs</div>
            <div className="grid grid-cols-5 gap-12 text-caption text-text-muted">
              <div>Started</div>
              <div>Duration</div>
              <div>Status</div>
              <div>Fetched</div>
              <div>Inserted</div>
            </div>
            <div className="mt-12 rounded-md border border-border-subtle bg-bg-elevated p-16 text-caption text-text-muted">
              Table placeholder
            </div>
          </div>
        </Card>

        <div className="col-span-4 flex flex-col gap-24">
          <Card title="Pipeline Status">
            <div className="flex flex-col gap-12">
              {pipelineStatus.map((item) => (
                <div key={item.label} className="flex items-center justify-between">
                  <span className="text-caption text-text-muted">{item.label}</span>
                  <Chip tone={item.tone}>{item.value}</Chip>
                </div>
              ))}
            </div>
          </Card>
          <Card title="Database Health">
            <div className="flex flex-col gap-12">
              {dbHealth.map((item) => (
                <div key={item.label} className="flex items-center justify-between">
                  <span className="text-caption text-text-muted">{item.label}</span>
                  <span className="text-label text-text-secondary">{item.value}</span>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
