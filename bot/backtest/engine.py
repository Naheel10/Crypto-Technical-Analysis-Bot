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
    Simple but robust backtest engine for a single strategy.

    Design choices (to avoid the issues you were seeing):

    - We **do not** try to reconstruct an exact historical date window via the DB.
      Instead, we fetch a large chunk of recent candles directly from the exchange,
      just like the /candles endpoint that already works.
    - We still *approximate* the user’s requested window (start/end) when choosing
      which part of the data to trade on, but we never rely on the exchange's
      `since` behaviour (which is flaky across venues).
    - Indicators get plenty of warm-up candles so `dropna()` does not nuke
      the entire DataFrame.
    """

    # how many bars we want to trade at minimum
    MIN_CORE_BARS = 100
    # extra bars before the trading window for indicator warmup
    WARMUP_BARS = 250

    def __init__(
        self,
        repository: Optional[DataRepository] = None,
        exchange_client: Optional[ExchangeClient] = None,
    ) -> None:
        self.repository = repository or DataRepository()
        self.exchange_client = exchange_client or ExchangeClient()

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #

    def _timeframe_to_timedelta(self, timeframe: str) -> timedelta:
        """
        Convert strings like '1h', '4h', '15m', '1d' into a timedelta.
        """
        unit = timeframe[-1]
        try:
            value = int(timeframe[:-1])
        except ValueError as exc:
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

    def _compute_bars_needed(self, timeframe: str, start: datetime, end: datetime) -> int:
        """
        Roughly estimate how many bars we want to trade over the requested window,
        then add warmup bars for indicators.
        """
        tf_delta = self._timeframe_to_timedelta(timeframe)
        span_seconds = max((end - start).total_seconds(), 0.0)
        per_bar = tf_delta.total_seconds() or 1.0

        core_bars = int(span_seconds / per_bar)
        if core_bars < self.MIN_CORE_BARS:
            core_bars = self.MIN_CORE_BARS

        return core_bars + self.WARMUP_BARS

    # ------------------------------------------------------------------ #
    # Main backtest entrypoint
    # ------------------------------------------------------------------ #

    def run_backtest(
        self,
        symbol: str,
        timeframe: str,
        strategy_cls: Type[BaseStrategy],
        start: datetime,
        end: datetime,
    ) -> BacktestResult:
        """
        Run a bar-by-bar backtest.

        NOTE: We *approximate* the requested [start, end] using the most recent
        candles from the exchange. The actual start/end used are stored in the
        BacktestResult and shown in your history table.
        """

        # normalise datetimes (we keep everything naive/UTC)
        if start.tzinfo is not None:
            start = start.replace(tzinfo=None)
        if end.tzinfo is not None:
            end = end.replace(tzinfo=None)

        if start >= end:
            raise ValueError("Backtest start must be before end")

        now = datetime.utcnow()
        if end > now:
            raise ValueError("End date cannot be in the future")

        # How many bars do we want in total (core + warmup)?
        limit = self._compute_bars_needed(timeframe, start, end)

        # ------------------------------------------------------------------
        # 1) Fetch recent candles directly from the exchange (same as /candles)
        # ------------------------------------------------------------------
        candles = self.exchange_client.get_recent_candles(
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
        )
        if candles is None or candles.empty:
            raise ValueError(
                "No candles available from the exchange for that market/timeframe."
            )

        candles = candles.sort_values("timestamp").reset_index(drop=True)

        # ------------------------------------------------------------------
        # 2) Add indicators and drop warmup rows with NaNs
        # ------------------------------------------------------------------
        candles = add_basic_indicators(candles)
        before_dropna = len(candles)
        candles = candles.dropna().reset_index(drop=True)

        if candles.empty:
            raise ValueError(
                "No usable candles after applying indicators (dropna removed all rows). "
                "Try a longer lookback window or a higher timeframe."
            )

        # ------------------------------------------------------------------
        # 3) Approximate the requested date window inside this data
        # ------------------------------------------------------------------
        # We try to keep only rows between [start, end]. If that gives us too
        # few candles (because the exchange only returned very recent data),
        # we just use the last MIN_CORE_BARS candles as the trading window.
        tf_delta = self._timeframe_to_timedelta(timeframe)
        approx_core_bars = max(
            int((end - start).total_seconds() / tf_delta.total_seconds()),
            self.MIN_CORE_BARS,
        )

        window = candles[
            (candles["timestamp"] >= start) & (candles["timestamp"] <= end)
        ].copy()

        if len(window) < 50:
            # fallback: just take the most recent slice
            window = candles.iloc[-approx_core_bars :].copy()

        if window.empty:
            raise ValueError(
                "No candles available for the requested range (even after warmup). "
                "Try a more recent range or different timeframe."
            )

        # This is the actual window we will trade on
        candles = window.reset_index(drop=True)
        actual_start = candles["timestamp"].iloc[0].to_pydatetime().replace(tzinfo=None)
        actual_end = candles["timestamp"].iloc[-1].to_pydatetime().replace(tzinfo=None)

        print(
            f"[Backtester] Using {len(candles)} candles for {symbol} {timeframe} "
            f"(fetched={before_dropna}, window={actual_start} → {actual_end})"
        )

        # ------------------------------------------------------------------
        # 4) Run the strategy bar-by-bar
        # ------------------------------------------------------------------
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
            primary_direction = primary.direction if primary else None

            high = float(row["high"])
            low = float(row["low"])
            close = float(row["close"])

            # --- manage open position first ---
            if position:
                exit_price: Optional[float] = None
                if position["direction"] == 1:
                    # long
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
                    elif primary_direction == TradeDirection.SHORT:
                        exit_price = close
                else:
                    # short
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
                    elif primary_direction == TradeDirection.LONG:
                        exit_price = close

                if exit_price is not None:
                    close_position(exit_price)

            # --- open new position if flat and we have a valid candidate ---
            if position is None and primary is not None:
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

        # ------------------------------------------------------------------
        # 5) Compute stats
        # ------------------------------------------------------------------
        trades_count = len(trades)
        wins = len([t for t in trades if t > 0])
        gross_profit = sum(t for t in trades if t > 0)
        gross_loss = abs(sum(t for t in trades if t < 0))

        win_rate = (wins / trades_count * 100) if trades_count else 0.0
        total_return_pct = (equity - 1) * 100
        max_drawdown_pct = max_drawdown * 100
        if gross_loss > 0:
            profit_factor = gross_profit / gross_loss
        else:
            profit_factor = float("inf") if gross_profit > 0 else 0.0

        print(
            "[Backtester] Trades:",
            trades_count,
            f"win_rate={win_rate:.2f}%",
            f"total_return={total_return_pct:.2f}%",
            f"max_dd={max_drawdown_pct:.2f}%",
            f"pf={'∞' if profit_factor == float('inf') else profit_factor:.2f}",
        )

        return BacktestResult(
            symbol=symbol,
            timeframe=timeframe,
            strategy_name=strategy.name,
            start=actual_start,
            end=actual_end,
            win_rate=win_rate,
            total_return_pct=total_return_pct,
            max_drawdown_pct=max_drawdown_pct,
            profit_factor=profit_factor,
            trades_count=trades_count,
        )
