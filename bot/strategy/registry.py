from __future__ import annotations

from typing import Dict, List

from bot.models import MarketRegime
from bot.strategy.base import BaseStrategy
from bot.strategy.trend_continuation import TrendContinuationStrategy
from bot.strategy.range_reversion import RangeReversionStrategy

# Instantiate singletons
_trend_continuation = TrendContinuationStrategy()
_range_reversion = RangeReversionStrategy()

# Map regimes to strategies; UNKNOWN gets both so we always try something
_REGISTRY: Dict[MarketRegime, List[BaseStrategy]] = {
    MarketRegime.TREND_UP: [_trend_continuation],
    MarketRegime.TREND_DOWN: [_trend_continuation],   # could become short-only later
    MarketRegime.RANGE: [_range_reversion],
    MarketRegime.CHOPPY: [_range_reversion],
    MarketRegime.BREAKOUT: [_trend_continuation],
    MarketRegime.UNKNOWN: [_trend_continuation, _range_reversion],
}


def get_strategy_registry() -> Dict[MarketRegime, List[BaseStrategy]]:
    """Return mapping from market regime to list of strategies to run."""
    return _REGISTRY
