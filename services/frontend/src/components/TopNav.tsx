import { NavLink } from "react-router-dom";

const navItems = [
  { label: "Monitor", to: "/", icon: "monitor" },
  { label: "Ticker", to: "/tickers", icon: "ticker" },
  { label: "Market Pulse", to: "/market-pulse", icon: "pulse" },
  { label: "Signals", to: "/signals", icon: "signals" },
  { label: "Topics", to: "/topics", icon: "topics" },
  { label: "Backtest", to: "/backtest", icon: "backtest" },
  { label: "System", to: "/system", icon: "system" }
];

interface TopNavProps {
  lastSync: string;
}

function NavIcon({ name }: { name: string }) {
  if (name === "monitor") {
    return (
      <svg
        width="14"
        height="14"
        viewBox="0 0 16 16"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="text-text-muted"
      >
        <rect x="2.5" y="3" width="11" height="8.5" rx="1.5" stroke="currentColor" strokeWidth="1.2" />
        <path d="M6 13h4" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" />
      </svg>
    );
  }
  if (name === "pulse") {
    return (
      <svg
        width="14"
        height="14"
        viewBox="0 0 16 16"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="text-text-muted"
      >
        <path
          d="M1.5 8h3l2-3 3 6 2-3h3"
          stroke="currentColor"
          strokeWidth="1.2"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    );
  }
  if (name === "ticker") {
    return (
      <svg
        width="14"
        height="14"
        viewBox="0 0 16 16"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="text-text-muted"
      >
        <rect x="2.5" y="2.5" width="11" height="11" rx="1.5" stroke="currentColor" strokeWidth="1.2" />
        <path d="M5 6h6M5 8.5h6M5 11h3" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" />
      </svg>
    );
  }
  if (name === "signals") {
    return (
      <svg
        width="14"
        height="14"
        viewBox="0 0 16 16"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="text-text-muted"
      >
        <path d="M8 2.5v11" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" />
        <path d="M5 6l3-3 3 3" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" />
      </svg>
    );
  }
  if (name === "topics") {
    return (
      <svg
        width="14"
        height="14"
        viewBox="0 0 16 16"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="text-text-muted"
      >
        <rect x="2.5" y="2.5" width="11" height="4" rx="1" stroke="currentColor" strokeWidth="1.2" />
        <rect x="2.5" y="9.5" width="11" height="4" rx="1" stroke="currentColor" strokeWidth="1.2" />
      </svg>
    );
  }
  if (name === "backtest") {
    return (
      <svg
        width="14"
        height="14"
        viewBox="0 0 16 16"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="text-text-muted"
      >
        <path d="M2.5 11.5l3-4 2 2 4-5" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" />
        <path d="M2.5 13.5h11" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" />
      </svg>
    );
  }
  return (
    <svg
      width="14"
      height="14"
      viewBox="0 0 16 16"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className="text-text-muted"
    >
      <circle cx="8" cy="8" r="4.5" stroke="currentColor" strokeWidth="1.2" />
      <path d="M8 5.5v2.5l2 1" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" />
    </svg>
  );
}

function SystemIcon() {
  return (
    <svg
      width="14"
      height="14"
      viewBox="0 0 16 16"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className="text-text-muted"
    >
      <path d="M6.5 2.5h3l.5 2 1.5.5v3l-1.5.5-.5 2h-3l-.5-2-1.5-.5v-3l1.5-.5.5-2z" stroke="currentColor" strokeWidth="1.1" />
      <circle cx="8" cy="8" r="1.5" stroke="currentColor" strokeWidth="1.1" />
    </svg>
  );
}

export default function TopNav({ lastSync }: TopNavProps) {
  return (
    <header className="h-64 border-b border-border-subtle bg-bg-surface">
      <div className="mx-auto flex h-full w-full max-w-contentWide items-center justify-between px-24">
        <div className="flex items-center gap-16">
          <div className="flex items-center gap-8">
            <div className="flex h-24 w-24 items-center justify-center rounded bg-semantic-info text-text-inverse">
              S
            </div>
            <span className="text-h3">MarketSentinel</span>
          </div>
          <nav className="flex items-center gap-8">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === "/"}
                className={({ isActive }) =>
                  [
                    "flex items-center gap-8 rounded px-12 py-8 text-label transition",
                    isActive ? "bg-state-selected text-text-primary" : "text-text-secondary hover:bg-state-hover"
                  ].join(" ")
                }
              >
                {item.icon === "system" ? <SystemIcon /> : <NavIcon name={item.icon} />}
                {item.label}
              </NavLink>
            ))}
          </nav>
        </div>
        <div className="text-caption text-text-muted">Last sync: {lastSync}</div>
      </div>
    </header>
  );
}
