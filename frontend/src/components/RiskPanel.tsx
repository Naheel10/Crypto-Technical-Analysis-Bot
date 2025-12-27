import React, { useState } from "react";
import {
  calculatePositionSizing,
  type PositionSizingResponse,
  type TradeSignalResponse,
} from "../lib/api";
import { LoadingSpinner } from "./LoadingSpinner";

interface Props {
  signal: TradeSignalResponse | null;
}

export const RiskPanel: React.FC<Props> = ({ signal }) => {
  const [accountSize, setAccountSize] = useState(1000);
  const [riskPct, setRiskPct] = useState(1);
  const [result, setResult] = useState<PositionSizingResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const canCalculate = Boolean(signal && signal.stop_loss !== null);

  const handleCalculate = async () => {
    if (!signal || signal.stop_loss === null) {
      return;
    }

    const entryPrice = signal.entry_zone
      ? (signal.entry_zone[0] + signal.entry_zone[1]) / 2
      : signal.context?.close;

    if (!entryPrice || !signal.stop_loss) {
      setError("Missing entry or stop loss to size a position.");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const data = await calculatePositionSizing({
        account_size: accountSize,
        risk_pct: riskPct / 100,
        entry_price: entryPrice,
        stop_loss: signal.stop_loss,
        take_profits: signal.take_profits || undefined,
      });
      setResult(data);
    } catch (err) {
      console.error(err);
      setError("Unable to calculate position size");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4 text-sm">
      <div className="mb-3 flex items-center justify-between">
        <div>
          <h2 className="text-sm font-semibold text-slate-100">
            Risk helper
          </h2>
          <p className="text-xs text-slate-400">
            Size a position using the signal entry and stop.
          </p>
        </div>
        {loading && <LoadingSpinner />}
      </div>

      {!canCalculate && (
        <p className="text-xs text-slate-400">
          Run analysis to get a setup with a stop loss before sizing your risk.
        </p>
      )}

      {canCalculate && (
        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <div className="flex flex-col gap-1">
              <label className="text-xs text-slate-400">Account size (USD)</label>
              <input
                type="number"
                className="rounded-xl border border-slate-700 bg-slate-900 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
                value={accountSize}
                min={0}
                onChange={(e) => setAccountSize(Number(e.target.value))}
              />
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-xs text-slate-400">Risk per trade (%)</label>
              <input
                type="number"
                className="rounded-xl border border-slate-700 bg-slate-900 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
                value={riskPct}
                min={0}
                step={0.1}
                onChange={(e) => setRiskPct(Number(e.target.value))}
              />
            </div>
          </div>

          {error && (
            <div className="rounded-xl border border-rose-500/60 bg-rose-500/10 px-3 py-2 text-xs text-rose-100">
              {error}
            </div>
          )}

          <button
            type="button"
            onClick={handleCalculate}
            disabled={loading}
            className="inline-flex items-center rounded-xl bg-emerald-500 px-4 py-2 text-sm font-semibold text-slate-950 hover:bg-emerald-400 disabled:opacity-60"
          >
            Calculate position size
          </button>

          {result && (
            <div className="rounded-xl border border-slate-800 bg-slate-950/40 p-3 text-xs text-slate-200 space-y-2">
              <p>
                Position size: <span className="font-semibold">{result.position_size.toFixed(4)}</span>
              </p>
              <p>
                Risk per trade: <span className="font-semibold">${result.risk_amount.toFixed(2)}</span>
              </p>
              {result.r_to_tp.length > 0 && (
                <div className="space-y-1">
                  {result.r_to_tp.map((r, idx) => (
                    <p key={idx}>
                      R to TP{idx + 1}: <span className="font-semibold">{r.toFixed(2)}x</span>
                    </p>
                  ))}
                </div>
              )}
              <p className="text-slate-400">
                If you risk {riskPct}% of a ${accountSize.toLocaleString()} account, this position
                would risk ${result.risk_amount.toFixed(2)} with stop-loss at {signal?.stop_loss?.toFixed(2)}.
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

