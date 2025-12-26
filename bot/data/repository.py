from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from typing import Optional

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
                    strategy TEXT NOT NULL,
                    start INTEGER NOT NULL,
                    end INTEGER NOT NULL,
                    metrics_json TEXT,
                    created_at INTEGER NOT NULL
                )
                """,
            )
            self._migrate_backtests_table(cur)
            conn.commit()
        finally:
            conn.close()

    def _migrate_backtests_table(self, cur: sqlite3.Cursor) -> None:
        """Add any missing columns for the backtests table without dropping data."""
        required_columns = {
            "strategy": "TEXT NOT NULL DEFAULT ''",
            "start": "INTEGER NOT NULL DEFAULT 0",
            "end": "INTEGER NOT NULL DEFAULT 0",
            "metrics_json": "TEXT",
            "created_at": "INTEGER NOT NULL DEFAULT 0",
        }
        existing_columns = {
            row[1] for row in cur.execute("PRAGMA table_info(backtests)").fetchall()
        }
        for column_name, column_type in required_columns.items():
            if column_name not in existing_columns:
                cur.execute(
                    f"ALTER TABLE backtests ADD COLUMN {column_name} {column_type}"
                )

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

    def save_backtest_result(
        self,
        symbol: str,
        timeframe: str,
        strategy: str,
        start: datetime,
        end: datetime,
        metrics: dict,
    ) -> None:
        conn = self._connect()
        try:
            conn.execute(
                """
                INSERT INTO backtests (symbol, timeframe, strategy, start, end, metrics_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    symbol,
                    timeframe,
                    strategy,
                    int(start.timestamp()),
                    int(end.timestamp()),
                    json.dumps(metrics),
                    int(datetime.utcnow().timestamp()),
                ),
            )
            conn.commit()
        finally:
            conn.close()
