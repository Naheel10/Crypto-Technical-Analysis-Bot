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

export interface CandleWithIndicators {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  ema20?: number | null;
  ema50?: number | null;
  ema200?: number | null;
  rsi14?: number | null;
  macd?: number | null;
  macd_signal?: number | null;
  macd_hist?: number | null;
  bb_high?: number | null;
  bb_low?: number | null;
  bb_mid?: number | null;
  bb_width?: number | null;
}

export interface CandlesResponse {
  symbol: string;
  timeframe: string;
  candles: CandleWithIndicators[];
}

export interface SignalHistoryItem {
  id: number;
  created_at: string;
  symbol: string;
  timeframe: string;
  action: TradeAction;
  strategy_name: string;
  risk_rating: RiskRating;
  confidence_score: number;
  regime: MarketRegime;
}

export interface RecentSignalsResponse {
  items: SignalHistoryItem[];
}

export interface PositionSizingRequest {
  account_size: number;
  risk_pct: number;
  entry_price: number;
  stop_loss: number;
  take_profits?: number[];
}

export interface PositionSizingResponse {
  account_size: number;
  risk_pct: number;
  risk_amount: number;
  position_size: number;
  r_to_tp: number[];
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

export async function fetchCandles(params: {
  symbol: string;
  timeframe: string;
  limit?: number;
}): Promise<CandlesResponse> {
  const url = new URL(`${API_BASE}/candles`);
  url.searchParams.set("symbol", params.symbol);
  url.searchParams.set("timeframe", params.timeframe);
  if (params.limit) url.searchParams.set("limit", params.limit.toString());

  const res = await fetch(url.toString());
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || "Failed to fetch candles");
  }
  return res.json();
}

export async function fetchRecentSignals(
  limit: number = 20,
): Promise<SignalHistoryItem[]> {
  const url = new URL(`${API_BASE}/signals/recent`);
  url.searchParams.set("limit", limit.toString());

  const res = await fetch(url.toString());
  if (!res.ok) {
    throw new Error("Failed to fetch recent signals");
  }
  const data: RecentSignalsResponse = await res.json();
  return data.items;
}

export async function calculatePositionSizing(
  payload: PositionSizingRequest,
): Promise<PositionSizingResponse> {
  const res = await fetch(`${API_BASE}/risk/position`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || "Failed to calculate position sizing");
  }

  return res.json();
}
