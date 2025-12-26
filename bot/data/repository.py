from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional

import pandas as pd


class DataRepository:
    """
    Simple SQLite repository for candles and backtest results.

    This is intentionally minimal for v1.
    """

    def __init__(self, db_path: str = "data.db") -> None:
        self.db_path = db_path
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_schema(self) -> None:
        conn = self._connect()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS candles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    timeframe TEXT NOT NULL,
                    timestamp INTEGER NOT NULL,
                    open REAL NOT NULL,
                    high REAL NOT NULL,
                    low REAL NOT NULL,
                    close REAL NOT NULL,
                    volume REAL NOT NULL,
                    UNIQUE(symbol, timeframe, timestamp)
                )
                """,
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS backtests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    timeframe TEXT NOT NULL,
                    strategy_name TEXT NOT NULL,
                    start_ts INTEGER NOT NULL,
                    end_ts INTEGER NOT NULL,
                    win_rate REAL,
                    total_return REAL,
                    max_drawdown REAL,
                    profit_factor REAL,
                    trades_count INTEGER,
                    created_at INTEGER NOT NULL
                )
                """,
            )
            conn.commit()
        finally:
            conn.close()

    def save_candles(
        self,
        symbol: str,
        timeframe: str,
        candles: pd.DataFrame,
    ) -> None:
        """
        Save candle DataFrame to DB.

        Expects columns: timestamp, open, high, low, close, volume.
        """
        conn = self._connect()
        try:
            rows = [
                (
                    symbol,
                    timeframe,
                    int(row["timestamp"].timestamp()),
                    float(row["open"]),
                    float(row["high"]),
                    float(row["low"]),
                    float(row["close"]),
                    float(row["volume"]),
                )
                for _, row in candles.iterrows()
            ]
            conn.executemany(
                """
                INSERT OR IGNORE INTO candles
                (symbol, timeframe, timestamp, open, high, low, close, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                rows,
            )
            conn.commit()
        finally:
            conn.close()

    def load_candles(
        self,
        symbol: str,
        timeframe: str,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> pd.DataFrame:
        """Load candles for symbol and timeframe from DB."""
        conn = self._connect()
        try:
            params: list = [symbol, timeframe]
            query = """
                SELECT timestamp, open, high, low, close, volume
                FROM candles
                WHERE symbol = ? AND timeframe = ?
            """
            if start:
                query += " AND timestamp >= ?"
                params.append(int(start.timestamp()))
            if end:
                query += " AND timestamp <= ?"
                params.append(int(end.timestamp()))
            query += " ORDER BY timestamp ASC"
            df = pd.read_sql_query(query, conn, params=params)
            if not df.empty:
                df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s")
            return df
        finally:
            conn.close()
