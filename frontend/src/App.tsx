import React, { useState } from "react";
import { Layout } from "./components/Layout";
import { SignalForm } from "./components/SignalForm";
import { SignalCard } from "./components/SignalCard";
import { MetricsPanel } from "./components/MetricsPanel";
import { BacktestForm } from "./components/BacktestForm";
import { BacktestResultCard } from "./components/BacktestResultCard";
import { ChartPanel } from "./components/ChartPanel";
import { RecentSignalsPanel } from "./components/RecentSignalsPanel";
import { RiskPanel } from "./components/RiskPanel";
import { BacktestHistoryPanel } from "./components/BacktestHistoryPanel";
import type { BacktestResponse, TradeSignalResponse } from "./lib/api";

const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<"live" | "backtest">("live");
  const [signal, setSignal] = useState<TradeSignalResponse | null>(null);
  const [backtestResult, setBacktestResult] =
    useState<BacktestResponse | null>(null);
  const [selectedSymbol, setSelectedSymbol] = useState("BTC/USDT");
  const [selectedTimeframe, setSelectedTimeframe] = useState("1h");

  return (
    <Layout>
      <div className="mb-4 flex gap-2 rounded-xl bg-slate-900/80 p-1 text-sm">
        <button
          onClick={() => setActiveTab("live")}
          className={`flex-1 rounded-lg px-3 py-2 font-semibold transition ${
            activeTab === "live"
              ? "bg-emerald-500 text-slate-950"
              : "text-slate-200 hover:bg-slate-800"
          }`}
        >
          Live Signal
        </button>
        <button
          onClick={() => setActiveTab("backtest")}
          className={`flex-1 rounded-lg px-3 py-2 font-semibold transition ${
            activeTab === "backtest"
              ? "bg-emerald-500 text-slate-950"
              : "text-slate-200 hover:bg-slate-800"
          }`}
        >
          Backtest
        </button>
      </div>

      {activeTab === "live" ? (
        <div className="grid gap-6 lg:grid-cols-[2fr,1.2fr]">
          <div className="space-y-4">
            <SignalForm
              onSignalLoaded={setSignal}
              onSelectionChange={({ symbol, timeframe }) => {
                setSelectedSymbol(symbol);
                setSelectedTimeframe(timeframe);
              }}
            />
            {signal && <SignalCard signal={signal} />}
            <ChartPanel
              symbol={selectedSymbol}
              timeframe={selectedTimeframe}
              signal={signal}
            />
            <RecentSignalsPanel limit={15} />
          </div>

          <div className="space-y-4">
            <MetricsPanel signal={signal} />
            <RiskPanel signal={signal} />
            <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4 text-sm space-y-2">
              <h2 className="text-sm font-semibold text-slate-100">
                How to use this bot
              </h2>
              <p className="text-slate-300">
                1. Choose a coin and timeframe. The bot scans the chart using
                predefined technical analysis strategies.
              </p>
              <p className="text-slate-300">
                2. It labels the market regime and outputs{" "}
                <span className="font-semibold">BUY</span>,{" "}
                <span className="font-semibold">SELL</span>, or{" "}
                <span className="font-semibold">NO&nbsp;TRADE</span> with a
                plain English explanation.
              </p>
              <p className="text-slate-400 text-xs">
                This is an educational decision-support tool. It does not
                connect to your wallet and does not guarantee profit or protect
                you from loss.
              </p>
            </div>
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="grid gap-6 lg:grid-cols-[2fr,1.2fr]">
            <div className="space-y-4">
              <BacktestForm onBacktestLoaded={setBacktestResult} />
            </div>
            <div className="space-y-4">
              {backtestResult && <BacktestResultCard result={backtestResult} />}
            </div>
          </div>

          <BacktestHistoryPanel limit={15} />
        </div>
      )}
    </Layout>
  );
};

export default App;
