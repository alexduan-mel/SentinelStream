import type { ReactNode } from "react";

import TopNav from "../components/TopNav";

interface AppLayoutProps {
  children: ReactNode;
}

export default function AppLayout({ children }: AppLayoutProps) {
  return (
    <div className="min-h-screen bg-bg-primary">
      <TopNav lastSync="18:38:54" />
      <main className="mx-auto w-full max-w-contentWide px-24 py-24">
        {children}
      </main>
    </div>
  );
}
