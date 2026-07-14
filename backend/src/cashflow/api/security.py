from __future__ import annotations

from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

JWT_SECRET = "hackathon-demo-secret-change-in-production"  # prototype only, see ARCHITECTURE.md §5
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 24 * 7


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8")[:72], bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8")[:72], password_hash.encode("utf-8"))


def create_access_token(*, user_id: str, role: str, enterprise_id: str | None, officer_id: str | None) -> str:
    payload = {
        "sub": user_id,
        "role": role,
        "enterprise_id": enterprise_id,
        "officer_id": officer_id,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRY_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
