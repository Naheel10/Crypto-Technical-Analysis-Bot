from __future__ import annotations

from typing import List, Optional

from fastapi import HTTPException
from pydantic import BaseModel


class PositionSizingRequest(BaseModel):
    account_size: float
    risk_pct: float
    entry_price: float
    stop_loss: float
    take_profits: Optional[List[float]] = None


class PositionSizingResponse(BaseModel):
    account_size: float
    risk_pct: float
    risk_amount: float
    position_size: float
    r_to_tp: List[float]


def calculate_position_sizing(payload: PositionSizingRequest) -> PositionSizingResponse:
    risk_amount = payload.account_size * payload.risk_pct
    per_unit_risk = abs(payload.entry_price - payload.stop_loss)

    if per_unit_risk <= 0:
        raise HTTPException(status_code=400, detail="Invalid stop loss or entry price")

    position_size = risk_amount / per_unit_risk if per_unit_risk > 0 else 0.0

    r_to_tp: List[float] = []
    if payload.take_profits:
        for tp in payload.take_profits:
            if payload.entry_price >= payload.stop_loss:
                reward = tp - payload.entry_price
            else:
                reward = payload.entry_price - tp
            r_multiple = reward / per_unit_risk
            r_to_tp.append(r_multiple)

    return PositionSizingResponse(
        account_size=payload.account_size,
        risk_pct=payload.risk_pct,
        risk_amount=risk_amount,
        position_size=position_size,
        r_to_tp=r_to_tp,
    )
