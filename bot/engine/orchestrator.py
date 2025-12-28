from __future__ import annotations

from datetime import datetime, timedelta
from typing import List, Optional

import pandas as pd

from bot.data.client import ExchangeClient
from bot.indicators.core import add_basic_indicators
from bot.engine.regime import detect_regime
from bot.models import (
    AnalysisResult,
    AnalysisSnapshot,
    CandidateTrade,
    MarketRegime,
    MarketStructure,
    MomentumState,
    RiskRating,
    SetupType,
    TradeDirection,
    TrendBias,
    VolatilityRegime,
)
from bot.strategy.registry import get_strategy_registry


def select_primary_candidate(
    candidates: list[CandidateTrade], min_quality: float = 0.45
) -> Optional[CandidateTrade]:
    """Pick the highest quality candidate above the minimum threshold."""

    if not candidates:
        return None

    primary = max(candidates, key=lambda c: c.quality_score)
    if primary.quality_score < min_quality:
        return None
    return primary


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
    """High level engine that generates analysis snapshots and trade ideas."""

    def __init__(self, exchange_client: Optional[ExchangeClient] = None) -> None:
        self.exchange_client = exchange_client or ExchangeClient()

    def _build_snapshot(self, df: pd.DataFrame, symbol: str, timeframe: str) -> AnalysisSnapshot:
        last = df.iloc[-1]
        price = float(last["close"])
        ema20 = float(last.get("ema20", price)) if not pd.isna(last.get("ema20")) else None
        ema50 = float(last.get("ema50", price)) if not pd.isna(last.get("ema50")) else None
        ema200 = float(last.get("ema200", price)) if not pd.isna(last.get("ema200")) else None
        rsi14 = float(last.get("rsi14", 50.0)) if not pd.isna(last.get("rsi14")) else None
        macd_hist = float(last.get("macd_hist", 0.0)) if not pd.isna(last.get("macd_hist")) else None

        trend_bias = TrendBias.NEUTRAL
        if ema20 and ema50 and ema200:
            if price > ema20 > ema50 > ema200:
                trend_bias = TrendBias.STRONGLY_BULLISH
            elif price > ema50 > ema200:
                trend_bias = TrendBias.BULLISH
            elif price < ema20 < ema50 < ema200:
                trend_bias = TrendBias.STRONGLY_BEARISH
            elif price < ema50 < ema200:
                trend_bias = TrendBias.BEARISH

        structure = MarketStructure.TREND
        bb_width = float(last.get("bb_width", 0.0)) if not pd.isna(last.get("bb_width")) else 0.0
        if bb_width < 0.015:
            structure = MarketStructure.CHOP
        elif bb_width < 0.03:
            structure = MarketStructure.RANGE

        momentum_state = MomentumState.BUILDING
        if rsi14 is not None:
            if rsi14 > 70:
                momentum_state = MomentumState.EXTREME
            elif rsi14 < 45:
                momentum_state = MomentumState.FADING

        volatility_regime = VolatilityRegime.NORMAL
        if bb_width > 0.06:
            volatility_regime = VolatilityRegime.HIGH
        if bb_width > 0.12:
            volatility_regime = VolatilityRegime.INSANE
        if bb_width < 0.02:
            volatility_regime = VolatilityRegime.LOW

        recent = df.tail(120)
        swing_high = float(recent["high"].max())
        swing_low = float(recent["low"].min())
        mid = (swing_high + swing_low) / 2
        key_levels = [(swing_low, swing_low * 1.001), (mid * 0.995, mid * 1.005), (swing_high * 0.999, swing_high * 1.001)]

        return AnalysisSnapshot(
            symbol=symbol,
            timeframe=timeframe,
            trend_bias=trend_bias,
            structure=structure,
            momentum_state=momentum_state,
            volatility_regime=volatility_regime,
            key_levels=key_levels,
            latest_price=price,
            ema20=ema20,
            ema50=ema50,
            ema200=ema200,
            rsi14=rsi14,
            macd_hist=macd_hist,
        )

    def generate_signal(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 400,
        use_mock: bool = False,
        enabled_strategies: List[str] | None = None,
    ) -> Optional[AnalysisResult]:
        """Full pipeline to produce an AnalysisResult with candidate trades."""
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
            print(
                f"[SignalEngine] Fetched {len(df)} candles for {symbol} {timeframe} "
                f"(requested {limit})"
            )

            if df.empty:
                print("[SignalEngine] No candles returned from exchange")
                return None

            df = add_basic_indicators(df)
            print(
                f"[SignalEngine] After indicators (before dropna): {len(df)} rows"
            )
            df = df.dropna()
            print(
                f"[SignalEngine] After dropna: {len(df)} rows (indicator warmup removed)"
            )

            if len(df) < 120:
                print(
                    "[SignalEngine] Not enough history after indicator warmup for a stable read"
                )
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
        if not strategies:
            print(
                f"[SignalEngine] No strategies mapped for regime={regime} with enabled filter={enabled_strategies}"
            )
        print(
            "[SignalEngine] Strategies for regime",
            regime,
            "=>",
            [getattr(s, "name", s.__class__.__name__) for s in strategies],
        )

        all_candidates: list[CandidateTrade] = []
        for strat in strategies:
            name = getattr(strat, "name", strat.__class__.__name__)
            try:
                ideas = strat.generate_candidates(df, symbol, timeframe, regime)
            except Exception as exc:  # keep engine alive even if one strategy bugs
                print(f"[SignalEngine] Strategy {name} raised: {exc!r}")
                continue

            if not ideas:
                print(f"[SignalEngine] Strategy {name} -> no ideas")
                continue

            print(
                f"[SignalEngine] Strategy {name} produced {len(ideas)} candidates"
            )
            all_candidates.extend(ideas)

        # 4) Demo fallback: always a strong long idea if use_mock
        if use_mock and not all_candidates:
            last = df.iloc[-1]
            price = float(last["close"])
            all_candidates.append(
                CandidateTrade(
                    direction=TradeDirection.LONG,
                    setup_type=SetupType.PULLBACK,
                    entry_zone=(price * 0.995, price * 1.01),
                    stop_loss=price * 0.985,
                    take_profits=[price * 1.02, price * 1.04],
                    quality_score=0.92,
                    risk_rating=RiskRating.MEDIUM,
                    notes="Synthetic uptrend example with clear pullback entry.",
                    strategy_name="DemoTrendContinuation",
                )
            )
            print("[SignalEngine] DEMO fallback candidate created")

        snapshot = self._build_snapshot(df, symbol, timeframe)

        primary = select_primary_candidate(all_candidates)

        print(
            f"[SignalEngine] Selected primary quality={getattr(primary, 'quality_score', 0):.2f}"
        )

        return AnalysisResult(
            analysis=snapshot,
            primary_candidate=primary,
            all_candidates=all_candidates,
            regime=regime,
        )
