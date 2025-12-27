import React from "react";
import type { StrategyInfo } from "../lib/api";
import { LoadingSpinner } from "./LoadingSpinner";

interface Props {
  strategies: StrategyInfo[];
  loading: boolean;
  error: string | null;
  onRetry: () => void;
  enabledStrategies: string[];
  toggleStrategy: (name: string) => void;
  enableAll: () => void;
  disableAll: () => void;
}

export const StrategiesTab: React.FC<Props> = ({
  strategies,
  loading,
  error,
  onRetry,
  enabledStrategies,
  toggleStrategy,
  enableAll,
  disableAll,
}) => {
  const allDisabled = enabledStrategies.length === 0;

  if (loading) {
    return (
      <div className="flex items-center gap-2 text-sm text-slate-200">
        <LoadingSpinner />
        <span>Loading strategies...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-3">
        <div className="rounded-lg border border-red-500/50 bg-red-500/10 p-3 text-sm text-red-100">
          {error}
        </div>
        <button
          type="button"
          onClick={onRetry}
          className="rounded-lg border border-slate-700 bg-slate-800 px-3 py-1 text-xs font-semibold text-slate-100 hover:bg-slate-700"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Strategies</h2>
        <div className="space-x-2">
          <button
            type="button"
            onClick={enableAll}
            className="rounded-lg border border-slate-700 bg-slate-800 px-3 py-1 text-xs font-semibold text-slate-100 hover:bg-slate-700"
          >
            Enable all
          </button>
          <button
            type="button"
            onClick={disableAll}
            className="rounded-lg border border-slate-700 bg-slate-800 px-3 py-1 text-xs font-semibold text-slate-100 hover:bg-slate-700"
          >
            Disable all
          </button>
        </div>
      </div>

      {allDisabled && (
        <div className="rounded-lg border border-yellow-500/50 bg-yellow-500/10 p-2 text-xs text-yellow-200">
          All strategies are currently disabled. No trades will be suggested.
        </div>
      )}

      <div className="space-y-2">
        {strategies.map((s) => {
          const enabled = enabledStrategies.includes(s.name);
          return (
            <div
              key={s.name}
              className="flex items-start justify-between rounded-lg border border-slate-800 bg-slate-900/60 p-3"
            >
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-medium text-slate-100">{s.name}</span>
                  <span className="rounded-full bg-slate-800 px-2 py-0.5 text-xs capitalize text-slate-200">
                    {s.risk_profile}
                  </span>
                </div>
                <p className="mt-1 text-sm text-slate-300">{s.description}</p>
                <div className="mt-1 flex flex-wrap gap-1">
                  {s.regimes.map((regime) => (
                    <span
                      key={regime}
                      className="rounded-full bg-slate-800 px-2 py-0.5 text-[10px] uppercase tracking-wide text-slate-300"
                    >
                      {regime}
                    </span>
                  ))}
                </div>
              </div>
              <label className="flex items-center gap-2 text-xs text-slate-200">
                <input
                  type="checkbox"
                  checked={enabled}
                  onChange={() => toggleStrategy(s.name)}
                  className="h-4 w-4 rounded border-slate-600 bg-slate-900 text-emerald-500 focus:ring-emerald-500"
                />
                <span>{enabled ? "Enabled" : "Disabled"}</span>
              </label>
            </div>
          );
        })}
      </div>
    </div>
  );
};
