from __future__ import annotations

from dataclasses import dataclass, asdict
from enum import Enum
from typing import Dict, List, Optional, Tuple


class TradeAction(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    NO_TRADE = "NO_TRADE"


class TradeDirection(str, Enum):
    LONG = "LONG"
    SHORT = "SHORT"


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


class TrendBias(str, Enum):
    STRONGLY_BULLISH = "STRONGLY_BULLISH"
    BULLISH = "BULLISH"
    NEUTRAL = "NEUTRAL"
    BEARISH = "BEARISH"
    STRONGLY_BEARISH = "STRONGLY_BEARISH"


class MarketStructure(str, Enum):
    TREND = "TREND"
    RANGE = "RANGE"
    CHOP = "CHOP"


class MomentumState(str, Enum):
    BUILDING = "BUILDING"
    FADING = "FADING"
    EXTREME = "EXTREME"


class VolatilityRegime(str, Enum):
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    INSANE = "INSANE"


class SetupType(str, Enum):
    PULLBACK = "PULLBACK"
    BREAKOUT = "BREAKOUT"
    RANGE_REVERSION = "RANGE_REVERSION"
    TREND_EXIT = "TREND_EXIT"
    MOMENTUM_FADE = "MOMENTUM_FADE"


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


@dataclass
class CandidateTrade:
    """Possible trade idea emitted by a strategy with a quality score."""

    direction: TradeDirection
    setup_type: SetupType | str
    entry_zone: Optional[Tuple[float, float]]
    stop_loss: Optional[float]
    take_profits: Optional[List[float]]
    quality_score: float
    risk_rating: RiskRating
    notes: str
    strategy_name: str


@dataclass
class AnalysisSnapshot:
    """Structured view of the current market conditions."""

    symbol: str
    timeframe: str
    trend_bias: TrendBias
    structure: MarketStructure
    momentum_state: MomentumState
    volatility_regime: VolatilityRegime
    key_levels: List[Tuple[float, float]]
    latest_price: float
    ema20: Optional[float]
    ema50: Optional[float]
    ema200: Optional[float]
    rsi14: Optional[float]
    macd_hist: Optional[float]


@dataclass
class AnalysisResult:
    """Container returned by the signal engine for API consumption."""

    analysis: AnalysisSnapshot
    primary_candidate: Optional[CandidateTrade]
    all_candidates: List[CandidateTrade]
    regime: MarketRegime
