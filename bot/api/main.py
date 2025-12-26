from __future__ import annotations

from datetime import datetime
from typing import Optional, Type

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from bot.ai.explanation import generate_explanation
from bot.api.schemas import BacktestResponse, TradeSignalResponse
from bot.backtest.engine import Backtester, BacktestResult
from bot.engine.orchestrator import SignalEngine
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

    result: BacktestResult = backtester.run_backtest(
        symbol=symbol,
        timeframe=timeframe,
        strategy_cls=strategy_cls,
        start=start,
        end=end,
    )

    return BacktestResponse(**result.__dict__)
