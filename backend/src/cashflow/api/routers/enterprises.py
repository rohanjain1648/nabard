from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models as m
from ..db import get_db
from ..deps import CurrentUser, get_current_user
from ..schemas import AlertOut, EnterpriseProfile, ForecastOut, RiskScoreOut

router = APIRouter(prefix="/enterprises", tags=["enterprises"])


def _authorize_enterprise_access(enterprise_id: str, user: CurrentUser, db: Session) -> None:
    if user.role == "owner":
        if user.enterprise_id != enterprise_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your enterprise")
        return
    # officer: must be assigned to this enterprise
    assigned = (
        db.query(m.OfficerAssignment)
        .filter(m.OfficerAssignment.officer_id == user.officer_id, m.OfficerAssignment.enterprise_id == enterprise_id)
        .first()
    )
    if assigned is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Enterprise not in your portfolio")


@router.get("/{enterprise_id}/profile", response_model=EnterpriseProfile)
def get_profile(enterprise_id: str, user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)) -> EnterpriseProfile:
    _authorize_enterprise_access(enterprise_id, user, db)
    ent = db.query(m.Enterprise).filter(m.Enterprise.id == enterprise_id).first()
    if ent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enterprise not found")
    return EnterpriseProfile.model_validate(ent)


@router.get("/{enterprise_id}/forecast", response_model=list[ForecastOut])
def get_forecast(enterprise_id: str, user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)) -> list[ForecastOut]:
    _authorize_enterprise_access(enterprise_id, user, db)
    rows = (
        db.query(m.Forecast)
        .filter(m.Forecast.enterprise_id == enterprise_id)
        .order_by(m.Forecast.horizon)
        .all()
    )
    return [ForecastOut.model_validate(r) for r in rows]


@router.get("/{enterprise_id}/risk", response_model=RiskScoreOut | None)
def get_risk(enterprise_id: str, user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)) -> RiskScoreOut | None:
    _authorize_enterprise_access(enterprise_id, user, db)
    row = (
        db.query(m.RiskScore)
        .filter(m.RiskScore.enterprise_id == enterprise_id)
        .order_by(m.RiskScore.as_of.desc())
        .first()
    )
    return RiskScoreOut.model_validate(row) if row else None


@router.get("/{enterprise_id}/risk/history", response_model=list[RiskScoreOut])
def get_risk_history(enterprise_id: str, user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)) -> list[RiskScoreOut]:
    _authorize_enterprise_access(enterprise_id, user, db)
    rows = (
        db.query(m.RiskScore)
        .filter(m.RiskScore.enterprise_id == enterprise_id)
        .order_by(m.RiskScore.as_of)
        .all()
    )
    return [RiskScoreOut.model_validate(r) for r in rows]


@router.get("/{enterprise_id}/alerts", response_model=list[AlertOut])
def get_alerts(enterprise_id: str, user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)) -> list[AlertOut]:
    _authorize_enterprise_access(enterprise_id, user, db)
    rows = (
        db.query(m.Alert)
        .filter(m.Alert.enterprise_id == enterprise_id)
        .order_by(m.Alert.created_at.desc())
        .limit(50)
        .all()
    )
    return [AlertOut.model_validate(r) for r in rows]


@router.post("/alerts/{alert_id}/ack", response_model=AlertOut)
def acknowledge_alert(alert_id: int, user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)) -> AlertOut:
    alert = db.query(m.Alert).filter(m.Alert.id == alert_id).first()
    if alert is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    _authorize_enterprise_access(alert.enterprise_id, user, db)
    alert.status = "acknowledged"
    db.commit()
    db.refresh(alert)
    return AlertOut.model_validate(alert)
