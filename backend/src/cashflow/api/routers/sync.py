from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from cashflow.ml.infer import run_inference_for_enterprise

from .. import models as m
from ..db import get_db
from ..deps import CurrentUser, require_owner
from ..schemas import EnterpriseProfile, ForecastOut, RiskScoreOut, SyncRequest, SyncResponse

router = APIRouter(tags=["ledger"])


@router.get("/me/enterprise", response_model=EnterpriseProfile)
def get_my_enterprise(user: CurrentUser = Depends(require_owner), db: Session = Depends(get_db)) -> EnterpriseProfile:
    ent = db.query(m.Enterprise).filter(m.Enterprise.id == user.enterprise_id).first()
    if ent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enterprise not found")
    return EnterpriseProfile.model_validate(ent)


@router.post("/sync", response_model=SyncResponse)
def sync(payload: SyncRequest, user: CurrentUser = Depends(require_owner), db: Session = Depends(get_db)) -> SyncResponse:
    enterprise_id = user.enterprise_id
    accepted_ids: list[str] = []

    for entry in payload.entries:
        existing = db.query(m.Entry.id).filter(m.Entry.id == entry.id).first()
        if existing is not None:
            accepted_ids.append(entry.id)  # idempotent replay - already synced
            continue
        db.add(m.Entry(
            id=entry.id, enterprise_id=enterprise_id, type=entry.type, category=entry.category,
            amount=entry.amount, note=entry.note, occurred_at=entry.occurred_at,
            created_at=datetime.utcnow(), synced_at=datetime.utcnow(), device_id=entry.device_id,
        ))
        accepted_ids.append(entry.id)
    db.commit()

    if payload.entries:
        run_inference_for_enterprise(db, enterprise_id)

    forecast_rows = (
        db.query(m.Forecast)
        .filter(m.Forecast.enterprise_id == enterprise_id)
        .order_by(m.Forecast.horizon)
        .all()
    )
    risk_row = (
        db.query(m.RiskScore)
        .filter(m.RiskScore.enterprise_id == enterprise_id)
        .order_by(m.RiskScore.as_of.desc())
        .first()
    )
    alerts = (
        db.query(m.Alert)
        .filter(m.Alert.enterprise_id == enterprise_id, m.Alert.status == "open")
        .order_by(m.Alert.created_at.desc())
        .limit(20)
        .all()
    )

    return SyncResponse(
        accepted_ids=accepted_ids,
        forecast=[ForecastOut.model_validate(f) for f in forecast_rows],
        risk=RiskScoreOut.model_validate(risk_row) if risk_row else None,
        alerts=alerts,
    )
