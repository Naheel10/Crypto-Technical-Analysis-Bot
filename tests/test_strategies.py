from datetime import datetime, timedelta

import pandas as pd

from bot.indicators.core import add_basic_indicators
from bot.models import MarketRegime
from bot.strategy.trend_continuation import TrendContinuationStrategy


def _mock_uptrend_df(n: int = 60) -> pd.DataFrame:
    ts = [datetime.utcnow() - timedelta(minutes=5 * (n - i)) for i in range(n)]
    close = [100 + i * 0.5 for i in range(n)]
    df = pd.DataFrame(
        {
            "timestamp": ts,
            "open": close,
            "high": [c * 1.01 for c in close],
            "low": [c * 0.99 for c in close],
            "close": close,
            "volume": [1000] * n,
        },
    )
    df = add_basic_indicators(df)
    df = df.dropna()
    return df


def test_trend_continuation_generates_buy_in_uptrend():
    df = _mock_uptrend_df()
    strat = TrendContinuationStrategy()
    signal = strat.generate_signal(
        df=df,
        symbol="TEST/USDT",
        timeframe="1h",
        regime=MarketRegime.TREND_UP,
    )
    assert signal is not None
    assert signal.action.value == "BUY"
