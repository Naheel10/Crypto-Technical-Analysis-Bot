from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, Optional, Type

import pandas as pd

from bot.data.repository import DataRepository
from bot.data.client import ExchangeClient
from bot.indicators.core import add_basic_indicators
from bot.engine.regime import detect_regime
from bot.engine.orchestrator import select_primary_candidate
from bot.models import TradeDirection
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

    def __init__(
        self,
        repository: Optional[DataRepository] = None,
        exchange_client: Optional[ExchangeClient] = None,
    ) -> None:
        self.repository = repository or DataRepository()
        self.exchange_client = exchange_client or ExchangeClient()

    def _timeframe_to_timedelta(self, timeframe: str) -> timedelta:
        unit = timeframe[-1]
        try:
            value = int(timeframe[:-1])
        except ValueError as exc:  # pragma: no cover - defensive parsing
            raise ValueError(f"Invalid timeframe: {timeframe}") from exc

        mapping = {
            "s": timedelta(seconds=value),
            "m": timedelta(minutes=value),
            "h": timedelta(hours=value),
            "d": timedelta(days=value),
            "w": timedelta(weeks=value),
        }
        if unit not in mapping:
            raise ValueError(f"Unsupported timeframe unit: {unit}")
        return mapping[unit]

    def _has_requested_range(
        self,
        candles: pd.DataFrame,
        start: datetime,
        end: datetime,
        timeframe_delta: timedelta,
    ) -> bool:
        if candles.empty:
            return False
        earliest = candles["timestamp"].min()
        latest = candles["timestamp"].max()
        return earliest <= (start + timeframe_delta) and latest >= (end - timeframe_delta)

    def _load_candles_with_backfill(
        self,
        symbol: str,
        timeframe: str,
        start: datetime,
        end: datetime,
        timeframe_delta: timedelta,
    ) -> pd.DataFrame:
        candles = self.repository.load_candles(symbol, timeframe, start, end)
        if self._has_requested_range(candles, start, end, timeframe_delta):
            return candles

        fetched = self.exchange_client.sync_historical_candles(
            symbol=symbol, timeframe=timeframe, since=start, end=end
        )
        if fetched.empty:
            return candles

        filtered = fetched[(fetched["timestamp"] >= start) & (fetched["timestamp"] <= end)]
        if filtered.empty:
            return candles

        self.repository.save_candles(symbol, timeframe, filtered)
        return self.repository.load_candles(symbol, timeframe, start, end)

    def run_backtest(
        self,
        symbol: str,
        timeframe: str,
        strategy_cls: Type[BaseStrategy],
        start: datetime,
        end: datetime,
    ) -> BacktestResult:
        """Run a bar by bar backtest."""
        if start.tzinfo is not None:
            start = start.replace(tzinfo=None)
        if end.tzinfo is not None:
            end = end.replace(tzinfo=None)

        if start >= end:
            raise ValueError("Backtest start must be before end")

        timeframe_delta = self._timeframe_to_timedelta(timeframe)
        now = datetime.utcnow()
        if end - now > timeframe_delta:
            raise ValueError("End date cannot be in the future")

        candles = self._load_candles_with_backfill(
            symbol, timeframe, start, end, timeframe_delta
        )
        candles = add_basic_indicators(candles)
        candles = candles.dropna()
        candles = candles.sort_values("timestamp").reset_index(drop=True)

        if candles.empty:
            raise ValueError("No candles available for the requested range")

        print(
            f"[Backtester] Loaded {len(candles)} candles for {symbol} {timeframe}"
        )

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
            try:
                candidates = strategy.generate_candidates(
                    history, symbol, timeframe, regime
                )
            except Exception as exc:
                print(
                    f"[Backtester] Strategy {strategy.name} raised on bar {idx}: {exc!r}"
                )
                candidates = []

            primary = select_primary_candidate(candidates)
            candidate_action = primary.direction if primary else None

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
                    elif candidate_action == TradeDirection.SHORT:
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
                    elif candidate_action == TradeDirection.LONG:
                        exit_price = close

                if exit_price is not None:
                    close_position(exit_price)

            if position is None and primary:
                direction = 1 if primary.direction == TradeDirection.LONG else -1
                take_profit = (
                    primary.take_profits[0] if primary.take_profits else None
                )
                stop_loss = primary.stop_loss
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

        print(
            "[Backtester] Trades taken:",
            trades_count,
            f"win_rate={win_rate:.2f}%",
            f"total_return={total_return_pct:.2f}%",
            f"max_drawdown={max_drawdown_pct:.2f}%",
            f"profit_factor={'∞' if profit_factor == float('inf') else profit_factor:.2f}",
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
