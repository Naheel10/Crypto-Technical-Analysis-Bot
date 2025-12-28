// frontend/src/components/SignalCard.tsx
import React from "react";
import type { CandidateTrade, TradeSignalResponse } from "../lib/api";

interface Props {
  signal: TradeSignalResponse;
}

const biasColor: Record<string, string> = {
  STRONGLY_BULLISH: "bg-emerald-500/20 text-emerald-200 border border-emerald-500/40",
  BULLISH: "bg-emerald-500/10 text-emerald-200 border border-emerald-500/30",
  NEUTRAL: "bg-slate-700/50 text-slate-200 border border-slate-600",
  BEARISH: "bg-rose-500/10 text-rose-200 border border-rose-500/30",
  STRONGLY_BEARISH: "bg-rose-500/20 text-rose-100 border border-rose-500/50",
};

const directionLabel = (candidate: CandidateTrade | null) => {
  if (!candidate) return "NO CLEAR TRADE";
  return candidate.direction === "LONG" ? "BUY BIAS" : "SELL BIAS";
};

export const SignalCard: React.FC<Props> = ({ signal }) => {
  const primary = signal.primary_candidate;

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4 space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-3">
            <div
              className={`rounded-full px-3 py-1 text-xs font-semibold ${
                biasColor[signal.analysis.trend_bias] || biasColor.NEUTRAL
              }`}
            >
              {signal.analysis.trend_bias.replace("_", " ")}
            </div>
            <div className="text-sm font-semibold text-slate-100">
              {signal.symbol} • {signal.timeframe}
            </div>
          </div>
          <p className="text-xs text-slate-400">
            Regime: {signal.regime} • Structure: {signal.analysis.structure}
          </p>
        </div>
        <div className="text-right text-xs text-slate-400">
          Volatility: <span className="text-slate-100">{signal.analysis.volatility_regime}</span>
          <br />
          Momentum: <span className="text-slate-100">{signal.analysis.momentum_state}</span>
        </div>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-3 text-xs space-y-2">
          <h3 className="text-[13px] font-semibold text-slate-100">Market summary</h3>
          <div className="flex flex-wrap gap-2 text-slate-200">
            <span className="rounded-lg bg-slate-800 px-2 py-1">EMA20: {signal.analysis.ema20?.toFixed(2) ?? "—"}</span>
            <span className="rounded-lg bg-slate-800 px-2 py-1">EMA50: {signal.analysis.ema50?.toFixed(2) ?? "—"}</span>
            <span className="rounded-lg bg-slate-800 px-2 py-1">RSI14: {signal.analysis.rsi14?.toFixed(1) ?? "—"}</span>
          </div>
          <p className="text-slate-400">
            Latest price {signal.analysis.latest_price.toFixed(2)} near key levels {signal.analysis.key_levels
              .map((lvl) => `${lvl[0].toFixed(2)}-${lvl[1].toFixed(2)}`)
              .join(", ")}
          </p>
        </div>

        <div className="rounded-xl border border-emerald-800/60 bg-emerald-500/5 p-3 text-xs space-y-2">
          <div className="flex items-center justify-between">
            <h3 className="text-[13px] font-semibold text-emerald-200">Primary idea</h3>
            <span className="rounded-full bg-slate-800 px-2 py-1 text-[11px] text-slate-200">
              {directionLabel(primary)}
            </span>
          </div>
          {primary ? (
            <>
              <p className="text-slate-200 text-sm">
                {primary.setup_type} • Quality {primary.quality_score.toFixed(2)} • Risk {primary.risk_rating}
              </p>
              <div className="grid grid-cols-3 gap-2 text-[11px] text-slate-100">
                <div>
                  <div className="text-slate-400">Entry</div>
                  {primary.entry_zone ? (
                    <div>
                      {primary.entry_zone[0].toFixed(2)} – {primary.entry_zone[1].toFixed(2)}
                    </div>
                  ) : (
                    <div className="text-slate-500">Flexible</div>
                  )}
                </div>
                <div>
                  <div className="text-slate-400">Stop</div>
                  {primary.stop_loss ? primary.stop_loss.toFixed(2) : "—"}
                </div>
                <div>
                  <div className="text-slate-400">Targets</div>
                  {primary.take_profits?.length ? primary.take_profits.map((tp) => tp.toFixed(2)).join(", ") : "—"}
                </div>
              </div>
              <p className="text-slate-300">{primary.notes}</p>
            </>
          ) : (
            <p className="text-slate-300">No high-quality setup detected. Waiting for cleaner price action.</p>
          )}
        </div>
      </div>

      {signal.all_candidates.length > 1 && (
        <div className="rounded-xl border border-slate-800 bg-slate-950/50 p-3 text-xs space-y-2">
          <h3 className="text-[13px] font-semibold text-slate-100">Other ideas</h3>
          <div className="space-y-1 text-slate-200">
            {signal.all_candidates
              .filter((c) => c !== primary)
              .map((c, idx) => (
                <div key={idx} className="flex items-center justify-between rounded-lg bg-slate-900/70 px-2 py-2">
                  <div>
                    <div className="font-semibold">{c.setup_type}</div>
                    <div className="text-slate-400">{c.notes}</div>
                  </div>
                  <div className="text-right text-[11px] text-slate-300">
                    {c.direction} • Q {c.quality_score.toFixed(2)}
                  </div>
                </div>
              ))}
          </div>
        </div>
      )}

      {signal.simple_explanation && (
        <p className="text-sm text-slate-200 leading-relaxed">
          {signal.simple_explanation}
        </p>
      )}

      <p className="text-[11px] text-slate-500">
        This is an educational, simulated analysis. It is not financial advice and does not guarantee any outcome.
      </p>
    </div>
  );
};
