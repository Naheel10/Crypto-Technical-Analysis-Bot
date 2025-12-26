// frontend/src/components/SignalCard.tsx
import React from "react";
import type { TradeSignalResponse } from "../lib/api";

interface Props {
  signal: TradeSignalResponse;
}

const actionColor: Record<string, string> = {
  BUY: "bg-emerald-500 text-emerald-950",
  SELL: "bg-rose-500 text-rose-950",
  NO_TRADE: "bg-slate-600 text-slate-100",
};

export const SignalCard: React.FC<Props> = ({ signal }) => {
  const colorClass =
    actionColor[signal.action] || "bg-slate-600 text-slate-100";

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4 space-y-3">
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-3">
          <div
            className={`px-3 py-1 rounded-full text-xs font-semibold ${colorClass}`}
          >
            {signal.action}
          </div>
          <div>
            <div className="text-sm font-semibold text-slate-100">
              {signal.symbol} • {signal.timeframe}
            </div>
            <div className="text-xs text-slate-400">
              Strategy: {signal.strategy_name}
            </div>
          </div>
        </div>
        <div className="text-xs text-slate-400 text-right">
          Regime:{" "}
          <span className="font-semibold text-slate-200">
            {signal.regime}
          </span>
          <br />
          Risk:{" "}
          <span
            className={
              signal.risk_rating === "LOW"
                ? "text-emerald-400"
                : signal.risk_rating === "MEDIUM"
                ? "text-amber-300"
                : "text-rose-300"
            }
          >
            {signal.risk_rating}
          </span>
        </div>
      </div>

      {signal.simple_explanation && (
        <p className="text-sm text-slate-200 leading-relaxed">
          {signal.simple_explanation}
        </p>
      )}

      <div className="grid gap-3 md:grid-cols-3 text-xs text-slate-300">
        <div>
          <div className="text-slate-400 mb-1">Entry zone</div>
          {signal.entry_zone ? (
            <div>
              {signal.entry_zone[0].toFixed(2)} –{" "}
              {signal.entry_zone[1].toFixed(2)}
            </div>
          ) : (
            <div className="text-slate-500">Not specified</div>
          )}
        </div>
        <div>
          <div className="text-slate-400 mb-1">Stop loss</div>
          {signal.stop_loss ? (
            <div>{signal.stop_loss.toFixed(2)}</div>
          ) : (
            <div className="text-slate-500">Not specified</div>
          )}
        </div>
        <div>
          <div className="text-slate-400 mb-1">Take profits</div>
          {signal.take_profits && signal.take_profits.length > 0 ? (
            <div className="flex flex-wrap gap-1">
              {signal.take_profits.map((tp, idx) => (
                <span
                  key={idx}
                  className="inline-flex items-center rounded-full bg-slate-800 px-2 py-0.5"
                >
                  TP{idx + 1}: {tp.toFixed(2)}
                </span>
              ))}
            </div>
          ) : (
            <div className="text-slate-500">Not specified</div>
          )}
        </div>
      </div>

      <p className="text-[11px] text-slate-500">
        This is an educational, simulated signal. It is not financial advice and
        does not guarantee any outcome.
      </p>
    </div>
  );
};
