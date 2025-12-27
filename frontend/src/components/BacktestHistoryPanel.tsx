import { useEffect, useState } from "react";
import {
  type BacktestHistoryItem,
  fetchRecentBacktests,
} from "../lib/api";

const formatDate = (value: string) =>
  new Date(value).toLocaleString(undefined, {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });

const percentText = (value: number, digits = 1) => `${value.toFixed(digits)}%`;

const metricClass = (value: number, positiveThreshold = 0) =>
  value > positiveThreshold
    ? "text-emerald-300"
    : value < 0
    ? "text-rose-300"
    : "text-slate-200";

export const BacktestHistoryPanel: React.FC<{ limit?: number }> = ({
  limit = 15,
}) => {
  const [items, setItems] = useState<BacktestHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    setLoading(true);
    fetchRecentBacktests(limit)
      .then((data) => {
        if (mounted) {
          setItems(data);
          setError(null);
        }
      })
      .catch(() => {
        if (mounted) setError("Unable to load backtest history");
      })
      .finally(() => {
        if (mounted) setLoading(false);
      });

    return () => {
      mounted = false;
    };
  }, [limit]);

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4 shadow-lg">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-sm font-semibold text-slate-100">Recent Backtests</h2>
        {loading && (
          <span className="text-xs text-slate-400">Loading history...</span>
        )}
        {error && (
          <span className="text-xs text-rose-300" role="alert">
            {error}
          </span>
        )}
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full text-left text-sm">
          <thead>
            <tr className="text-slate-400">
              <th className="pb-2 pr-4 font-semibold">Date</th>
              <th className="pb-2 pr-4 font-semibold">Symbol</th>
              <th className="pb-2 pr-4 font-semibold">Timeframe</th>
              <th className="pb-2 pr-4 font-semibold">Strategy</th>
              <th className="pb-2 pr-4 text-right font-semibold">Win rate</th>
              <th className="pb-2 pr-4 text-right font-semibold">Total return</th>
              <th className="pb-2 pr-4 text-right font-semibold">Max drawdown</th>
              <th className="pb-2 pr-4 text-right font-semibold">Profit factor</th>
              <th className="pb-2 text-right font-semibold">Trades</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/80">
            {items.length === 0 && !loading ? (
              <tr>
                <td colSpan={9} className="py-3 text-center text-slate-400">
                  No backtests logged yet.
                </td>
              </tr>
            ) : (
              items.map((item) => (
                <tr key={item.id} className="text-slate-100">
                  <td className="py-2 pr-4 text-slate-200">
                    {formatDate(item.created_at)}
                  </td>
                  <td className="py-2 pr-4">{item.symbol}</td>
                  <td className="py-2 pr-4">{item.timeframe}</td>
                  <td className="py-2 pr-4">{item.strategy_name}</td>
                  <td className={`py-2 pr-4 text-right ${metricClass(item.win_rate)}`}>
                    {percentText(item.win_rate)}
                  </td>
                  <td
                    className={`py-2 pr-4 text-right ${metricClass(
                      item.total_return_pct,
                    )}`}
                  >
                    {percentText(item.total_return_pct, 1)}
                  </td>
                  <td className={`py-2 pr-4 text-right ${metricClass(-item.max_drawdown_pct)}`}>
                    {percentText(item.max_drawdown_pct, 1)}
                  </td>
                  <td
                    className={`py-2 pr-4 text-right ${metricClass(
                      item.profit_factor,
                      1,
                    )}`}
                  >
                    {item.profit_factor === Infinity
                      ? "∞"
                      : item.profit_factor.toFixed(2)}
                  </td>
                  <td className="py-2 text-right text-slate-200">
                    {item.trades_count}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
