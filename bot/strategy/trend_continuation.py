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
    """Bias long in clear uptrends with reasonably soft pullback rules."""

    name = "TrendContinuation"

    def generate_signal(
        self,
        df: pd.DataFrame,
        symbol: str,
        timeframe: str,
        regime: MarketRegime,
    ) -> Optional[TradeSignal]:
        """Return a TradeSignal if a valid trend continuation setup exists."""

        # Prefer uptrends, but also allow BREAKOUT or UNKNOWN
        if regime not in (
            MarketRegime.TREND_UP,
            MarketRegime.BREAKOUT,
            MarketRegime.UNKNOWN,
        ):
            return None

        last = df.iloc[-1]
        close = float(last["close"])
        ema20 = float(last.get("ema20", close))
        ema50 = float(last.get("ema50", close * 0.99))
        ema200 = float(last.get("ema200", ema50 * 0.99))
        rsi = float(last.get("rsi14", 55.0))

        # 1) Trend filter: EMAs stacked or at least 20 > 50 and price above 20
        ema_trend_ok = (ema20 > ema50 > ema200) or (ema20 > ema50 and close > ema20)
        if not ema_trend_ok:
            return None

        # 2) Pullback zone: within ~3% of EMA20
        pullback_ok = ema20 * 0.97 <= close <= ema20 * 1.03

        # 3) RSI in "healthy" zone: not oversold, not crazy overbought
        rsi_ok = 45 <= rsi <= 75

        if not (pullback_ok and rsi_ok):
            return None

        # Stop loss at recent swing low with tiny buffer
        recent_lows = df["low"].tail(15)
        swing_low = float(recent_lows.min())
        sl = swing_low * 0.995

        # Take profits 2% and 4% above current
        tp1 = close * 1.02
        tp2 = close * 1.04

        return TradeSignal(
            symbol=symbol,
            timeframe=timeframe,
            action=TradeAction.BUY,
            strategy_name=self.name,
            entry_zone=(ema20 * 0.97, ema20 * 1.03),
            stop_loss=sl,
            take_profits=[tp1, tp2],
            risk_rating=RiskRating.MEDIUM,
            confidence_score=0.7,
            regime=regime,
            context={
                "close": close,
                "ema20": ema20,
                "ema50": ema50,
                "ema200": ema200,
                "rsi14": rsi,
            },
        )
