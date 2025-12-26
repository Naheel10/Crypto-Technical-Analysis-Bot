import pandas as pd

from bot.indicators.core import add_basic_indicators


def test_add_basic_indicators_shapes():
    data = {
        "open": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        "high": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        "low": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        "close": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        "volume": [100] * 10,
    }
    df = pd.DataFrame(data)
    df2 = add_basic_indicators(df)

    for col in ["ema20", "ema50", "ema200", "rsi14", "macd", "macd_signal", "bb_high"]:
        assert col in df2.columns
