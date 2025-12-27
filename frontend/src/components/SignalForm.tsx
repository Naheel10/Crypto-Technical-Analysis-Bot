// frontend/src/components/SignalForm.tsx
import React, { useEffect, useState } from "react";
import { fetchSignal, type TradeSignalResponse } from "../lib/api";
import { LoadingSpinner } from "./LoadingSpinner";

interface Props {
  onSignalLoaded: (signal: TradeSignalResponse | null) => void;
  onSelectionChange?: (selection: { symbol: string; timeframe: string }) => void;
  selectedSymbol?: string;
  selectedTimeframe?: string;
  enabledStrategies?: string[];
}

const DEFAULT_SYMBOLS = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "XRP/USDT"];
const DEFAULT_TIMEFRAMES = ["15m", "1h", "4h", "1d"];

export const SignalForm: React.FC<Props> = ({
  onSignalLoaded,
  onSelectionChange,
  selectedSymbol,
  selectedTimeframe,
  enabledStrategies,
}) => {
  const [symbol, setSymbol] = useState(selectedSymbol ?? "BTC/USDT");
  const [timeframe, setTimeframe] = useState(selectedTimeframe ?? "1h");
  const [demo, setDemo] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    onSelectionChange?.({ symbol, timeframe });
  }, []);

  useEffect(() => {
    if (selectedSymbol && selectedSymbol !== symbol) {
      setSymbol(selectedSymbol);
      onSelectionChange?.({ symbol: selectedSymbol, timeframe });
    }
  }, [selectedSymbol]);

  useEffect(() => {
    if (selectedTimeframe && selectedTimeframe !== timeframe) {
      setTimeframe(selectedTimeframe);
      onSelectionChange?.({ symbol, timeframe: selectedTimeframe });
    }
  }, [selectedTimeframe]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    onSignalLoaded(null);

    try {
      const data = await fetchSignal({
        symbol,
        timeframe,
        demo,
        enabledStrategies,
      });
      onSignalLoaded(data);
    } catch (err) {
      console.error(err);
      setError("Failed to fetch signal. Is the backend running?");
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
          <h2 className="text-sm font-semibold text-slate-100">
            Signal Dashboard
          </h2>
          <p className="text-xs text-slate-400">
            Pick a coin and timeframe. The bot scans for a beginner-friendly
            setup.
          </p>
        </div>
        {loading && <LoadingSpinner />}
      </div>

      <div className="grid gap-3 md:grid-cols-3">
        <div className="flex flex-col gap-1">
          <label className="text-xs text-slate-400">Symbol</label>
          <select
            className="rounded-xl border border-slate-700 bg-slate-900 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
            value={symbol}
          onChange={(e) => {
            setSymbol(e.target.value);
            onSelectionChange?.({ symbol: e.target.value, timeframe });
          }}
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
          onChange={(e) => {
            setTimeframe(e.target.value);
            onSelectionChange?.({ symbol, timeframe: e.target.value });
          }}
          >
            {DEFAULT_TIMEFRAMES.map((tf) => (
              <option key={tf}>{tf}</option>
            ))}
          </select>
        </div>

        <div className="flex flex-col gap-1 justify-center">
          <label className="text-xs text-slate-400">Demo mode</label>
          <div className="flex items-center gap-2">
            <input
              id="demo"
              type="checkbox"
              checked={demo}
              onChange={(e) => setDemo(e.target.checked)}
              className="h-4 w-4 rounded border-slate-600 bg-slate-900 text-emerald-500 focus:ring-emerald-500"
            />
            <label htmlFor="demo" className="text-xs text-slate-300">
              Use mock uptrend for guaranteed BUY (demo)
            </label>
          </div>
        </div>
      </div>

      {error && (
        <div className="rounded-xl border border-red-500/60 bg-red-500/10 px-3 py-2 text-xs text-red-200">
          {error}
        </div>
      )}

      <div className="flex justify-end">
        <button
          type="submit"
          disabled={loading}
          className="inline-flex items-center rounded-xl bg-emerald-500 px-4 py-2 text-sm font-semibold text-slate-950 hover:bg-emerald-400 disabled:opacity-60"
        >
          Run Analysis
        </button>
      </div>
    </form>
  );
};
