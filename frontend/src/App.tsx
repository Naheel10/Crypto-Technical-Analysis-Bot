import React, { useState } from "react";
import { Layout } from "./components/Layout";
import { SignalForm } from "./components/SignalForm";
import { SignalCard } from "./components/SignalCard";
import { MetricsPanel } from "./components/MetricsPanel";
import type { TradeSignalResponse } from "./lib/api";

const App: React.FC = () => {
  const [signal, setSignal] = useState<TradeSignalResponse | null>(null);

  return (
    <Layout>
      <div className="grid gap-6 lg:grid-cols-[2fr,1.2fr]">
        <div className="space-y-4">
          <SignalForm onSignalLoaded={setSignal} />
          {signal && <SignalCard signal={signal} />}
        </div>

        <div className="space-y-4">
          <MetricsPanel signal={signal} />
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
              <span className="font-semibold">NO&nbsp;TRADE</span> with a plain
              English explanation.
            </p>
            <p className="text-slate-400 text-xs">
              This is an educational decision-support tool. It does not connect
              to your wallet and does not guarantee profit or protect you from
              loss.
            </p>
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default App;
