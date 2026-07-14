from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


class Enterprise(Base):
    __tablename__ = "enterprises"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    sector: Mapped[str] = mapped_column(String, index=True)
    village: Mapped[str] = mapped_column(String)
    district: Mapped[str] = mapped_column(String)
    state: Mapped[str] = mapped_column(String)
    onboarded_at: Mapped[date] = mapped_column(Date)
    savings_balance: Mapped[float] = mapped_column(Float, default=0)

    loans: Mapped[list["Loan"]] = relationship(back_populates="enterprise")


class Loan(Base):
    __tablename__ = "loans"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    enterprise_id: Mapped[str] = mapped_column(ForeignKey("enterprises.id"), index=True)
    principal: Mapped[float] = mapped_column(Float)
    outstanding: Mapped[float] = mapped_column(Float)
    emi_amount: Mapped[float] = mapped_column(Float)
    emi_due_day: Mapped[int] = mapped_column(Integer)
    start_date: Mapped[date] = mapped_column(Date)
    term_months: Mapped[int] = mapped_column(Integer)

    enterprise: Mapped[Enterprise] = relationship(back_populates="loans")


class Entry(Base):
    """Append-only ledger entry. Never updated in place — corrections use reversal entries."""
    __tablename__ = "entries"

    id: Mapped[str] = mapped_column(String, primary_key=True)  # client-generated UUID
    enterprise_id: Mapped[str] = mapped_column(ForeignKey("enterprises.id"), index=True)
    type: Mapped[str] = mapped_column(String)  # income|expense|savings_deposit|savings_withdrawal|loan_repayment
    category: Mapped[str] = mapped_column(String)
    amount: Mapped[float] = mapped_column(Float)
    note: Mapped[str | None] = mapped_column(String, nullable=True)
    occurred_at: Mapped[date] = mapped_column(Date, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    synced_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    device_id: Mapped[str] = mapped_column(String)


class ExternalSignal(Base):
    __tablename__ = "external_signals"
    __table_args__ = (UniqueConstraint("date", "series_key", "region", name="uq_signal"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date: Mapped[date] = mapped_column(Date, index=True)
    series_key: Mapped[str] = mapped_column(String, index=True)
    region: Mapped[str] = mapped_column(String, index=True)
    value: Mapped[float] = mapped_column(Float)


class Forecast(Base):
    __tablename__ = "forecasts"
    __table_args__ = (UniqueConstraint("enterprise_id", "target_month", "model_version", name="uq_forecast"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    enterprise_id: Mapped[str] = mapped_column(ForeignKey("enterprises.id"), index=True)
    target_month: Mapped[str] = mapped_column(String)  # "2026-08"
    horizon: Mapped[int] = mapped_column(Integer)  # 1..6
    p10: Mapped[float] = mapped_column(Float)
    p50: Mapped[float] = mapped_column(Float)
    p90: Mapped[float] = mapped_column(Float)
    projected_balance: Mapped[float] = mapped_column(Float)
    method: Mapped[str] = mapped_column(String)  # "model" | "baseline"
    model_version: Mapped[str] = mapped_column(String)
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class RiskScore(Base):
    __tablename__ = "risk_scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    enterprise_id: Mapped[str] = mapped_column(ForeignKey("enterprises.id"), index=True)
    as_of: Mapped[date] = mapped_column(Date, index=True)
    score: Mapped[float] = mapped_column(Float)
    band: Mapped[str] = mapped_column(String)  # green|amber|red
    drivers: Mapped[list] = mapped_column(JSON, default=list)
    model_version: Mapped[str] = mapped_column(String)


class Suggestion(Base):
    __tablename__ = "suggestions"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    sector: Mapped[str] = mapped_column(String, index=True)
    driver_key: Mapped[str] = mapped_column(String, index=True)
    text_en: Mapped[str] = mapped_column(String)
    text_hi: Mapped[str] = mapped_column(String)
    action_type: Mapped[str] = mapped_column(String)


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    enterprise_id: Mapped[str] = mapped_column(ForeignKey("enterprises.id"), index=True)
    severity: Mapped[str] = mapped_column(String)  # green|amber|red
    cause_key: Mapped[str] = mapped_column(String)
    cause_text_en: Mapped[str] = mapped_column(String)
    cause_text_hi: Mapped[str] = mapped_column(String)
    suggestion_id: Mapped[str | None] = mapped_column(ForeignKey("suggestions.id"), nullable=True)
    status: Mapped[str] = mapped_column(String, default="open")  # open|acknowledged|resolved
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


class Officer(Base):
    __tablename__ = "officers"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String)


class OfficerAssignment(Base):
    __tablename__ = "officer_assignments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    officer_id: Mapped[str] = mapped_column(ForeignKey("officers.id"), index=True)
    enterprise_id: Mapped[str] = mapped_column(ForeignKey("enterprises.id"), index=True)


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    role: Mapped[str] = mapped_column(String)  # owner|officer
    enterprise_id: Mapped[str | None] = mapped_column(ForeignKey("enterprises.id"), nullable=True)
    officer_id: Mapped[str | None] = mapped_column(ForeignKey("officers.id"), nullable=True)
    phone: Mapped[str] = mapped_column(String, unique=True)
    password_hash: Mapped[str] = mapped_column(String)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
