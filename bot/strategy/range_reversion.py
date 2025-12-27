from __future__ import annotations

from typing import Optional

import pandas as pd

from bot.models import MarketRegime, RiskRating, TradeAction, TradeSignal


class RangeReversionStrategy:
    """Fade extremes inside a sideways range."""

    name = "RangeReversion"
    description = (
        "Range-trading setup that looks for mean reversion near support and "
        "resistance levels."
    )
    regimes = [MarketRegime.RANGE]
    risk_profile = "conservative"

    def generate_signal(
        self,
        df: pd.DataFrame,
        symbol: str,
        timeframe: str,
        regime: MarketRegime,
    ) -> Optional[TradeSignal]:
        if regime != MarketRegime.RANGE:
            print("[RangeReversion] Skipped: regime not RANGE")
            return None

        last = df.iloc[-1]
        close = float(last["close"])
        rsi = float(last["rsi14"])

        recent = df.tail(50)
        range_high = float(recent["high"].max())
        range_low = float(recent["low"].min())

        range_height = range_high - range_low
        if range_height <= 0:
            print("[RangeReversion] Skipped: invalid range height")
            return None

        # Require that price has been coiling; otherwise skip
        compression = range_height / max(float(recent["close"].mean()), 1e-9)
        if compression > 0.08:
            print("[RangeReversion] Skipped: range too wide for mean reversion")
            return None

        support_zone = (range_low * 0.995, range_low * 1.01)
        resistance_zone = (range_high * 0.99, range_high * 1.005)

        if support_zone[0] <= close <= support_zone[1] and rsi < 38:
            sl = range_low * 0.99
            tp = close * 1.025
            return TradeSignal(
                symbol=symbol,
                timeframe=timeframe,
                action=TradeAction.BUY,
                strategy_name=self.name,
                entry_zone=support_zone,
                stop_loss=sl,
                take_profits=[tp],
                risk_rating=RiskRating.MEDIUM,
                confidence_score=0.6,
                regime=regime,
                context={
                    "close": close,
                    "rsi14": rsi,
                    "range_low": range_low,
                    "range_high": range_high,
                    "compression": compression,
                },
            )

        if resistance_zone[0] <= close <= resistance_zone[1] and rsi > 62:
            sl = range_high * 1.01
            tp = close * 0.975
            return TradeSignal(
                symbol=symbol,
                timeframe=timeframe,
                action=TradeAction.SELL,
                strategy_name=self.name,
                entry_zone=resistance_zone,
                stop_loss=sl,
                take_profits=[tp],
                risk_rating=RiskRating.HIGH,
                confidence_score=0.6,
                regime=regime,
                context={
                    "close": close,
                    "rsi14": rsi,
                    "range_low": range_low,
                    "range_high": range_high,
                    "compression": compression,
                },
            )

        return None
