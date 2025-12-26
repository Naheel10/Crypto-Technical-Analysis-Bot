// frontend/src/lib/api.ts
export type TradeAction = "BUY" | "SELL" | "NO_TRADE";
export type RiskRating = "LOW" | "MEDIUM" | "HIGH";
export type MarketRegime =
  | "TREND_UP"
  | "TREND_DOWN"
  | "RANGE"
  | "CHOPPY"
  | "BREAKOUT"
  | "UNKNOWN";

export interface TradeSignalResponse {
  symbol: string;
  timeframe: string;
  action: TradeAction;
  strategy_name: string;
  entry_zone: [number, number] | null;
  stop_loss: number | null;
  take_profits: number[] | null;
  risk_rating: RiskRating;
  confidence_score: number;
  regime: MarketRegime;
  context: Record<string, number>;
  simple_explanation: string | null;
}

export interface BacktestResponse {
  symbol: string;
  timeframe: string;
  strategy_name: string;
  start: string;
  end: string;
  win_rate: number;
  total_return_pct: number;
  max_drawdown_pct: number;
  profit_factor: number;
  trades_count: number;
}

const API_BASE =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export async function fetchSignal(params: {
  symbol: string;
  timeframe: string;
  demo?: boolean;
}): Promise<TradeSignalResponse> {
  const url = new URL(`${API_BASE}/signal`);
  url.searchParams.set("symbol", params.symbol);
  url.searchParams.set("timeframe", params.timeframe);
  if (params.demo) url.searchParams.set("demo", "true");

  const res = await fetch(url.toString());
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || "Failed to fetch signal");
  }
  return res.json();
}

export async function fetchBacktest(params: {
  symbol: string;
  timeframe: string;
  strategy: string;
  start: string;
  end: string;
}): Promise<BacktestResponse> {
  const url = new URL(`${API_BASE}/backtest`);
  url.searchParams.set("symbol", params.symbol);
  url.searchParams.set("timeframe", params.timeframe);
  url.searchParams.set("strategy", params.strategy);
  url.searchParams.set("start", params.start);
  url.searchParams.set("end", params.end);

  const res = await fetch(url.toString());
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || "Failed to fetch backtest");
  }
  return res.json();
}
