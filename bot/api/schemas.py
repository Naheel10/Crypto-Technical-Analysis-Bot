from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional, Tuple, Literal

from pydantic import BaseModel

from bot.models import MarketRegime, RiskRating, TradeAction
from bot.engine.risk import PositionSizingRequest, PositionSizingResponse


RiskProfile = Literal["conservative", "moderate", "aggressive"]


class StrategyInfo(BaseModel):
    name: str
    description: str
    regimes: list[MarketRegime]
    risk_profile: RiskProfile


class StrategyListResponse(BaseModel):
    items: list[StrategyInfo]


class TradeSignalResponse(BaseModel):
    symbol: str
    timeframe: str
    action: TradeAction
    strategy_name: str
    entry_zone: Optional[Tuple[float, float]] = None
    stop_loss: Optional[float] = None
    take_profits: Optional[List[float]] = None
    risk_rating: RiskRating
    confidence_score: float
    regime: MarketRegime
    context: Dict[str, float]
    simple_explanation: Optional[str] = None


class SignalScanRequest(BaseModel):
    symbols: list[str]
    timeframe: str
    demo: bool = False
    limit: int = 200
    enabled_strategies: list[str] | None = None


class SignalSummary(BaseModel):
    symbol: str
    timeframe: str
    action: TradeAction
    strategy_name: str
    risk_rating: RiskRating
    confidence_score: float
    regime: MarketRegime
    created_at: datetime
    simple_explanation: Optional[str] = None


class SignalScanResponse(BaseModel):
    items: list[SignalSummary]


class BacktestResponse(BaseModel):
    symbol: str
    timeframe: str
    strategy_name: str
    start: datetime
    end: datetime
    win_rate: float
    total_return_pct: float
    max_drawdown_pct: float
    profit_factor: float
    trades_count: int


class BacktestHistoryItem(BaseModel):
    id: int
    created_at: datetime
    symbol: str
    timeframe: str
    strategy_name: str
    start: datetime
    end: datetime
    win_rate: float
    total_return_pct: float
    max_drawdown_pct: float
    profit_factor: float
    trades_count: int


class RecentBacktestsResponse(BaseModel):
    items: list[BacktestHistoryItem]


class CandleWithIndicators(BaseModel):
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    ema20: Optional[float] = None
    ema50: Optional[float] = None
    ema200: Optional[float] = None
    rsi14: Optional[float] = None
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_hist: Optional[float] = None
    bb_high: Optional[float] = None
    bb_low: Optional[float] = None
    bb_mid: Optional[float] = None
    bb_width: Optional[float] = None


class CandlesResponse(BaseModel):
    symbol: str
    timeframe: str
    candles: List[CandleWithIndicators]


class SignalHistoryItem(BaseModel):
    id: int
    created_at: datetime
    symbol: str
    timeframe: str
    action: TradeAction
    strategy_name: str
    risk_rating: RiskRating
    confidence_score: float
    regime: MarketRegime


class RecentSignalsResponse(BaseModel):
    items: list[SignalHistoryItem]


__all__ = [
    "RiskProfile",
    "StrategyInfo",
    "StrategyListResponse",
    "TradeSignalResponse",
    "BacktestResponse",
    "BacktestHistoryItem",
    "RecentBacktestsResponse",
    "CandleWithIndicators",
    "CandlesResponse",
    "SignalHistoryItem",
    "RecentSignalsResponse",
    "PositionSizingRequest",
    "PositionSizingResponse",
    "SignalScanRequest",
    "SignalSummary",
    "SignalScanResponse",
]
