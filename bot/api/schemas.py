from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional, Tuple

from pydantic import BaseModel

from bot.models import MarketRegime, RiskRating, TradeAction


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
