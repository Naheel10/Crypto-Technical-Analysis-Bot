from __future__ import annotations

from datetime import datetime
from typing import Optional, Type

import pandas as pd

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from bot.ai.explanation import generate_explanation
from bot.api.schemas import (
    CandlesResponse,
    BacktestResponse,
    BacktestHistoryItem,
    PositionSizingRequest,
    PositionSizingResponse,
    RecentBacktestsResponse,
    RecentSignalsResponse,
    SignalHistoryItem,
    SignalScanRequest,
    SignalScanResponse,
    SignalSummary,
    TradeSignalResponse,
    StrategyInfo,
    StrategyListResponse,
)
from bot.backtest.engine import Backtester, BacktestResult
from bot.data.repository import DataRepository
from bot.engine.risk import calculate_position_sizing
from bot.engine.orchestrator import SignalEngine
from bot.indicators.core import add_basic_indicators
from bot.models import (
    TradeSignal,
    TradeAction,
    RiskRating,
    MarketRegime,
)
from bot.strategy.registry import list_all_strategies
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
repository = DataRepository()
backtester = Backtester(repository)


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
    enabled_strategies: Optional[str] = Query(
        None,
        description="Comma-separated list of strategy names to enable (e.g. 'TrendContinuation,RangeReversion'). If omitted, all strategies are considered.",
    ),
) -> TradeSignalResponse:
    enabled_list: list[str] | None = None
    if enabled_strategies:
        enabled_list = [s.strip() for s in enabled_strategies.split(",") if s.strip()]

    try:
        signal: Optional[TradeSignal] = signal_engine.generate_signal(
            symbol=symbol,
            timeframe=timeframe,
            use_mock=demo,
            enabled_strategies=enabled_list,
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

    repository.log_signal(signal)

    return TradeSignalResponse(
        simple_explanation=explanation,
        **signal.to_dict(),
    )

@app.post("/signals/scan", response_model=SignalScanResponse)
def scan_signals(payload: SignalScanRequest) -> SignalScanResponse:
    if not payload.symbols:
        raise HTTPException(status_code=400, detail="Symbols list cannot be empty")

    max_symbols = 20
    if len(payload.symbols) > max_symbols:
        raise HTTPException(
            status_code=400,
            detail=f"Too many symbols requested. Max {max_symbols} allowed.",
        )

    summaries: list[SignalSummary] = []

    for symbol in payload.symbols:
        try:
            signal: Optional[TradeSignal] = signal_engine.generate_signal(
                symbol=symbol,
                timeframe=payload.timeframe,
                limit=payload.limit,
                use_mock=payload.demo,
                enabled_strategies=payload.enabled_strategies,
            )
        except Exception as exc:
            print("ERROR while generating signal:", repr(exc))
            raise HTTPException(
                status_code=500,
                detail=f"Signal generation failed for {symbol}: {exc}",
            )

        if signal is None:
            signal = TradeSignal(
                symbol=symbol,
                timeframe=payload.timeframe,
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

        summaries.append(
            SignalSummary(
                symbol=symbol,
                timeframe=payload.timeframe,
                action=signal.action,
                strategy_name=signal.strategy_name,
                risk_rating=signal.risk_rating,
                confidence_score=signal.confidence_score,
                regime=signal.regime,
                created_at=datetime.utcnow(),
                simple_explanation=None,
            )
        )

    return SignalScanResponse(items=summaries)


@app.get("/strategies", response_model=StrategyListResponse)
def list_strategies() -> StrategyListResponse:
    """Return metadata about all available strategies."""
    items: list[StrategyInfo] = []
    for strat_cls in list_all_strategies():
        name = getattr(strat_cls, "name", strat_cls.__name__)
        description = getattr(strat_cls, "description", "")
        regimes = getattr(strat_cls, "regimes", [])
        risk_profile = getattr(strat_cls, "risk_profile", "moderate")
        items.append(
            StrategyInfo(
                name=name,
                description=description,
                regimes=regimes,
                risk_profile=risk_profile,  # type: ignore[arg-type]
            )
        )
    return StrategyListResponse(items=items)


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

    repository.log_backtest(result)

    return BacktestResponse(**result.__dict__)


@app.get("/backtests/recent", response_model=RecentBacktestsResponse)
def get_recent_backtests(limit: int = 20) -> RecentBacktestsResponse:
    """
    Return the most recent backtest runs, newest first.
    """

    capped_limit = min(max(limit, 1), 100)
    rows = repository.get_recent_backtests(limit=capped_limit)

    items = [
        BacktestHistoryItem(
            id=row["id"],
            created_at=row["created_at"],
            symbol=row["symbol"],
            timeframe=row["timeframe"],
            strategy_name=row["strategy_name"],
            start=row["start"],
            end=row["end"],
            win_rate=row["win_rate"],
            total_return_pct=row["total_return_pct"],
            max_drawdown_pct=row["max_drawdown_pct"],
            profit_factor=row["profit_factor"],
            trades_count=row["trades_count"],
        )
        for row in rows
    ]

    return RecentBacktestsResponse(items=items)


@app.get("/signals/recent", response_model=RecentSignalsResponse)
def get_recent_signals(limit: int = 20) -> RecentSignalsResponse:
    capped_limit = min(max(limit, 1), 100)
    rows = repository.get_recent_signals(limit=capped_limit)

    items = [
        SignalHistoryItem(
            id=row["id"],
            created_at=row["created_at"],
            symbol=row["symbol"],
            timeframe=row["timeframe"],
            action=TradeAction(row["action"]),
            strategy_name=row["strategy_name"],
            risk_rating=RiskRating(row["risk_rating"]),
            confidence_score=float(row["confidence_score"]),
            regime=MarketRegime(row["regime"]),
        )
        for row in rows
    ]

    return RecentSignalsResponse(items=items)


@app.post("/risk/position", response_model=PositionSizingResponse)
def calculate_position(payload: PositionSizingRequest) -> PositionSizingResponse:
    return calculate_position_sizing(payload)
