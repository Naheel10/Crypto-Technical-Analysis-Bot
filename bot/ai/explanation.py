from __future__ import annotations

from typing import Dict

from bot.models import TradeSignal, TradeAction


def generate_explanation(signal: TradeSignal, context: Dict[str, float]) -> str:
    """
    Generate a beginner friendly explanation for a TradeSignal.

    In v1 this can be a hand written template.
    Later you can plug this into an LLM API.
    """
    action = signal.action
    symbol = signal.symbol
    timeframe = signal.timeframe
    regime = signal.regime.value
    strategy = signal.strategy_name

    rsi = context.get("rsi14")
    ema20 = context.get("ema20")
    ema50 = context.get("ema50")

    if action == TradeAction.BUY:
        direction = "a potential BUY setup"
    elif action == TradeAction.SELL:
        direction = "a potential SELL setup"
    else:
        direction = "no clear trade setup right now"

    base = (
        f"{symbol} on the {timeframe} chart is currently classified as {regime.lower()}. "
        f"The {strategy} strategy sees {direction}. "
    )

    extra_parts = []
    if ema20 is not None and ema50 is not None:
        extra_parts.append(
            f"The 20 period EMA is at {ema20:.2f} and the 50 period EMA is at {ema50:.2f}, "
            f"which helps describe the short term trend.",
        )
    if rsi is not None:
        extra_parts.append(
            f"The 14 period RSI is around {rsi:.1f}, "
            f"which tells us if price is overheated or depressed.",
        )

    risk_note = (
        f"The suggested stop loss and take profit levels are only educational examples. "
        f"They do not guarantee profit or protect you from loss."
    )

    explanation = base + " ".join(extra_parts) + " " + risk_note
    return explanation.strip()
