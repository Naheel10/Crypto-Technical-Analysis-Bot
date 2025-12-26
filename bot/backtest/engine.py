from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional, Type

import pandas as pd

from bot.data.repository import DataRepository
from bot.indicators.core import add_basic_indicators
from bot.engine.regime import detect_regime
from bot.models import TradeAction, TradeSignal
from bot.strategy.base import BaseStrategy


@dataclass
class BacktestResult:
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

        if candles.empty:
            raise ValueError("No candles available for the requested range")

        strategy = strategy_cls()

        trades: list[float] = []
        equity = 1.0
        peak_equity = 1.0
        max_drawdown = 0.0
        position: Optional[Dict] = None

        def close_position(exit_price: float) -> None:
            nonlocal equity, peak_equity, max_drawdown, position
            if position is None:
                return
            pct_return = (
                (exit_price - position["entry_price"])
                / position["entry_price"]
                * position["direction"]
            )
            trades.append(pct_return)
            equity *= 1 + pct_return
            peak_equity = max(peak_equity, equity)
            if peak_equity > 0:
                drawdown = (peak_equity - equity) / peak_equity
                max_drawdown = max(max_drawdown, drawdown)
            position = None

        for idx, row in candles.iterrows():
            history = candles.iloc[: idx + 1]
            regime = detect_regime(history)
            signal: Optional[TradeSignal] = strategy.generate_signal(
                history, symbol, timeframe, regime
            )

            high = float(row["high"])
            low = float(row["low"])
            close = float(row["close"])

            if position:
                exit_price: Optional[float] = None
                if position["direction"] == 1:
                    if (
                        position.get("stop_loss") is not None
                        and low <= float(position["stop_loss"])
                    ):
                        exit_price = float(position["stop_loss"])
                    elif (
                        position.get("take_profit") is not None
                        and high >= float(position["take_profit"])
                    ):
                        exit_price = float(position["take_profit"])
                    elif signal and signal.action == TradeAction.SELL:
                        exit_price = close
                else:
                    if (
                        position.get("stop_loss") is not None
                        and high >= float(position["stop_loss"])
                    ):
                        exit_price = float(position["stop_loss"])
                    elif (
                        position.get("take_profit") is not None
                        and low <= float(position["take_profit"])
                    ):
                        exit_price = float(position["take_profit"])
                    elif signal and signal.action == TradeAction.BUY:
                        exit_price = close

                if exit_price is not None:
                    close_position(exit_price)

            if position is None and signal and signal.action in (
                TradeAction.BUY,
                TradeAction.SELL,
            ):
                direction = 1 if signal.action == TradeAction.BUY else -1
                take_profit = signal.take_profits[0] if signal.take_profits else None
                stop_loss = signal.stop_loss
                position = {
                    "direction": direction,
                    "entry_price": close,
                    "take_profit": take_profit,
                    "stop_loss": stop_loss,
                }

        # Close any open position at the final close
        if position is not None:
            close_position(float(candles.iloc[-1]["close"]))

        trades_count = len(trades)
        wins = len([t for t in trades if t > 0])
        gross_profit = sum(t for t in trades if t > 0)
        gross_loss = abs(sum(t for t in trades if t < 0))

        win_rate = (wins / trades_count * 100) if trades_count else 0.0
        total_return_pct = (equity - 1) * 100
        max_drawdown_pct = max_drawdown * 100
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else (
            float("inf") if gross_profit > 0 else 0.0
        )

        result = BacktestResult(
            symbol=symbol,
            timeframe=timeframe,
            strategy_name=strategy.name,
            start=start,
            end=end,
            win_rate=win_rate,
            total_return_pct=total_return_pct,
            max_drawdown_pct=max_drawdown_pct,
            profit_factor=profit_factor,
            trades_count=trades_count,
        )

        return result
