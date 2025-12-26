from __future__ import annotations

import pandas as pd

from bot.indicators.features import compute_trend_direction
from bot.models import MarketRegime


def detect_regime(df: pd.DataFrame) -> MarketRegime:
    """
    Detect the current market regime using indicators and features.

    This function can be extended later.
    """
    regime = compute_trend_direction(df)
    return regime
