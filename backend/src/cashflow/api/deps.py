from __future__ import annotations

from dataclasses import dataclass

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from .db import get_db
from .security import decode_access_token

bearer_scheme = HTTPBearer()


@dataclass
class CurrentUser:
    user_id: str
    role: str
    enterprise_id: str | None
    officer_id: str | None


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> CurrentUser:
    try:
        payload = decode_access_token(credentials.credentials)
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    return CurrentUser(
        user_id=payload["sub"], role=payload["role"],
        enterprise_id=payload.get("enterprise_id"), officer_id=payload.get("officer_id"),
    )


def require_owner(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    if user.role != "owner":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Owner role required")
    return user


def require_officer(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    if user.role != "officer":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Officer role required")
    return user


DbSession = Depends(get_db)
