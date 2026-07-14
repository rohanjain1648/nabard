"""Demo-control endpoints (TRD.md §6): trigger a full rescore, or inject a live
shock into one enterprise's recent ledger so the audience watches its risk band
flip during the pitch. Entries injected here are real ledger rows (not a fake
override) - the shock's economic effect (higher input costs / lower sales) is
reflected the same way it would be if the owner logged it themselves, so the
resulting band change is driven by the same model path as any real transaction.
"""
from __future__ import annotations

import uuid
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from cashflow.ml.infer import run_inference_all, run_inference_for_enterprise
from cashflow.simulator.sectors import SECTORS
from cashflow.simulator.shocks import SHOCK_EFFECTS

from .. import models as m
from ..db import get_db
from ..schemas import AlertOut, ForecastOut, RiskScoreOut

router = APIRouter(prefix="/admin", tags=["admin"])

INJECT_WINDOW_DAYS = 12


class InjectShockRequest(BaseModel):
    enterprise_id: str
    shock_type: str


class InjectShockResponse(BaseModel):
    enterprise_id: str
    shock_type: str
    risk: RiskScoreOut | None
    forecast: list[ForecastOut]
    alerts: list[AlertOut]


@router.post("/rescore")
def rescore_all(db: Session = Depends(get_db)) -> dict:
    result = run_inference_all(db)
    return {"n_enterprises": result["n_enterprises"]}


@router.post("/inject-shock", response_model=InjectShockResponse)
def inject_shock(payload: InjectShockRequest, db: Session = Depends(get_db)) -> InjectShockResponse:
    ent = db.query(m.Enterprise).filter(m.Enterprise.id == payload.enterprise_id).first()
    if ent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enterprise not found")
    shock_cfg = SHOCK_EFFECTS.get(payload.shock_type)
    if shock_cfg is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unknown shock_type: {payload.shock_type}")

    profile = SECTORS[ent.sector]
    recent_entries = (
        db.query(m.Entry)
        .filter(m.Entry.enterprise_id == ent.id, m.Entry.type.in_(["income", "expense"]))
        .order_by(m.Entry.occurred_at.desc())
        .limit(60)
        .all()
    )
    avg_income = _avg_amount(recent_entries, "income", default=500.0)
    avg_expense = _avg_amount(recent_entries, "expense", default=300.0)

    income_mult = shock_cfg["income_mult"]
    expense_mult = shock_cfg["expense_mult"]
    today = date.today()
    device_id = f"DEV-{ent.id}-SHOCK-DEMO"

    for offset in range(INJECT_WINDOW_DAYS):
        occurred_at = today - timedelta(days=offset)
        db.add(m.Entry(
            id=str(uuid.uuid4()), enterprise_id=ent.id, type="expense",
            category=profile.expense_categories[0], amount=round(avg_expense * expense_mult, 2),
            note=f"[demo] {payload.shock_type}", occurred_at=occurred_at,
            created_at=occurred_at, synced_at=occurred_at, device_id=device_id,
        ))
        if income_mult < 1.0:
            db.add(m.Entry(
                id=str(uuid.uuid4()), enterprise_id=ent.id, type="income",
                category=profile.income_categories[0], amount=round(avg_income * income_mult, 2),
                note=f"[demo] {payload.shock_type}", occurred_at=occurred_at,
                created_at=occurred_at, synced_at=occurred_at, device_id=device_id,
            ))
    db.commit()

    result = run_inference_for_enterprise(db, ent.id)
    risk = result["risk"]
    forecast_rows = (
        db.query(m.Forecast).filter(m.Forecast.enterprise_id == ent.id).order_by(m.Forecast.horizon).all()
    )
    alerts = (
        db.query(m.Alert)
        .filter(m.Alert.enterprise_id == ent.id, m.Alert.status == "open")
        .order_by(m.Alert.created_at.desc())
        .limit(5)
        .all()
    )

    return InjectShockResponse(
        enterprise_id=ent.id, shock_type=payload.shock_type,
        risk=RiskScoreOut(score=risk["score"], band=risk["band"], drivers=risk["drivers"], as_of=risk["as_of"]),
        forecast=[ForecastOut.model_validate(f) for f in forecast_rows],
        alerts=[AlertOut.model_validate(a) for a in alerts],
    )


def _avg_amount(entries: list[m.Entry], entry_type: str, default: float) -> float:
    values = [e.amount for e in entries if e.type == entry_type]
    return sum(values) / len(values) if values else default
