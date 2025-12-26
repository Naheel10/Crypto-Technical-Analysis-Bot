from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

import pandas as pd

from bot.models import MarketRegime, TradeSignal


class BaseStrategy(ABC):
    """Base class for all TA strategies."""

    name: str

    @abstractmethod
    def generate_signal(
        self,
        df: pd.DataFrame,
        symbol: str,
        timeframe: str,
        regime: MarketRegime,
    ) -> Optional[TradeSignal]:
        """
        Inspect the latest candles and emit a TradeSignal or None.

        df is assumed to already have indicators added.
        """
        raise NotImplementedError
