from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

import pandas as pd

from bot.models import CandidateTrade, MarketRegime


class BaseStrategy(ABC):
    """Base class for all TA strategies."""

    name: str

    @abstractmethod
    def generate_candidates(
        self,
        df: pd.DataFrame,
        symbol: str,
        timeframe: str,
        regime: MarketRegime,
    ) -> List[CandidateTrade]:
        """Inspect the latest candles and emit possible trade ideas."""

        raise NotImplementedError
