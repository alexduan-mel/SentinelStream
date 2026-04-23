import { useEffect, useMemo, useState } from "react";
import type { FormEvent } from "react";

import { addTicker, deleteTicker, getTickerManagement } from "../../api/tickerManagementApi";
import type { TickerManagementItem, TickerManagementSummary, TickerRowStatus } from "../../types";

type StatusFilter = "all" | "active" | "paused" | "error";

const filterOptions: Array<{ value: StatusFilter; label: string }> = [
  { value: "all", label: "All" },
  { value: "active", label: "Active" },
  { value: "paused", label: "Paused" },
  { value: "error", label: "Errors" }
];

const emptySummary: TickerManagementSummary = {
  totalTickers: 0,
  active: 0,
  paused: 0,
  errors: 0
};

const statusClass: Record<TickerRowStatus, string> = {
  active: "bg-semantic-positive/15 text-semantic-positive border-semantic-positive/30",
  paused: "bg-semantic-warning/15 text-semantic-warning border-semantic-warning/30",
  error: "bg-semantic-negative/15 text-semantic-negative border-semantic-negative/30"
};

const jobStatusClass: Record<string, string> = {
  running: "text-semantic-info",
  idle: "text-text-secondary",
  failed: "text-semantic-negative"
};

function formatAgo(value: string | null): string {
  if (!value) return "--";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "--";
  const diffMs = Date.now() - date.getTime();
  const mins = Math.floor(diffMs / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins} min ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours} hour${hours === 1 ? "" : "s"} ago`;
  const days = Math.floor(hours / 24);
  return `${days} day${days === 1 ? "" : "s"} ago`;
}

export default function TickerPage() {
  const [summary, setSummary] = useState<TickerManagementSummary>(emptySummary);
  const [items, setItems] = useState<TickerManagementItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<StatusFilter>("all");
  const [showAddModal, setShowAddModal] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [newTicker, setNewTicker] = useState({ symbol: "", name: "", exchange: "" });

  const reload = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getTickerManagement();
      setSummary(data.summary);
      setItems(data.items);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to load tickers";
      if (message.includes("\"status\":404") || message.includes("404")) {
        setError("Ticker management API not found. Restart java-core to load /api/tickers.");
      } else {
        setError(message);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    reload();
  }, []);

  const filteredItems = useMemo(() => {
    if (filter === "all") return items;
    if (filter === "error") return items.filter((item) => item.status === "error");
    return items.filter((item) => item.status === filter);
  }, [items, filter]);

  const onSubmitAdd = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!newTicker.symbol.trim()) return;
    setSubmitting(true);
    setError(null);
    try {
      await addTicker(newTicker);
      setShowAddModal(false);
      setNewTicker({ symbol: "", name: "", exchange: "" });
      await reload();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to add ticker");
    } finally {
      setSubmitting(false);
    }
  };

  const onDeleteTicker = async (symbol: string) => {
    const confirmed = window.confirm(`Delete ticker ${symbol}?`);
    if (!confirmed) return;
    setError(null);
    try {
      await deleteTicker(symbol);
      await reload();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete ticker");
    }
  };

  return (
    <div className="flex flex-col gap-24">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-text-primary">Ticker Management</h1>
          <p className="text-sm text-text-secondary font-normal">Manage ticker ingestion and analysis workflows</p>
        </div>
        <button
          type="button"
          onClick={() => setShowAddModal(true)}
          className="flex cursor-pointer items-center gap-2 rounded border-0 bg-blue-600 px-4 py-2 font-medium text-white transition-colors duration-150 ease-[cubic-bezier(0.4,0,0.2,1)] hover:bg-blue-700"
        >
          + Add Ticker
        </button>
      </div>

      {error && (
        <div className="rounded border border-semantic-negative/40 bg-bg-surface p-12 text-sm text-semantic-negative">
          {error}
        </div>
      )}

      <div className="grid grid-cols-4 gap-16">
        <div className="rounded-md border border-border-default bg-bg-surface p-16">
          <div className="text-sm text-text-muted">Total Tickers</div>
          <div className="mt-8 text-3xl font-semibold text-text-primary">{summary.totalTickers}</div>
        </div>
        <div className="rounded-md border border-border-default bg-bg-surface p-16">
          <div className="text-sm text-text-muted">Active</div>
          <div className="mt-8 text-3xl font-semibold text-text-primary">{summary.active}</div>
        </div>
        <div className="rounded-md border border-border-default bg-bg-surface p-16">
          <div className="text-sm text-text-muted">Paused</div>
          <div className="mt-8 text-3xl font-semibold text-text-primary">{summary.paused}</div>
        </div>
        <div className="rounded-md border border-border-default bg-bg-surface p-16">
          <div className="text-sm text-text-muted">Errors</div>
          <div className="mt-8 text-3xl font-semibold text-text-primary">{summary.errors}</div>
        </div>
      </div>

      <div className="mb-6 flex items-center gap-3">
        {filterOptions.map((option) => (
          <button
            key={option.value}
            type="button"
            onClick={() => setFilter(option.value)}
            className={[
              "rounded px-4 py-2 text-sm transition-colors",
              filter === option.value
                ? "bg-blue-600 text-white hover:bg-blue-700"
                : "bg-slate-800 text-slate-300 hover:bg-slate-700"
            ].join(" ")}
          >
            {option.label}
          </button>
        ))}
      </div>

      <div className="overflow-hidden rounded-md border border-border-default bg-bg-surface">
        <table className="w-full border-collapse">
          <thead>
            <tr className="border-b border-border-subtle text-left text-sm text-text-muted">
              <th className="px-16 py-12 font-medium">Ticker</th>
              <th className="px-16 py-12 font-medium">Status</th>
              <th className="px-16 py-12 font-medium">News</th>
              <th className="px-16 py-12 font-medium">Filings</th>
              <th className="px-16 py-12 font-medium">Job Status</th>
              <th className="px-16 py-12 font-medium">Last Sync</th>
              <th className="px-16 py-12 font-medium">Signals</th>
              <th className="px-16 py-12 font-medium text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={8} className="px-16 py-24 text-center text-sm text-text-secondary">
                  Loading tickers...
                </td>
              </tr>
            ) : filteredItems.length === 0 ? (
              <tr>
                <td colSpan={8} className="px-16 py-24 text-center text-sm text-text-secondary">
                  No tickers found.
                </td>
              </tr>
            ) : (
              filteredItems.map((item) => (
                <tr key={item.symbol} className="border-b border-border-subtle last:border-b-0">
                  <td className="px-16 py-14">
                    <div className="text-2xl font-semibold text-text-primary">{item.symbol}</div>
                    <div className="text-sm text-text-muted">{item.name || item.exchange || "--"}</div>
                  </td>
                  <td className="px-16 py-14">
                    <span className={["inline-flex rounded border px-10 py-4 text-sm font-semibold", statusClass[item.status]].join(" ")}>
                      {item.status === "error" ? "Error" : item.status === "paused" ? "Paused" : "Active"}
                    </span>
                  </td>
                  <td className="px-16 py-14 text-sm text-text-secondary">{item.newsEnabled ? "Yes" : "No"}</td>
                  <td className="px-16 py-14 text-sm text-text-secondary">{item.filingsEnabled ? "Yes" : "No"}</td>
                  <td className={["px-16 py-14 text-sm font-medium", jobStatusClass[item.jobStatus] ?? "text-text-secondary"].join(" ")}>
                    {item.jobStatus === "running" ? "Running" : item.jobStatus === "failed" ? "Failed" : "Idle"}
                  </td>
                  <td className="px-16 py-14 text-sm text-text-secondary">{formatAgo(item.lastSyncAt)}</td>
                  <td className="px-16 py-14 text-sm font-semibold text-text-primary">{item.signalCount}</td>
                  <td className="px-16 py-14 text-right">
                    <button
                      type="button"
                      onClick={() => onDeleteTicker(item.symbol)}
                      className="rounded border border-semantic-negative/40 px-10 py-6 text-xs font-medium text-semantic-negative hover:bg-semantic-negative/10"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/65 px-16 py-24">
          <div className="w-full max-w-[640px] overflow-hidden rounded-md border border-border-default bg-bg-surface shadow-md">
            <div className="flex items-center justify-between border-b border-border-subtle px-20 py-16">
              <h2 className="text-2xl font-semibold text-text-primary">Add New Ticker</h2>
              <button
                type="button"
                onClick={() => setShowAddModal(false)}
                className="rounded px-8 py-4 text-xl leading-none text-text-muted transition-colors hover:bg-state-hover hover:text-text-primary"
                aria-label="Close"
              >
                ×
              </button>
            </div>

            <form className="flex flex-col gap-16 px-20 py-20" onSubmit={onSubmitAdd}>
              <label className="flex flex-col gap-8 text-sm font-medium text-text-secondary">
                Ticker Symbol *
                <input
                  value={newTicker.symbol}
                  onChange={(event) => setNewTicker((prev) => ({ ...prev, symbol: event.target.value.toUpperCase() }))}
                  className="h-48 rounded border border-border-default bg-bg-elevated px-12 text-base text-text-primary outline-none transition-colors focus:border-semantic-info"
                  placeholder="e.g., AAPL"
                  required
                />
              </label>

              <label className="flex flex-col gap-8 text-sm font-medium text-text-secondary">
                Company Name
                <input
                  value={newTicker.name}
                  onChange={(event) => setNewTicker((prev) => ({ ...prev, name: event.target.value }))}
                  className="h-48 rounded border border-border-default bg-bg-elevated px-12 text-base text-text-primary outline-none transition-colors focus:border-semantic-info"
                  placeholder="Auto-filled or enter manually"
                />
              </label>

              <label className="flex flex-col gap-8 text-sm font-medium text-text-secondary">
                Exchange
                <input
                  value={newTicker.exchange}
                  onChange={(event) => setNewTicker((prev) => ({ ...prev, exchange: event.target.value.toUpperCase() }))}
                  className="h-48 rounded border border-border-default bg-bg-elevated px-12 text-base text-text-primary outline-none transition-colors focus:border-semantic-info"
                  placeholder="NASDAQ"
                />
              </label>

              <div className="mt-8 grid grid-cols-2 gap-12">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="rounded bg-slate-800 px-12 py-10 text-base font-medium text-slate-200 transition-colors hover:bg-slate-700"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="rounded bg-blue-600 px-12 py-10 text-base font-semibold text-white transition-colors hover:bg-blue-700 disabled:opacity-60"
                >
                  {submitting ? "Adding..." : "Add Ticker"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
