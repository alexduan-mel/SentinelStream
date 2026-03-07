import { NavLink } from "react-router-dom";

const navItems = [
  { label: "Monitor", to: "/" },
  { label: "Signals", to: "/signals" },
  { label: "Topics", to: "/topics" },
  { label: "Backtest", to: "/backtest" },
  { label: "System", to: "/system" }
];

interface TopNavProps {
  lastSync: string;
}

function NavIcon() {
  return (
    <svg
      width="16"
      height="16"
      viewBox="0 0 16 16"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className="text-text-muted"
    >
      <path
        d="M2 8h12M8 2v12"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
      />
    </svg>
  );
}

export default function TopNav({ lastSync }: TopNavProps) {
  return (
    <header className="h-64 border-b border-border-subtle bg-bg-surface">
      <div className="mx-auto flex h-full w-full max-w-contentWide items-center justify-between px-24">
        <div className="flex items-center gap-16">
          <div className="flex items-center gap-8">
            <div className="flex h-24 w-24 items-center justify-center rounded-md bg-semantic-info text-text-inverse">
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
                    "flex items-center gap-8 rounded-md px-12 py-8 text-label transition",
                    isActive ? "bg-state-selected text-text-primary" : "text-text-secondary hover:bg-state-hover"
                  ].join(" ")
                }
              >
                <NavIcon />
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
