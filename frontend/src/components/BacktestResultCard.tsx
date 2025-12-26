import React from "react";
import type { BacktestResponse } from "../lib/api";

interface Props {
  result: BacktestResponse;
}

const formatNumber = (value: number, decimals = 1) => {
  if (!Number.isFinite(value)) return "-";
  return value.toFixed(decimals);
};

const summarizeOutcome = (result: BacktestResponse) => {
  if (result.trades_count === 0) return "No trades were triggered in this window.";
  if (result.total_return_pct > 5 && result.win_rate > 55) {
    return "Over this period, the strategy was generally profitable.";
  }
  if (result.total_return_pct < -5) {
    return "Price action was rough for this setup and stayed negative.";
  }
  return "Results were mixed, suggesting choppy conditions.";
};

export const BacktestResultCard: React.FC<Props> = ({ result }) => {
  const metrics = [
    { label: "Win rate", value: `${formatNumber(result.win_rate)}%` },
    { label: "Total return", value: `${formatNumber(result.total_return_pct)}%` },
    { label: "Max drawdown", value: `${formatNumber(result.max_drawdown_pct)}%` },
    { label: "Profit factor", value: formatNumber(result.profit_factor, 2) },
    { label: "# trades", value: result.trades_count },
  ];

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4 space-y-3">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-sm font-semibold text-slate-100">Backtest result</h2>
          <p className="text-xs text-slate-400">
            {result.symbol} · {result.timeframe} · {result.strategy_name}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
        {metrics.map((metric) => (
          <div
            key={metric.label}
            className="rounded-xl border border-slate-800 bg-slate-900/80 px-3 py-2"
          >
            <p className="text-[11px] uppercase tracking-wide text-slate-500">
              {metric.label}
            </p>
            <p className="text-lg font-semibold text-slate-100">{metric.value}</p>
          </div>
        ))}
      </div>

      <p className="text-xs text-slate-300">{summarizeOutcome(result)}</p>
    </div>
  );
};
