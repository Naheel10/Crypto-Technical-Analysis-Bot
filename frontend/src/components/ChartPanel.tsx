import React, { useEffect, useMemo, useState } from "react";
import {
  fetchCandles,
  type CandleWithIndicators,
  type TradeSignalResponse,
} from "../lib/api";
import { LoadingSpinner } from "./LoadingSpinner";

interface Props {
  symbol: string;
  timeframe: string;
  signal: TradeSignalResponse | null;
}

interface ScaledCandle {
  raw: CandleWithIndicators;
  x: number;
  yOpen: number;
  yClose: number;
  yHigh: number;
  yLow: number;
}

const CHART_WIDTH = 900;
const CHART_HEIGHT = 320;
const PADDING = 50;

export const ChartPanel: React.FC<Props> = ({ symbol, timeframe, signal }) => {
  const [candles, setCandles] = useState<CandleWithIndicators[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    const load = async () => {
      try {
        const data = await fetchCandles({ symbol, timeframe, limit: 200 });
        if (cancelled) return;
        setCandles(data.candles);
      } catch (err) {
        console.error(err);
        if (!cancelled)
          setError("Unable to load chart data. Please try again.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    load();

    return () => {
      cancelled = true;
    };
  }, [symbol, timeframe]);

  const priceRange = useMemo(() => {
    if (candles.length === 0)
      return { min: 0, max: 1 };

    const allPrices = candles.flatMap((c) => [c.high, c.low]);
    const min = Math.min(...allPrices);
    const max = Math.max(...allPrices);
    const padding = (max - min) * 0.05 || 1;
    return { min: min - padding, max: max + padding };
  }, [candles]);

  const scaledCandles: ScaledCandle[] = useMemo(() => {
    if (candles.length === 0) return [];
    const step = (CHART_WIDTH - PADDING * 2) / Math.max(candles.length - 1, 1);
    const scaleY = (price: number) =>
      CHART_HEIGHT -
      PADDING -
      ((price - priceRange.min) / (priceRange.max - priceRange.min)) *
        (CHART_HEIGHT - PADDING * 2);

    return candles.map((candle, idx) => {
      const x = PADDING + step * idx;
      return {
        raw: candle,
        x,
        yOpen: scaleY(candle.open),
        yClose: scaleY(candle.close),
        yHigh: scaleY(candle.high),
        yLow: scaleY(candle.low),
      };
    });
  }, [candles, priceRange]);

  const buildLinePath = (
    accessor: (c: CandleWithIndicators) => number | null | undefined,
  ) => {
    if (scaledCandles.length === 0) return "";
    const segments = scaledCandles
      .map((c) => {
        const val = accessor(c.raw);
        if (val === null || val === undefined) return null;
        return `${c.x},${
          CHART_HEIGHT -
          PADDING -
          ((val - priceRange.min) / (priceRange.max - priceRange.min)) *
            (CHART_HEIGHT - PADDING * 2)
        }`;
      })
      .filter(Boolean) as string[];

    if (segments.length < 2) return "";
    return `M ${segments.join(" L ")}`;
  };

  const entryLevels = signal?.entry_zone || null;
  const stopLoss = signal?.stop_loss || null;
  const takeProfits = signal?.take_profits || [];

  const priceToY = (price: number) =>
    CHART_HEIGHT -
    PADDING -
    ((price - priceRange.min) / (priceRange.max - priceRange.min)) *
      (CHART_HEIGHT - PADDING * 2);

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4 space-y-3">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-sm font-semibold text-slate-100">Chart panel</h2>
          <p className="text-xs text-slate-400">
            Price (candles) with EMAs and your current signal levels.
          </p>
        </div>
        {loading && <LoadingSpinner />}
      </div>

      {error ? (
        <div className="flex h-80 items-center justify-center rounded-xl border border-red-500/60 bg-red-500/10 px-3 py-2 text-sm text-red-200">
          {error}
        </div>
      ) : candles.length === 0 ? (
        <div className="flex h-80 items-center justify-center rounded-xl border border-slate-800 bg-slate-900/40 text-sm text-slate-300">
          No chart data yet. Run an analysis to load candles.
        </div>
      ) : (
        <div className="relative overflow-hidden rounded-xl border border-slate-800 bg-slate-950/60">
          <svg
            viewBox={`0 0 ${CHART_WIDTH} ${CHART_HEIGHT}`}
            className="h-80 w-full"
            preserveAspectRatio="none"
          >
            <rect
              x={0}
              y={0}
              width={CHART_WIDTH}
              height={CHART_HEIGHT}
              fill="url(#grid-bg)"
            />
            <defs>
              <linearGradient id="grid-bg" x1="0" x2="0" y1="0" y2="1">
                <stop offset="0%" stopColor="#0b1220" />
                <stop offset="100%" stopColor="#0f172a" />
              </linearGradient>
            </defs>

            {Array.from({ length: 6 }).map((_, i) => {
              const x = PADDING + ((CHART_WIDTH - PADDING * 2) / 5) * i;
              return (
                <line
                  key={`v-${i}`}
                  x1={x}
                  x2={x}
                  y1={PADDING / 2}
                  y2={CHART_HEIGHT - PADDING / 2}
                  stroke="#1e293b"
                  strokeWidth={1}
                />
              );
            })}
            {Array.from({ length: 6 }).map((_, i) => {
              const y = PADDING / 2 + ((CHART_HEIGHT - PADDING) / 5) * i;
              return (
                <line
                  key={`h-${i}`}
                  x1={PADDING / 2}
                  x2={CHART_WIDTH - PADDING / 2}
                  y1={y}
                  y2={y}
                  stroke="#1e293b"
                  strokeWidth={1}
                />
              );
            })}

            {entryLevels && (
              <g>
                <rect
                  x={PADDING / 2}
                  width={CHART_WIDTH - PADDING}
                  y={Math.min(priceToY(entryLevels[0]), priceToY(entryLevels[1]))}
                  height={
                    Math.abs(priceToY(entryLevels[0]) - priceToY(entryLevels[1])) || 1
                  }
                  fill="rgba(250, 204, 21, 0.12)"
                />
              </g>
            )}

            {takeProfits?.map((tp, idx) => (
              <line
                key={`tp-${tp}-${idx}`}
                x1={PADDING / 2}
                x2={CHART_WIDTH - PADDING / 2}
                y1={priceToY(tp)}
                y2={priceToY(tp)}
                stroke="#22c55e"
                strokeDasharray="4 4"
                strokeWidth={2}
              />
            ))}

            {stopLoss && (
              <line
                x1={PADDING / 2}
                x2={CHART_WIDTH - PADDING / 2}
                y1={priceToY(stopLoss)}
                y2={priceToY(stopLoss)}
                stroke="#ef4444"
                strokeWidth={2}
              />
            )}

            {entryLevels && (
              <>
                <line
                  x1={PADDING / 2}
                  x2={CHART_WIDTH - PADDING / 2}
                  y1={priceToY(entryLevels[0])}
                  y2={priceToY(entryLevels[0])}
                  stroke="#facc15"
                  strokeWidth={2}
                  strokeDasharray="6 6"
                />
                <line
                  x1={PADDING / 2}
                  x2={CHART_WIDTH - PADDING / 2}
                  y1={priceToY(entryLevels[1])}
                  y2={priceToY(entryLevels[1])}
                  stroke="#facc15"
                  strokeWidth={2}
                  strokeDasharray="6 6"
                />
              </>
            )}

            <path
              d={buildLinePath((c) => c.ema200 ?? null)}
              fill="none"
              stroke="#f59e0b"
              strokeWidth={2}
            />
            <path
              d={buildLinePath((c) => c.ema50 ?? null)}
              fill="none"
              stroke="#38bdf8"
              strokeWidth={2}
            />
            <path
              d={buildLinePath((c) => c.ema20 ?? null)}
              fill="none"
              stroke="#a855f7"
              strokeWidth={2}
            />

            {scaledCandles.map((candle, idx) => {
              const isUp = candle.raw.close >= candle.raw.open;
              const bodyTop = Math.min(candle.yOpen, candle.yClose);
              const bodyHeight = Math.max(Math.abs(candle.yOpen - candle.yClose), 2);
              const bodyColor = isUp ? "#22c55e" : "#ef4444";

              return (
                <g key={idx}>
                  <line
                    x1={candle.x}
                    x2={candle.x}
                    y1={candle.yHigh}
                    y2={candle.yLow}
                    stroke={bodyColor}
                    strokeWidth={1}
                  />
                  <rect
                    x={candle.x - 4}
                    width={8}
                    y={bodyTop}
                    height={bodyHeight}
                    fill={bodyColor}
                    opacity={0.9}
                    rx={2}
                  />
                </g>
              );
            })}

            {Array.from({ length: 5 }).map((_, i) => {
              const priceLabel =
                priceRange.max - ((priceRange.max - priceRange.min) / 4) * i;
              const y = priceToY(priceLabel);
              return (
                <text
                  key={`label-${i}`}
                  x={10}
                  y={y + 4}
                  className="fill-slate-400 text-[10px]"
                >
                  {priceLabel.toFixed(2)}
                </text>
              );
            })}
          </svg>

          {loading && (
            <div className="absolute inset-0 flex items-center justify-center bg-slate-900/70 backdrop-blur">
              <LoadingSpinner />
            </div>
          )}
        </div>
      )}

      <div className="grid gap-2 text-xs text-slate-300 sm:grid-cols-2">
        <div className="flex flex-col gap-1">
          <span className="font-semibold text-slate-100">Legend</span>
          <span>Price (candles)</span>
          <span className="text-purple-200">Short-term trend (EMA 20)</span>
          <span className="text-sky-200">Medium-term trend (EMA 50)</span>
          <span className="text-amber-200">Long-term trend (EMA 200)</span>
        </div>
        <div className="text-slate-400">
          {signal ? (
            <p>
              Visual overlays show entry, stop loss, and targets for the latest
              signal.
            </p>
          ) : (
            <p>Run an analysis to see suggested levels on the chart.</p>
          )}
        </div>
      </div>

      <p className="text-[11px] text-slate-400">
        This chart shows the recent price action for {symbol} on {timeframe} with
        trend EMAs and the suggested entry/stop/targets for the current signal.
      </p>
    </div>
  );
};
