from __future__ import annotations

from typing import Optional

import pandas as pd

from bot.models import MarketRegime, RiskRating, TradeAction, TradeSignal


class RangeReversionStrategy:
    """Fade extremes in clear ranges with RSI oversold or overbought."""

    name = "RangeReversion"

    def generate_signal(
        self,
        df: pd.DataFrame,
        symbol: str,
        timeframe: str,
        regime: MarketRegime,
    ) -> Optional[TradeSignal]:
        if regime != MarketRegime.RANGE:
            return None

        last = df.iloc[-1]
        close = float(last["close"])
        rsi = float(last["rsi14"])

        recent = df.tail(50)
        range_high = float(recent["high"].max())
        range_low = float(recent["low"].min())

        support_zone = (range_low * 0.995, range_low * 1.01)
        resistance_zone = (range_high * 0.99, range_high * 1.005)

        if support_zone[0] <= close <= support_zone[1] and rsi < 35:
            sl = range_low * 0.99
            tp = close * 1.03
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
                },
            )

        if resistance_zone[0] <= close <= resistance_zone[1] and rsi > 65:
            sl = range_high * 1.01
            tp = close * 0.97
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
                },
            )

        return None
