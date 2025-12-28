// frontend/src/components/MetricsPanel.tsx
import React from "react";
import type { TradeSignalResponse } from "../lib/api";

interface Props {
  signal: TradeSignalResponse | null;
}

export const MetricsPanel: React.FC<Props> = ({ signal }) => {
  if (!signal) {
    return (
      <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4 text-sm text-slate-300">
        <h2 className="text-sm font-semibold text-slate-100 mb-1">
          Indicator snapshot
        </h2>
        <p className="text-xs text-slate-400">
          Run an analysis to see EMA, RSI, and other readings for your chosen
          coin and timeframe.
        </p>
      </div>
    );
  }

  const ctx = signal.analysis || {};
  const items: { label: string; value: number | null | undefined }[] = [
    { label: "Close", value: signal.analysis.latest_price },
    { label: "EMA 20", value: ctx.ema20 },
    { label: "EMA 50", value: ctx.ema50 },
    { label: "EMA 200", value: ctx.ema200 },
    { label: "RSI 14", value: ctx.rsi14 },
  ];

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4 text-sm">
      <h2 className="text-sm font-semibold text-slate-100 mb-2">
        Indicator snapshot
      </h2>
      <div className="grid grid-cols-2 gap-2 text-xs">
        {items.map((item) => (
          <div
            key={item.label}
            className="flex items-center justify-between rounded-xl bg-slate-900/80 px-3 py-2"
          >
            <span className="text-slate-400">{item.label}</span>
            <span className="text-slate-100">
              {typeof item.value === "number" ? item.value.toFixed(2) : "—"}
            </span>
          </div>
        ))}
      </div>
      <p className="mt-3 text-[11px] text-slate-500">
        Indicators come from recent candles and help the engine decide if it is
        safer to enter or to stay out of the market.
      </p>
    </div>
  );
};
