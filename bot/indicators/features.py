from __future__ import annotations

import pandas as pd

from bot.models import MarketRegime


def compute_trend_direction(df: pd.DataFrame) -> MarketRegime:
    """
    Simple trend direction based on EMAs and recent price.

    Much looser rules so we classify uptrends more often.
    """
    last = df.iloc[-1]
    ema20 = float(last["ema20"])
    ema50 = float(last["ema50"])
    close = float(last["close"])

    # Loose definition of uptrend / downtrend
    if ema20 > ema50 and close > ema20:
        return MarketRegime.TREND_UP

    if ema20 < ema50 and close < ema20:
        return MarketRegime.TREND_DOWN

    # Check if price is mostly ranging
    recent_closes = df["close"].tail(50)
    pct_range = (recent_closes.max() - recent_closes.min()) / recent_closes.mean()

    if pct_range < 0.03:
        return MarketRegime.RANGE

    return MarketRegime.CHOPPY


def compute_volatility_regime(df: pd.DataFrame) -> str:
    """
    Classify volatility as 'low', 'medium', or 'high'.

    Based on Bollinger Band width relative to price.
    """
    last = df.iloc[-1]
    width = float(last.get("bb_width", 0.0))
    price = float(last["close"])
    if price == 0:
        return "unknown"

    rel_width = width / price
    if rel_width < 0.02:
        return "low"
    if rel_width < 0.05:
        return "medium"
    return "high"
