import { Navigate, Route, Routes } from "react-router-dom";

import MonitorPage from "../pages/Monitor";
import TickerPage from "../pages/Ticker";
import MarketPulsePage from "../pages/MarketPulse";
import SignalsPage from "../pages/Signals";
import TopicsPage from "../pages/Topics";
import BacktestPage from "../pages/Backtest";
import SystemPage from "../pages/System";
import SignalDetailPage from "../pages/SignalDetail";

export default function AppRouter() {
  return (
    <Routes>
      <Route path="/" element={<MonitorPage />} />
      <Route path="/monitor" element={<MonitorPage />} />
      <Route path="/tickers" element={<TickerPage />} />
      <Route path="/market-pulse" element={<MarketPulsePage />} />
      <Route path="/signal/:id" element={<SignalDetailPage />} />
      <Route path="/ticker/:symbol" element={<SignalDetailPage />} />
      <Route path="/signals" element={<SignalsPage />} />
      <Route path="/topics" element={<TopicsPage />} />
      <Route path="/backtest" element={<BacktestPage />} />
      <Route path="/system" element={<SystemPage />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
