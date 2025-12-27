import React, { useEffect, useState } from "react";
import { fetchRecentSignals, type SignalHistoryItem } from "../lib/api";
import { LoadingSpinner } from "./LoadingSpinner";

interface Props {
  limit?: number;
}

const actionBadgeClasses: Record<string, string> = {
  BUY: "bg-emerald-500/20 text-emerald-200 border-emerald-500/60",
  SELL: "bg-rose-500/20 text-rose-100 border-rose-500/60",
  NO_TRADE: "bg-slate-800 text-slate-200 border-slate-600",
};

export const RecentSignalsPanel: React.FC<Props> = ({ limit = 20 }) => {
  const [items, setItems] = useState<SignalHistoryItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await fetchRecentSignals(limit);
        setItems(data);
      } catch (err) {
        console.error(err);
        setError("Unable to load recent signals");
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [limit]);

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4 text-sm">
      <div className="mb-3 flex items-center justify-between">
        <div>
          <h2 className="text-sm font-semibold text-slate-100">Recent signals</h2>
          <p className="text-xs text-slate-400">
            Latest decisions saved whenever you run an analysis.
          </p>
        </div>
        {loading && <LoadingSpinner />}
      </div>

      {error && (
        <div className="rounded-xl border border-rose-500/60 bg-rose-500/10 px-3 py-2 text-xs text-rose-100">
          {error}
        </div>
      )}

      {!loading && !error && items.length === 0 && (
        <p className="text-xs text-slate-400">
          No signals logged yet. Run an analysis to start building history.
        </p>
      )}

      {items.length > 0 && (
        <div className="overflow-x-auto">
          <table className="min-w-full text-left text-xs text-slate-200">
            <thead className="text-[11px] uppercase text-slate-500">
              <tr>
                <th className="py-2 pr-4">Time</th>
                <th className="py-2 pr-4">Symbol</th>
                <th className="py-2 pr-4">Timeframe</th>
                <th className="py-2 pr-4">Action</th>
                <th className="py-2 pr-4">Strategy</th>
                <th className="py-2 pr-4">Risk</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/80">
              {items.map((item) => {
                const date = new Date(item.created_at);
                const badgeClass =
                  actionBadgeClasses[item.action] || actionBadgeClasses.NO_TRADE;
                return (
                  <tr key={item.id}>
                    <td className="py-2 pr-4 text-slate-300">
                      {date.toLocaleString(undefined, {
                        year: "numeric",
                        month: "2-digit",
                        day: "2-digit",
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </td>
                    <td className="py-2 pr-4 font-semibold text-slate-100">
                      {item.symbol}
                    </td>
                    <td className="py-2 pr-4 text-slate-300">{item.timeframe}</td>
                    <td className="py-2 pr-4">
                      <span
                        className={`inline-flex items-center rounded-full border px-2 py-0.5 text-[11px] font-semibold ${badgeClass}`}
                      >
                        {item.action.replace("_", " ")}
                      </span>
                    </td>
                    <td className="py-2 pr-4 text-slate-300">{item.strategy_name}</td>
                    <td className="py-2 pr-4 text-slate-300">{item.risk_rating}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

