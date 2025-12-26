from __future__ import annotations

import pandas as pd
from ta.trend import EMAIndicator, MACD
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands


def add_basic_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add common indicators to the DataFrame.

    Assumes columns: ['open', 'high', 'low', 'close', 'volume'].
    """
    df = df.copy()

    close = df["close"]

    # EMAs
    df["ema20"] = EMAIndicator(close=close, window=20).ema_indicator()
    df["ema50"] = EMAIndicator(close=close, window=50).ema_indicator()
    df["ema200"] = EMAIndicator(close=close, window=200).ema_indicator()

    # RSI
    df["rsi14"] = RSIIndicator(close=close, window=14).rsi()

    # MACD
    macd = MACD(
        close=close,
        window_slow=26,
        window_fast=12,
        window_sign=9,
    )
    df["macd"] = macd.macd()
    df["macd_signal"] = macd.macd_signal()
    df["macd_hist"] = macd.macd_diff()

    # Bollinger Bands
    bb = BollingerBands(close=close, window=20, window_dev=2)
    df["bb_high"] = bb.bollinger_hband()
    df["bb_low"] = bb.bollinger_lband()
    df["bb_mid"] = bb.bollinger_mavg()
    df["bb_width"] = df["bb_high"] - df["bb_low"]

    return df
