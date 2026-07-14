from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models as m
from ..db import get_db
from ..schemas import LoginRequest, LoginResponse
from ..security import create_access_token, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
    user = db.query(m.User).filter(m.User.phone == payload.phone, m.User.active.is_(True)).first()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid phone or password")

    token = create_access_token(
        user_id=user.id, role=user.role, enterprise_id=user.enterprise_id, officer_id=user.officer_id,
    )
    return LoginResponse(token=token, role=user.role, enterprise_id=user.enterprise_id, officer_id=user.officer_id)
