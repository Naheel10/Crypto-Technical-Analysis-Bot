from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional, Type

import pandas as pd

from bot.data.repository import DataRepository
from bot.indicators.core import add_basic_indicators
from bot.engine.regime import detect_regime
from bot.models import TradeSignal
from bot.strategy.base import BaseStrategy


@dataclass
class BacktestResult:
    symbol: str
    timeframe: str
    strategy_name: str
    start: datetime
    end: datetime
    win_rate: float
    total_return: float
    max_drawdown: float
    profit_factor: float
    trades_count: int


class Backtester:
    """
    Very simple backtest engine for one strategy.

    Uses basic assumptions and close to close fills.
    """

    def __init__(self, repository: Optional[DataRepository] = None) -> None:
        self.repository = repository or DataRepository()

    def run_backtest(
        self,
        symbol: str,
        timeframe: str,
        strategy_cls: Type[BaseStrategy],
        start: datetime,
        end: datetime,
    ) -> BacktestResult:
        """Run a bar by bar backtest."""
        candles = self.repository.load_candles(symbol, timeframe, start, end)
        candles = add_basic_indicators(candles)
        candles = candles.dropna()
        strategy = strategy_cls()

        # TODO implement proper backtesting logic
        # For now this is a placeholder with dummy metrics
        win_rate = 0.5
        total_return = 0.0
        max_drawdown = 0.1
        profit_factor = 1.0
        trades_count = 0

        return BacktestResult(
            symbol=symbol,
            timeframe=timeframe,
            strategy_name=strategy.name,
            start=start,
            end=end,
            win_rate=win_rate,
            total_return=total_return,
            max_drawdown=max_drawdown,
            profit_factor=profit_factor,
            trades_count=trades_count,
        )
