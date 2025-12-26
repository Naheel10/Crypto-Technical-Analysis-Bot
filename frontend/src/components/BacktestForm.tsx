import React, { useMemo, useState } from "react";
import { fetchBacktest, type BacktestResponse } from "../lib/api";
import { LoadingSpinner } from "./LoadingSpinner";

interface Props {
  onBacktestLoaded: (result: BacktestResponse | null) => void;
}

const DEFAULT_SYMBOLS = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "XRP/USDT"];
const DEFAULT_TIMEFRAMES = ["1h", "4h", "1d"];
const STRATEGIES = [
  { label: "Trend Continuation", value: "TrendContinuation" },
  { label: "Range Reversion", value: "RangeReversion" },
];

function toInputDateTime(date: Date) {
  const pad = (n: number) => `${n}`.padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

export const BacktestForm: React.FC<Props> = ({ onBacktestLoaded }) => {
  const defaultRange = useMemo(() => {
    const end = new Date();
    const start = new Date();
    start.setDate(end.getDate() - 30);
    return { start: toInputDateTime(start), end: toInputDateTime(end) };
  }, []);

  const [symbol, setSymbol] = useState("BTC/USDT");
  const [timeframe, setTimeframe] = useState("1h");
  const [strategy, setStrategy] = useState("TrendContinuation");
  const [startDate, setStartDate] = useState(defaultRange.start);
  const [endDate, setEndDate] = useState(defaultRange.end);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    onBacktestLoaded(null);

    try {
      const data = await fetchBacktest({
        symbol,
        timeframe,
        strategy,
        start: new Date(startDate).toISOString(),
        end: new Date(endDate).toISOString(),
      });
      onBacktestLoaded(data);
    } catch (err) {
      console.error(err);
      setError("Backtest failed. Check dates and try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4 flex flex-col gap-4"
    >
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-sm font-semibold text-slate-100">Backtest</h2>
          <p className="text-xs text-slate-400">
            Run the chosen strategy on stored candles for a date range.
          </p>
        </div>
        {loading && <LoadingSpinner />}
      </div>

      <div className="grid gap-3 md:grid-cols-2">
        <div className="flex flex-col gap-1">
          <label className="text-xs text-slate-400">Symbol</label>
          <select
            className="rounded-xl border border-slate-700 bg-slate-900 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
            value={symbol}
            onChange={(e) => setSymbol(e.target.value)}
          >
            {DEFAULT_SYMBOLS.map((s) => (
              <option key={s}>{s}</option>
            ))}
          </select>
        </div>

        <div className="flex flex-col gap-1">
          <label className="text-xs text-slate-400">Timeframe</label>
          <select
            className="rounded-xl border border-slate-700 bg-slate-900 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
            value={timeframe}
            onChange={(e) => setTimeframe(e.target.value)}
          >
            {DEFAULT_TIMEFRAMES.map((tf) => (
              <option key={tf}>{tf}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="grid gap-3 md:grid-cols-2">
        <div className="flex flex-col gap-1">
          <label className="text-xs text-slate-400">Strategy</label>
          <select
            className="rounded-xl border border-slate-700 bg-slate-900 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
            value={strategy}
            onChange={(e) => setStrategy(e.target.value)}
          >
            {STRATEGIES.map((s) => (
              <option key={s.value} value={s.value}>
                {s.label}
              </option>
            ))}
          </select>
        </div>

        <div className="flex flex-col gap-1">
          <label className="text-xs text-slate-400">Start</label>
          <input
            type="datetime-local"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            className="rounded-xl border border-slate-700 bg-slate-900 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
          />
        </div>
      </div>

      <div className="grid gap-3 md:grid-cols-2">
        <div className="flex flex-col gap-1">
          <label className="text-xs text-slate-400">End</label>
          <input
            type="datetime-local"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            className="rounded-xl border border-slate-700 bg-slate-900 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
          />
        </div>

        <div className="flex flex-col gap-1 justify-end">
          <button
            type="submit"
            disabled={loading}
            className="inline-flex items-center justify-center rounded-xl bg-emerald-500 px-4 py-2 text-sm font-semibold text-slate-950 hover:bg-emerald-400 disabled:opacity-60"
          >
            Run Backtest
          </button>
        </div>
      </div>

      {error && (
        <div className="rounded-xl border border-red-500/60 bg-red-500/10 px-3 py-2 text-xs text-red-200">
          {error}
        </div>
      )}
    </form>
  );
};
