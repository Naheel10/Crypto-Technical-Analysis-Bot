from __future__ import annotations

from typing import Optional

from bot.models import AnalysisSnapshot, CandidateTrade, TrendBias, TradeDirection


def _bias_to_text(bias: TrendBias) -> str:
    mapping = {
        TrendBias.STRONGLY_BULLISH: "a strong bullish trend",
        TrendBias.BULLISH: "a bullish drift",
        TrendBias.NEUTRAL: "mixed direction",
        TrendBias.BEARISH: "a bearish tilt",
        TrendBias.STRONGLY_BEARISH: "a strong bearish trend",
    }
    return mapping.get(bias, "unclear price direction")


def generate_explanation(
    analysis: AnalysisSnapshot,
    primary: Optional[CandidateTrade],
) -> str:
    """Generate a beginner friendly explanation for a chart read."""

    summary = (
        f"{analysis.symbol} on the {analysis.timeframe} chart shows {_bias_to_text(analysis.trend_bias)} "
        f"with market structure leaning {analysis.structure.value.lower()} and volatility {analysis.volatility_regime.value.lower()}."
    )

    indicators = []
    if analysis.ema20 and analysis.ema50:
        indicators.append(
            f"Price is {analysis.latest_price:.2f} with EMA20 at {analysis.ema20:.2f} and EMA50 at {analysis.ema50:.2f}."
        )
    if analysis.rsi14 is not None:
        indicators.append(f"RSI(14) sits near {analysis.rsi14:.1f}, hinting at momentum {analysis.momentum_state.value.lower()}.")

    idea_text = "No clean trade idea right now; consider waiting for price to interact with key levels."
    if primary:
        direction = "long" if primary.direction == TradeDirection.LONG else "short"
        entry = (
            f"an entry zone around {primary.entry_zone[0]:.2f}-{primary.entry_zone[1]:.2f}"
            if primary.entry_zone
            else "a flexible entry"
        )
        sl = f"stop near {primary.stop_loss:.2f}" if primary.stop_loss else "no fixed stop"
        tps = (
            ", ".join([f"TP{idx+1}: {tp:.2f}" for idx, tp in enumerate(primary.take_profits or [])])
            or "open upside"
        )
        idea_text = (
            f"Primary idea: a {direction} {primary.setup_type} setup with {entry}, {sl}, and targets {tps}. "
            f"Notes: {primary.notes} (quality {primary.quality_score:.2f})."
        )

    risk_note = (
        "This is educational only. Levels are illustrative examples and do not guarantee outcomes."
    )

    parts = [summary, " ".join(indicators), idea_text, risk_note]
    return " ".join(p.strip() for p in parts if p).strip()
