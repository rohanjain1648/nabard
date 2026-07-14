from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel


class LoginRequest(BaseModel):
    phone: str
    password: str


class LoginResponse(BaseModel):
    token: str
    role: Literal["owner", "officer"]
    enterprise_id: str | None = None
    officer_id: str | None = None


class LoanOut(BaseModel):
    id: str
    principal: float
    outstanding: float
    emi_amount: float
    emi_due_day: int
    start_date: date
    term_months: int

    class Config:
        from_attributes = True


class EnterpriseProfile(BaseModel):
    id: str
    name: str
    sector: str
    village: str
    district: str
    state: str
    onboarded_at: date
    savings_balance: float
    loans: list[LoanOut] = []

    class Config:
        from_attributes = True


class EntryIn(BaseModel):
    id: str  # client-generated UUID
    type: Literal["income", "expense", "savings_deposit", "savings_withdrawal", "loan_repayment"]
    category: str
    amount: float
    note: str | None = None
    occurred_at: date
    device_id: str


class EntryOut(BaseModel):
    id: str
    enterprise_id: str
    type: str
    category: str
    amount: float
    note: str | None
    occurred_at: date
    created_at: datetime

    class Config:
        from_attributes = True


class SyncRequest(BaseModel):
    entries: list[EntryIn] = []


class ForecastOut(BaseModel):
    target_month: str
    horizon: int
    p10: float
    p50: float
    p90: float
    projected_balance: float
    method: str

    class Config:
        from_attributes = True


class DriverOut(BaseModel):
    driver_key: str
    weight: float
    human_text: str


class RiskScoreOut(BaseModel):
    score: float
    band: Literal["green", "amber", "red"]
    drivers: list[dict]
    as_of: date

    class Config:
        from_attributes = True


class AlertOut(BaseModel):
    id: int
    enterprise_id: str
    severity: str
    cause_key: str
    cause_text_en: str
    cause_text_hi: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class SyncResponse(BaseModel):
    accepted_ids: list[str]
    forecast: list[ForecastOut]
    risk: RiskScoreOut | None
    alerts: list[AlertOut]


class PortfolioItem(BaseModel):
    enterprise_id: str
    name: str
    sector: str
    village: str
    district: str
    band: str
    score: float
    last_entry_at: date | None


class PortfolioSummary(BaseModel):
    green: int
    amber: int
    red: int
    total: int
    sector_heatmap: dict[str, dict[str, int]]
