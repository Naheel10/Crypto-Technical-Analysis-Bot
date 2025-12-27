from __future__ import annotations

import pandas as pd

from bot.models import MarketRegime


def _ema_slope(series: pd.Series, window: int = 15) -> float:
    """Return simple percentage slope over the provided window."""

    tail = series.tail(window)
    if len(tail) < 2:
        return 0.0

    start = float(tail.iloc[0])
    end = float(tail.iloc[-1])
    if start == 0:
        return 0.0

    return (end - start) / start


def compute_trend_direction(df: pd.DataFrame) -> MarketRegime:
    """
    Detect market regime using EMA stacking plus recent slopes.

    Uptrend: EMAs stacked upward with positive slope.
    Downtrend: EMAs stacked downward with negative slope.
    Range: flat-ish EMAs with compressed price range.
    Otherwise: choppy/unknown.
    """

    recent = df.tail(120) if len(df) > 120 else df
    last = recent.iloc[-1]
    ema20 = float(last["ema20"])
    ema50 = float(last["ema50"])
    ema200 = float(last.get("ema200", ema50))
    close = float(last["close"])

    ema20_slope = _ema_slope(recent["ema20"], window=25)
    ema50_slope = _ema_slope(recent["ema50"], window=35)

    stacked_up = ema20 > ema50 > ema200
    stacked_down = ema20 < ema50 < ema200

    # Require some directional slope so noisy periods don't count as trends
    if stacked_up and ema20_slope > 0.0015 and ema50_slope > 0.0005 and close > ema20:
        return MarketRegime.TREND_UP

    if stacked_down and ema20_slope < -0.0015 and ema50_slope < -0.0005 and close < ema20:
        return MarketRegime.TREND_DOWN

    # Range detection: small slopes + compressed prices around EMA50
    recent_closes = recent["close"].tail(60)
    if len(recent_closes) >= 20:
        pct_range = (recent_closes.max() - recent_closes.min()) / max(recent_closes.mean(), 1e-9)
        close_to_ema = abs(close - ema50) / max(ema50, 1e-9)
        if abs(ema20_slope) < 0.001 and abs(ema50_slope) < 0.0008 and pct_range < 0.05 and close_to_ema < 0.02:
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
