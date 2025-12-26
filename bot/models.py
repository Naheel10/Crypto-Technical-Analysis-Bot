from __future__ import annotations

from dataclasses import dataclass, asdict
from enum import Enum
from typing import Dict, List, Optional, Tuple


class TradeAction(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    NO_TRADE = "NO_TRADE"


class RiskRating(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class MarketRegime(str, Enum):
    TREND_UP = "TREND_UP"
    TREND_DOWN = "TREND_DOWN"
    RANGE = "RANGE"
    CHOPPY = "CHOPPY"
    BREAKOUT = "BREAKOUT"
    UNKNOWN = "UNKNOWN"


@dataclass
class TradeSignal:
    """
    Single trade recommendation produced by a strategy or the engine.
    """

    symbol: str
    timeframe: str
    action: TradeAction
    strategy_name: str
    entry_zone: Optional[Tuple[float, float]]
    stop_loss: Optional[float]
    take_profits: Optional[List[float]]
    risk_rating: RiskRating
    confidence_score: float
    regime: MarketRegime
    context: Dict[str, float]

    def to_dict(self) -> Dict:
        """Convert signal to a plain dict for JSON serialization."""
        data = asdict(self)
        data["action"] = self.action.value
        data["risk_rating"] = self.risk_rating.value
        data["regime"] = self.regime.value
        return data
