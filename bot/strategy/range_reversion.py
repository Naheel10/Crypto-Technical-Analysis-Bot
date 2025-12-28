from __future__ import annotations

from typing import List

import pandas as pd

from bot.models import (
    CandidateTrade,
    MarketRegime,
    RiskRating,
    SetupType,
    TradeDirection,
)


class RangeReversionStrategy:
    """Fade extremes inside a sideways range."""

    name = "RangeReversion"
    description = (
        "Range-trading setup that looks for mean reversion near support and "
        "resistance levels."
    )
    regimes = [MarketRegime.RANGE]
    risk_profile = "conservative"

    def generate_candidates(
        self,
        df: pd.DataFrame,
        symbol: str,
        timeframe: str,
        regime: MarketRegime,
    ) -> List[CandidateTrade]:
        if regime != MarketRegime.RANGE:
            print("[RangeReversion] Skipped: regime not RANGE")
            return []

        last = df.iloc[-1]
        close = float(last["close"])
        rsi = float(last["rsi14"])

        recent = df.tail(50)
        range_high = float(recent["high"].max())
        range_low = float(recent["low"].min())

        range_height = range_high - range_low
        if range_height <= 0:
            print("[RangeReversion] Skipped: invalid range height")
            return []

        # Require that price has been coiling; otherwise skip
        compression = range_height / max(float(recent["close"].mean()), 1e-9)
        if compression > 0.08:
            print("[RangeReversion] Skipped: range too wide for mean reversion")
            return []

        support_zone = (range_low * 0.995, range_low * 1.01)
        resistance_zone = (range_high * 0.99, range_high * 1.005)

        candidates: list[CandidateTrade] = []

        if support_zone[0] <= close <= support_zone[1]:
            sl = range_low * 0.99
            tp = close * 1.025
            quality = 0.45
            quality += min(0.25, max(0, (40 - rsi) / 100))
            candidates.append(
                CandidateTrade(
                    direction=TradeDirection.LONG,
                    setup_type=SetupType.RANGE_REVERSION,
                    entry_zone=support_zone,
                    stop_loss=sl,
                    take_profits=[tp],
                    quality_score=min(quality, 0.95),
                    risk_rating=RiskRating.MEDIUM,
                    notes=(
                        "Price near range support with soft momentum exhaustion; looking for bounce back to mid-range."
                    ),
                    strategy_name=self.name,
                )
            )

        if resistance_zone[0] <= close <= resistance_zone[1]:
            sl = range_high * 1.01
            tp = close * 0.975
            quality = 0.45
            quality += min(0.25, max(0, (rsi - 60) / 100))
            candidates.append(
                CandidateTrade(
                    direction=TradeDirection.SHORT,
                    setup_type=SetupType.RANGE_REVERSION,
                    entry_zone=resistance_zone,
                    stop_loss=sl,
                    take_profits=[tp],
                    quality_score=min(quality, 0.95),
                    risk_rating=RiskRating.HIGH,
                    notes=(
                        "Price stalling near range resistance with stretched RSI; mean reversion short idea."
                    ),
                    strategy_name=self.name,
                )
            )

        return candidates
