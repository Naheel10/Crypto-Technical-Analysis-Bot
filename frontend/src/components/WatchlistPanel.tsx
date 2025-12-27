import React, { useMemo, useState } from "react";
import {
  type SignalSummary,
  scanSignals,
  type TradeAction,
} from "../lib/api";
import { useWatchlist } from "../hooks/useWatchlist";
import { LoadingSpinner } from "./LoadingSpinner";

interface Props {
  onSelectSymbol?: (symbol: string, timeframe: string) => void;
  enabledStrategies?: string[];
}

const TIMEFRAME_OPTIONS = ["15m", "1h", "4h", "1d"];

const actionBadgeClass: Record<TradeAction, string> = {
  BUY: "bg-emerald-500/20 text-emerald-200 border border-emerald-500/40",
  SELL: "bg-rose-500/20 text-rose-200 border border-rose-500/40",
  NO_TRADE: "bg-slate-700 text-slate-200 border border-slate-600",
};

export const WatchlistPanel: React.FC<Props> = ({
  onSelectSymbol,
  enabledStrategies,
}) => {
  const { watchlist, addSymbol, removeSymbol } = useWatchlist();
  const [symbolInput, setSymbolInput] = useState("");
  const [timeframe, setTimeframe] = useState("1h");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<SignalSummary[]>([]);

  const sortedResults = useMemo(
    () =>
      [...results].sort((a, b) => a.symbol.localeCompare(b.symbol)),
    [results],
  );

  const handleAdd = () => {
    addSymbol(symbolInput);
    setSymbolInput("");
  };

  const handleScan = async () => {
    if (watchlist.length === 0) {
      setError("Add at least one symbol to scan.");
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const data = await scanSignals(
        {
          symbols: watchlist,
          timeframe,
          demo: false,
        },
        enabledStrategies,
      );
      setResults(data);
    } catch (err) {
      console.error(err);
      setError((err as Error).message || "Failed to scan watchlist");
    } finally {
      setLoading(false);
    }
  };

  const confidenceDisplay = (value: number) => `${(value * 100).toFixed(0)}%`;

  return (
    <div className="space-y-4">
      <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
        <div className="flex items-center justify-between gap-3">
          <div>
            <h2 className="text-sm font-semibold text-slate-100">Watchlist</h2>
            <p className="text-xs text-slate-400">
              Save your favorite pairs and scan them in one click.
            </p>
          </div>
          {loading && <LoadingSpinner />}
        </div>

        <div className="mt-4 grid gap-3 md:grid-cols-[2fr,1fr,auto]">
          <div className="flex flex-col gap-1">
            <label className="text-xs text-slate-400">Symbol</label>
            <input
              type="text"
              value={symbolInput}
              onChange={(e) => setSymbolInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  e.preventDefault();
                  handleAdd();
                }
              }}
              placeholder="BTC/USDT"
              className="rounded-xl border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100 focus:outline-none focus:ring-2 focus:ring-emerald-500"
            />
          </div>

          <div className="flex flex-col gap-1">
            <label className="text-xs text-slate-400">Timeframe</label>
            <select
              value={timeframe}
              onChange={(e) => setTimeframe(e.target.value)}
              className="rounded-xl border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100 focus:outline-none focus:ring-2 focus:ring-emerald-500"
            >
              {TIMEFRAME_OPTIONS.map((tf) => (
                <option key={tf}>{tf}</option>
              ))}
            </select>
          </div>

          <div className="flex items-end">
            <button
              type="button"
              onClick={handleAdd}
              className="w-full rounded-xl bg-emerald-500 px-4 py-2 text-sm font-semibold text-slate-950 hover:bg-emerald-400"
            >
              Add to watchlist
            </button>
          </div>
        </div>

        <div className="mt-4 flex flex-wrap gap-2 text-xs text-slate-100">
          {watchlist.length === 0 ? (
            <span className="text-slate-400">No symbols yet. Add some to track.</span>
          ) : (
            watchlist.map((sym) => (
              <span
                key={sym}
                className="inline-flex items-center gap-2 rounded-full border border-slate-700 bg-slate-800/80 px-3 py-1"
              >
                {sym}
                <button
                  type="button"
                  onClick={() => removeSymbol(sym)}
                  className="text-slate-400 hover:text-red-300"
                  aria-label={`Remove ${sym}`}
                >
                  ×
                </button>
              </span>
            ))
          )}
        </div>

        {error && (
          <div className="mt-3 rounded-xl border border-red-500/60 bg-red-500/10 px-3 py-2 text-xs text-red-200">
            {error}
          </div>
        )}

        <div className="mt-4 flex justify-end">
          <button
            type="button"
            onClick={handleScan}
            disabled={loading}
            className="inline-flex items-center rounded-xl bg-emerald-500 px-4 py-2 text-sm font-semibold text-slate-950 hover:bg-emerald-400 disabled:opacity-60"
          >
            Scan watchlist
          </button>
        </div>
      </div>

      <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4">
        <div className="mb-3 flex items-center justify-between">
          <div>
            <h3 className="text-sm font-semibold text-slate-100">Scan results</h3>
            <p className="text-xs text-slate-400">
              Click a row to load that symbol into the Signal tab.
            </p>
          </div>
          {loading && <LoadingSpinner />}
        </div>

        {sortedResults.length === 0 ? (
          <p className="text-sm text-slate-400">Run a scan to see signals here.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm text-slate-200">
              <thead>
                <tr className="border-b border-slate-800 text-xs uppercase text-slate-400">
                  <th className="px-3 py-2">Symbol</th>
                  <th className="px-3 py-2">Timeframe</th>
                  <th className="px-3 py-2">Trend regime</th>
                  <th className="px-3 py-2">Action</th>
                  <th className="px-3 py-2">Strategy</th>
                  <th className="px-3 py-2">Risk</th>
                  <th className="px-3 py-2">Confidence</th>
                </tr>
              </thead>
              <tbody>
                {sortedResults.map((item) => (
                  <tr
                    key={`${item.symbol}-${item.timeframe}`}
                    onClick={() => onSelectSymbol?.(item.symbol, item.timeframe)}
                    className="cursor-pointer border-b border-slate-800/60 transition hover:bg-slate-800/60"
                  >
                    <td className="px-3 py-2 font-semibold">{item.symbol}</td>
                    <td className="px-3 py-2">{item.timeframe}</td>
                    <td className="px-3 py-2 text-xs text-slate-300">{item.regime}</td>
                    <td className="px-3 py-2">
                      <span
                        className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold ${actionBadgeClass[item.action]}`}
                      >
                        {item.action.replace("_", " ")}
                      </span>
                    </td>
                    <td className="px-3 py-2 text-xs text-slate-300">
                      {item.strategy_name}
                    </td>
                    <td className="px-3 py-2 text-xs text-slate-300">
                      {item.risk_rating}
                    </td>
                    <td className="px-3 py-2 text-xs text-slate-300">
                      {confidenceDisplay(item.confidence_score)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
