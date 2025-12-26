from __future__ import annotations

from datetime import datetime
from typing import Optional, Type

import pandas as pd

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from bot.ai.explanation import generate_explanation
from bot.api.schemas import CandlesResponse, BacktestResponse, TradeSignalResponse
from bot.backtest.engine import Backtester, BacktestResult
from bot.engine.orchestrator import SignalEngine
from bot.indicators.core import add_basic_indicators
from bot.models import (
    TradeSignal,
    TradeAction,
    RiskRating,
    MarketRegime,
)
from bot.strategy.trend_continuation import TrendContinuationStrategy
from bot.strategy.range_reversion import RangeReversionStrategy
from bot.strategy.base import BaseStrategy


app = FastAPI(
    title="Crypto Technical Analysis Bot for Beginners",
    description="Beginner friendly crypto trading assistant that turns raw charts into clear BUY / SELL / NO-TRADE ideas.",
    version="0.1.0",
)

# --- CORS setup for frontend on Vite dev server ---
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# --- end CORS setup ---


signal_engine = SignalEngine()
backtester = Backtester()


STRATEGY_MAP: dict[str, Type[BaseStrategy]] = {
    "TrendContinuation": TrendContinuationStrategy,
    "RangeReversion": RangeReversionStrategy,
}


@app.get("/signal", response_model=TradeSignalResponse)
def get_signal(
    symbol: str = Query(..., example="BTC/USDT"),
    timeframe: str = Query(..., example="1h"),
    demo: bool = Query(
        False,
        description="Use mock uptrend data for a guaranteed BUY demo",
    ),
) -> TradeSignalResponse:
    try:
        signal: Optional[TradeSignal] = signal_engine.generate_signal(
            symbol=symbol,
            timeframe=timeframe,
            use_mock=demo,
        )
    except Exception as exc:  # debug guard
        print("ERROR while generating signal:", repr(exc))
        raise HTTPException(status_code=500, detail=f"Signal generation failed: {exc}")

    # If no strategy found a setup, return an explicit NO_TRADE signal
    if signal is None:
        signal = TradeSignal(
            symbol=symbol,
            timeframe=timeframe,
            action=TradeAction.NO_TRADE,
            strategy_name="NoValidSetup",
            entry_zone=None,
            stop_loss=None,
            take_profits=None,
            risk_rating=RiskRating.LOW,
            confidence_score=0.0,
            regime=MarketRegime.UNKNOWN,
            context={},
        )

    explanation = generate_explanation(
        signal=signal,
        context=signal.context,
    )

    return TradeSignalResponse(
        simple_explanation=explanation,
        **signal.to_dict(),
    )





@app.get("/candles", response_model=CandlesResponse)
def get_candles(
    symbol: str = Query(..., example="BTC/USDT"),
    timeframe: str = Query(..., example="1h"),
    limit: int = Query(200, ge=20, le=1000),
) -> CandlesResponse:
    try:
        df = signal_engine.exchange_client.get_recent_candles(
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
        )
    except Exception as exc:
        print("ERROR while fetching candles:", repr(exc))
        raise HTTPException(status_code=500, detail="Failed to load candles")

    if df is None or df.empty:
        raise HTTPException(status_code=404, detail="No candles returned for that market")

    df = add_basic_indicators(df)

    candles = []
    for _, row in df.iterrows():
        candles.append(
            {
                "timestamp": row["timestamp"].to_pydatetime(),
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "volume": float(row["volume"]),
                "ema20": None if pd.isna(row.get("ema20")) else float(row.get("ema20")),
                "ema50": None if pd.isna(row.get("ema50")) else float(row.get("ema50")),
                "ema200": None if pd.isna(row.get("ema200")) else float(row.get("ema200")),
                "rsi14": None if pd.isna(row.get("rsi14")) else float(row.get("rsi14")),
                "macd": None if pd.isna(row.get("macd")) else float(row.get("macd")),
                "macd_signal": None if pd.isna(row.get("macd_signal")) else float(row.get("macd_signal")),
                "macd_hist": None if pd.isna(row.get("macd_hist")) else float(row.get("macd_hist")),
                "bb_high": None if pd.isna(row.get("bb_high")) else float(row.get("bb_high")),
                "bb_low": None if pd.isna(row.get("bb_low")) else float(row.get("bb_low")),
                "bb_mid": None if pd.isna(row.get("bb_mid")) else float(row.get("bb_mid")),
                "bb_width": None if pd.isna(row.get("bb_width")) else float(row.get("bb_width")),
            }
        )

    return CandlesResponse(
        symbol=symbol,
        timeframe=timeframe,
        candles=candles,
    )

@app.get("/backtest", response_model=BacktestResponse)
def run_backtest(
    symbol: str = Query(..., example="BTC/USDT"),
    timeframe: str = Query(..., example="1h"),
    strategy: str = Query(..., example="TrendContinuation"),
    start: datetime = Query(...),
    end: datetime = Query(...),
) -> BacktestResponse:
    strategy_cls = STRATEGY_MAP.get(strategy)
    if strategy_cls is None:
        raise HTTPException(status_code=400, detail="Unknown strategy")

    try:
        result: BacktestResult = backtester.run_backtest(
            symbol=symbol,
            timeframe=timeframe,
            strategy_cls=strategy_cls,
            start=start,
            end=end,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    backtester.repository.save_backtest_result(
        symbol=symbol,
        timeframe=timeframe,
        strategy=strategy,
        start=start,
        end=end,
        metrics={
            "win_rate": result.win_rate,
            "total_return_pct": result.total_return_pct,
            "max_drawdown_pct": result.max_drawdown_pct,
            "profit_factor": result.profit_factor,
            "trades_count": result.trades_count,
        },
    )

    return BacktestResponse(**result.__dict__)
