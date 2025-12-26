from __future__ import annotations

import os
from datetime import datetime
from typing import Optional

import ccxt
import pandas as pd


class ExchangeClient:
    """Simple wrapper around ccxt for one exchange."""

    def __init__(self, exchange_id: Optional[str] = None) -> None:
        # Use env var override if set, otherwise default to Kraken
        self.exchange_id = exchange_id or os.getenv("EXCHANGE_ID", "kraken")
        self.exchange = getattr(ccxt, self.exchange_id)({
            "enableRateLimit": True,
        })

    def get_recent_candles(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 200,
    ) -> pd.DataFrame:
        """
        Fetch recent OHLCV candles for symbol and timeframe.

        Returns a DataFrame with columns:
        ['timestamp', 'open', 'high', 'low', 'close', 'volume'].
        """
        raw = self.exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        df = pd.DataFrame(
            raw,
            columns=["timestamp", "open", "high", "low", "close", "volume"],
        )
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        return df

    def sync_historical_candles(
        self,
        symbol: str,
        timeframe: str,
        since: Optional[datetime] = None,
        limit: int = 1000,
    ) -> pd.DataFrame:
        """
        Fetch historical OHLCV candles starting from 'since'.

        For now returns a DataFrame. The repository can store it.
        """
        since_ms = int(since.timestamp() * 1000) if since else None
        all_rows = []
        while True:
            batch = self.exchange.fetch_ohlcv(
                symbol,
                timeframe=timeframe,
                since=since_ms,
                limit=limit,
            )
            if not batch:
                break
            all_rows.extend(batch)
            if len(batch) < limit:
                break
            since_ms = batch[-1][0] + 1

        if not all_rows:
            return pd.DataFrame(
                columns=["timestamp", "open", "high", "low", "close", "volume"],
            )
        df = pd.DataFrame(
            all_rows,
            columns=["timestamp", "open", "high", "low", "close", "volume"],
        )
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        return df
