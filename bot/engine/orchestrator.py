from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional, List

import pandas as pd

from bot.data.client import ExchangeClient
from bot.indicators.core import add_basic_indicators
from bot.engine.regime import detect_regime
from bot.models import TradeSignal, TradeAction, RiskRating, MarketRegime
from bot.strategy.registry import get_strategy_registry


def _mock_uptrend_df(n: int = 200) -> pd.DataFrame:
    """
    Create a synthetic strong uptrend dataset for demo/testing.

    Used when use_mock=True so demo mode always has a clean uptrend.
    """
    now = datetime.utcnow()
    # 5-minute candles going back n steps
    ts = [now - timedelta(minutes=5 * (n - i)) for i in range(n)]
    close = [100 + i * 0.5 for i in range(n)]

    df = pd.DataFrame(
        {
            "timestamp": ts,
            "open": close,
            "high": [c * 1.01 for c in close],
            "low": [c * 0.99 for c in close],
            "close": close,
            "volume": [1000.0] * n,
        }
    )
    df = add_basic_indicators(df)
    df = df.dropna()
    return df


class SignalEngine:
    """High level engine that generates final trade signals."""

    def __init__(self, exchange_client: Optional[ExchangeClient] = None) -> None:
        self.exchange_client = exchange_client or ExchangeClient()

    def generate_signal(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 200,
        use_mock: bool = False,
        enabled_strategies: List[str] | None = None,
    ) -> Optional[TradeSignal]:
        """
        Full pipeline to produce a TradeSignal.

        If use_mock is True, uses synthetic uptrend data and will always
        return a BUY signal (either from a real strategy or a demo fallback).
        Otherwise fetches real candles via ccxt.
        """
        # 1) Data
        if use_mock:
            df = _mock_uptrend_df(limit)
            print(f"[SignalEngine] Using MOCK data for demo: {len(df)} candles")
        else:
            df = self.exchange_client.get_recent_candles(
                symbol=symbol,
                timeframe=timeframe,
                limit=limit,
            )
            print(f"[SignalEngine] Fetched {len(df)} candles for {symbol} {timeframe}")

            if df.empty:
                print("[SignalEngine] No candles returned from exchange")
                return None

            df = add_basic_indicators(df)
            df = df.dropna()
            print(f"[SignalEngine] After indicators & dropna: {len(df)} rows")

            if len(df) == 0:
                print("[SignalEngine] No rows after indicators (all NaN?)")
                return None

        # 2) Regime
        if use_mock:
            regime = MarketRegime.TREND_UP
        else:
            regime = detect_regime(df)
        print(f"[SignalEngine] Regime for {symbol} {timeframe}: {regime}")

        # 3) Strategies for this regime
        registry = get_strategy_registry()
        strategies = registry.get(regime, [])
        if enabled_strategies:
            enabled_set = set(enabled_strategies)
            strategies = [
                s for s in strategies if getattr(s, "name", "") in enabled_set
            ]
        print(
            "[SignalEngine] Strategies for regime",
            regime,
            "=>",
            [getattr(s, "name", s.__class__.__name__) for s in strategies],
        )

        best_signal: Optional[TradeSignal] = None

        for strat in strategies:
            name = getattr(strat, "name", strat.__class__.__name__)
            try:
                sig = strat.generate_signal(df, symbol, timeframe, regime)
            except Exception as exc:  # keep engine alive even if one strategy bugs
                print(f"[SignalEngine] Strategy {name} raised: {exc!r}")
                continue

            if sig is None:
                print(f"[SignalEngine] Strategy {name} -> None")
                continue

            print(
                f"[SignalEngine] Strategy {name} -> action={sig.action} "
                f"conf={sig.confidence_score}"
            )

            if best_signal is None or sig.confidence_score > best_signal.confidence_score:
                best_signal = sig

        # 4) Demo fallback: always BUY if use_mock
        if best_signal is None and use_mock:
            last = df.iloc[-1]
            price = float(last["close"])
            ema20 = float(last.get("ema20", price))
            ema50 = float(last.get("ema50", price * 0.99))
            rsi14 = float(last.get("rsi14", 60.0))

            best_signal = TradeSignal(
                symbol=symbol,
                timeframe=timeframe,
                action=TradeAction.BUY,
                strategy_name="DemoTrendContinuation",
                entry_zone=(price * 0.995, price * 1.005),
                stop_loss=price * 0.985,
                take_profits=[price * 1.02, price * 1.04],
                risk_rating=RiskRating.MEDIUM,
                confidence_score=0.9,
                regime=MarketRegime.TREND_UP,
                context={
                    "close": price,
                    "ema20": ema20,
                    "ema50": ema50,
                    "rsi14": rsi14,
                },
            )
            print("[SignalEngine] DEMO fallback BUY created")

        if best_signal is None:
            print("[SignalEngine] No valid signal found (real mode)")
        else:
            print(
                f"[SignalEngine] BEST signal: action={best_signal.action} "
                f"conf={best_signal.confidence_score}"
            )

        return best_signal
