from __future__ import annotations

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
                    created_at INTEGER NOT NULL,
                    symbol TEXT NOT NULL,
                    timeframe TEXT NOT NULL,
                    strategy_name TEXT NOT NULL,
                    start INTEGER NOT NULL,
                    end INTEGER NOT NULL,
                    win_rate REAL NOT NULL,
                    total_return_pct REAL NOT NULL,
                    max_drawdown_pct REAL NOT NULL,
                    profit_factor REAL NOT NULL,
                    trades_count INTEGER NOT NULL
                )
                """,
            )
            self._migrate_backtests_table(cur)
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS signals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at INTEGER NOT NULL,
                    symbol TEXT NOT NULL,
                    timeframe TEXT NOT NULL,
                    action TEXT NOT NULL,
                    strategy_name TEXT NOT NULL,
                    risk_rating TEXT NOT NULL,
                    confidence_score REAL NOT NULL,
                    regime TEXT NOT NULL,
                    entry_zone_low REAL,
                    entry_zone_high REAL,
                    stop_loss REAL,
                    tp1 REAL,
                    tp2 REAL
                )
                """,
            )
            conn.commit()
        finally:
            conn.close()

    def _migrate_backtests_table(self, cur: sqlite3.Cursor) -> None:
        """Add any missing columns for the backtests table without dropping data."""
        required_columns = {
            "created_at": "INTEGER NOT NULL DEFAULT 0",
            "symbol": "TEXT NOT NULL DEFAULT ''",
            "timeframe": "TEXT NOT NULL DEFAULT ''",
            "strategy_name": "TEXT NOT NULL DEFAULT ''",
            "start": "INTEGER NOT NULL DEFAULT 0",
            "end": "INTEGER NOT NULL DEFAULT 0",
            "win_rate": "REAL NOT NULL DEFAULT 0",
            "total_return_pct": "REAL NOT NULL DEFAULT 0",
            "max_drawdown_pct": "REAL NOT NULL DEFAULT 0",
            "profit_factor": "REAL NOT NULL DEFAULT 0",
            "trades_count": "INTEGER NOT NULL DEFAULT 0",
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

    def log_backtest(self, result) -> None:
        """Persist a backtest result for history browsing."""

        conn = self._connect()
        try:
            conn.execute(
                """
                INSERT INTO backtests (
                    created_at, symbol, timeframe, strategy_name, start, end,
                    win_rate, total_return_pct, max_drawdown_pct, profit_factor, trades_count
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    int(datetime.utcnow().timestamp()),
                    result.symbol,
                    result.timeframe,
                    result.strategy_name,
                    int(result.start.timestamp()),
                    int(result.end.timestamp()),
                    float(result.win_rate),
                    float(result.total_return_pct),
                    float(result.max_drawdown_pct),
                    float(result.profit_factor),
                    int(result.trades_count),
                ),
            )
            conn.commit()
        finally:
            conn.close()

    def get_recent_backtests(self, limit: int = 20) -> list[dict]:
        """Return the most recent backtests ordered newest first."""

        conn = self._connect()
        try:
            cursor = conn.execute(
                """
                SELECT
                    id, created_at, symbol, timeframe, strategy_name, start, end,
                    win_rate, total_return_pct, max_drawdown_pct, profit_factor, trades_count
                FROM backtests
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            )
            rows = cursor.fetchall()
            return [
                {
                    "id": row[0],
                    "created_at": datetime.utcfromtimestamp(row[1]),
                    "symbol": row[2],
                    "timeframe": row[3],
                    "strategy_name": row[4],
                    "start": datetime.utcfromtimestamp(row[5]),
                    "end": datetime.utcfromtimestamp(row[6]),
                    "win_rate": float(row[7]),
                    "total_return_pct": float(row[8]),
                    "max_drawdown_pct": float(row[9]),
                    "profit_factor": float(row[10]),
                    "trades_count": int(row[11]),
                }
                for row in rows
            ]
        finally:
            conn.close()

    def log_signal(self, signal) -> None:
        """Persist a TradeSignal for history/auditing."""

        entry_low = None
        entry_high = None
        if signal.entry_zone:
            entry_low, entry_high = signal.entry_zone

        tp1 = None
        tp2 = None
        if signal.take_profits:
            if len(signal.take_profits) > 0:
                tp1 = signal.take_profits[0]
            if len(signal.take_profits) > 1:
                tp2 = signal.take_profits[1]

        conn = self._connect()
        try:
            conn.execute(
                """
                INSERT INTO signals (
                    created_at, symbol, timeframe, action, strategy_name, risk_rating,
                    confidence_score, regime, entry_zone_low, entry_zone_high,
                    stop_loss, tp1, tp2
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    int(datetime.utcnow().timestamp()),
                    signal.symbol,
                    signal.timeframe,
                    getattr(signal.action, "value", signal.action),
                    signal.strategy_name,
                    getattr(signal.risk_rating, "value", signal.risk_rating),
                    float(signal.confidence_score),
                    getattr(signal.regime, "value", signal.regime),
                    entry_low,
                    entry_high,
                    signal.stop_loss,
                    tp1,
                    tp2,
                ),
            )
            conn.commit()
        finally:
            conn.close()

    def get_recent_signals(self, limit: int = 20) -> list[dict]:
        """Return the most recent logged signals ordered newest first."""

        conn = self._connect()
        try:
            cursor = conn.execute(
                """
                SELECT
                    id, created_at, symbol, timeframe, action, strategy_name,
                    risk_rating, confidence_score, regime
                FROM signals
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            )
            rows = cursor.fetchall()
            return [
                {
                    "id": row[0],
                    "created_at": datetime.utcfromtimestamp(row[1]),
                    "symbol": row[2],
                    "timeframe": row[3],
                    "action": row[4],
                    "strategy_name": row[5],
                    "risk_rating": row[6],
                    "confidence_score": row[7],
                    "regime": row[8],
                }
                for row in rows
            ]
        finally:
            conn.close()
