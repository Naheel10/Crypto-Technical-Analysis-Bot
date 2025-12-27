from __future__ import annotations

from typing import Optional

import pandas as pd

from bot.models import (
    MarketRegime,
    RiskRating,
    TradeAction,
    TradeSignal,
)


class TrendContinuationStrategy:
    """Bias long in clear uptrends with pullback entries."""

    name = "TrendContinuation"
    description = (
        "Trend-following setup that looks for pullbacks in an uptrend with EMAs "
        "and RSI confirmation."
    )
    regimes = [MarketRegime.TREND_UP]
    risk_profile = "moderate"

    def generate_signal(
        self,
        df: pd.DataFrame,
        symbol: str,
        timeframe: str,
        regime: MarketRegime,
    ) -> Optional[TradeSignal]:
        """Return a TradeSignal if a valid trend continuation setup exists."""

        if regime != MarketRegime.TREND_UP:
            print("[TrendContinuation] Skipped: regime not TREND_UP")
            return None

        last = df.iloc[-1]
        close = float(last["close"])
        ema20 = float(last.get("ema20", close))
        ema50 = float(last.get("ema50", close * 0.99))
        ema200 = float(last.get("ema200", ema50 * 0.99))
        rsi = float(last.get("rsi14", 55.0))

        ema20_slope = (df["ema20"].iloc[-1] - df["ema20"].iloc[-8]) / max(
            df["ema20"].iloc[-8], 1e-9
        )
        ema50_slope = (df["ema50"].iloc[-1] - df["ema50"].iloc[-13]) / max(
            df["ema50"].iloc[-13], 1e-9
        )

        # 1) Trend filter: EMAs stacked or at least 20 > 50 and price above 20
        ema_trend_ok = (ema20 > ema50 > ema200) and ema20_slope > 0.0005
        if not ema_trend_ok:
            print("[TrendContinuation] Skipped: EMA alignment or slope weak")
            return None

        # 2) Pullback zone: within a soft band around EMA20 / EMA50
        pullback_band_low = min(ema20, ema50) * 0.985
        pullback_band_high = ema20 * 1.03
        pullback_ok = pullback_band_low <= close <= pullback_band_high

        # 3) RSI in "healthy" zone: not oversold, not crazy overbought
        rsi_ok = 50 <= rsi <= 68

        if not (pullback_ok and rsi_ok):
            print(
                "[TrendContinuation] Skipped: pullback or RSI filter failed",
                {"pullback_ok": pullback_ok, "rsi": rsi},
            )
            return None

        def _atr(data: pd.DataFrame, period: int = 14) -> float:
            highs = data["high"]
            lows = data["low"]
            closes = data["close"]
            prev_close = closes.shift(1)
            tr = pd.concat(
                [
                    highs - lows,
                    (highs - prev_close).abs(),
                    (lows - prev_close).abs(),
                ],
                axis=1,
            ).max(axis=1)
            return float(tr.rolling(period).mean().iloc[-1])

        recent_slice = df.tail(80)
        atr = _atr(recent_slice)

        # Stop loss at recent swing low with buffer informed by ATR
        recent_lows = df["low"].tail(20)
        swing_low = float(recent_lows.min())
        sl_buffer = atr * 0.8 if atr > 0 else swing_low * 0.003
        sl = min(swing_low - sl_buffer, close * 0.97)

        # Take profits using ATR projection to allow trend follow-through
        tp1 = close + (atr * 1.4 if atr > 0 else close * 0.02)
        tp2 = close + (atr * 2.4 if atr > 0 else close * 0.04)
        entry_zone = (pullback_band_low, max(pullback_band_high, ema50 * 1.01))

        confidence = min(0.9, 0.65 + ema20_slope * 8)

        return TradeSignal(
            symbol=symbol,
            timeframe=timeframe,
            action=TradeAction.BUY,
            strategy_name=self.name,
            entry_zone=entry_zone,
            stop_loss=sl,
            take_profits=[tp1, tp2],
            risk_rating=RiskRating.MEDIUM,
            confidence_score=confidence,
            regime=regime,
            context={
                "close": close,
                "ema20": ema20,
                "ema50": ema50,
                "ema200": ema200,
                "rsi14": rsi,
                "ema20_slope": ema20_slope,
                "ema50_slope": ema50_slope,
                "atr14": atr,
            },
        )
