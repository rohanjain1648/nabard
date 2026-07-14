"""Serve forecasts, risk scores, and alerts for one or all enterprises, from live DB data.

Reuses the exact training feature pipeline (cashflow.ml.features) so train/serve
skew is structurally impossible - the only difference is where the raw frames
come from (CSVs at training time, the DB at serving time).

Implements TRD.md FR-3 (forecast, with cold-start baseline fallback), FR-4 (risk
score + rule-overlay floors + SHAP drivers), and FR-5 (suggestion lookup).
"""
from __future__ import annotations

import json
import pickle
from datetime import date, datetime
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
import shap
from sqlalchemy.orm import Session

from cashflow.simulator.sectors import SECTORS

from .drivers import top_drivers_from_shap
from .features import FEATURE_COLUMNS, build_feature_table_from_frames

BACKEND_ROOT = Path(__file__).resolve().parents[3]
MODELS_DIR = BACKEND_ROOT / "models"
HORIZONS = [1, 2, 3, 4, 5, 6]

COLD_START_MIN_MONTHS = 2
DISENGAGEMENT_DAYS = 30
MISSED_EMI_GRACE_DAYS = 45


class ModelBundle:
    """Loads all trained artifacts once; cheap to re-instantiate for a hackathon prototype."""

    def __init__(self, models_dir: Path = MODELS_DIR):
        self.forecast_spec = json.loads((models_dir / "forecast_feature_spec.json").read_text())
        self.forecaster_p50 = lgb.Booster(model_file=str(models_dir / "forecaster_p50.txt"))
        self.blend_weight = self.forecast_spec["blend_weight_p50"]
        self.residual_offsets = {int(h): v for h, v in self.forecast_spec["residual_offsets_by_horizon"].items()}
        self.forecast_model_version = self.forecast_spec["model_version"]
        self.forecast_sector_categories = self.forecast_spec["sector_categories"]

        self.risk_spec = json.loads((models_dir / "risk_feature_spec.json").read_text())
        self.risk_booster = lgb.Booster(model_file=str(models_dir / "risk.txt"))
        self.risk_threshold = self.risk_spec["decision_threshold"]
        self.risk_model_version = self.risk_spec["model_version"]
        self.risk_sector_categories = self.risk_spec["sector_categories"]
        with open(models_dir / "risk_calibrator.pkl", "rb") as f:
            self.risk_calibrator = pickle.load(f)
        self.risk_explainer = shap.TreeExplainer(self.risk_booster)


_bundle: ModelBundle | None = None


def get_bundle() -> ModelBundle:
    global _bundle
    if _bundle is None:
        _bundle = ModelBundle()
    return _bundle


def _load_frames_from_db(db: Session) -> dict[str, pd.DataFrame]:
    engine = db.get_bind()
    enterprises = pd.read_sql_table("enterprises", engine, parse_dates=["onboarded_at"])
    loans = pd.read_sql_table("loans", engine, parse_dates=["start_date"])
    entries = pd.read_sql_table("entries", engine, parse_dates=["occurred_at"])
    external = pd.read_sql_table("external_signals", engine, parse_dates=["date"])
    return {"enterprises": enterprises, "loans": loans, "entries": entries, "external": external}


def _seasonal_baseline_forecast(enterprise_row: pd.Series, entries: pd.DataFrame, sector: str, horizons: list[int]) -> dict[int, float]:
    """Cold-start fallback (TRD.md FR-3.2): scale the sector's seasonal curve by the
    enterprise's own observed average daily net flow (or a small positive default
    if there's no history at all yet)."""
    ent_entries = entries[entries["enterprise_id"] == enterprise_row["enterprise_id"]]
    if ent_entries.empty:
        avg_daily_net = 200.0  # small positive default for a brand-new enterprise
    else:
        sign = ent_entries["type"].map({"income": 1, "expense": -1, "loan_repayment": -1}).fillna(0)
        span_days = max((ent_entries["occurred_at"].max() - ent_entries["occurred_at"].min()).days, 1)
        avg_daily_net = float((ent_entries["amount"] * sign).sum() / span_days)

    profile = SECTORS[sector]
    current_month = enterprise_row["month"]
    preds = {}
    for h in horizons:
        target_month = current_month + h
        income_mult = profile.income_seasonality[target_month.month]
        expense_mult = profile.expense_seasonality[target_month.month]
        # blend income/expense seasonality into a single net-flow multiplier
        net_mult = (income_mult + expense_mult) / 2
        preds[h] = avg_daily_net * 30 * net_mult
    return preds


def _forecast_for_enterprise(feature_df: pd.DataFrame, entries: pd.DataFrame, enterprise_id: str, bundle: ModelBundle) -> list[dict]:
    ent_df = feature_df[feature_df["enterprise_id"] == enterprise_id].sort_values("month")
    if ent_df.empty:
        return []
    current = ent_df.iloc[-1]
    current_month = current["month"]

    n_active_months = int((ent_df["entry_count"] > 0).sum())
    cold_start = n_active_months < COLD_START_MIN_MONTHS

    rows = []
    cumulative_balance = float(current["observed_balance"])

    if cold_start:
        baseline_preds = _seasonal_baseline_forecast(
            pd.Series({**current.to_dict(), "enterprise_id": enterprise_id}), entries, current["sector"], HORIZONS,
        )
        for h in HORIZONS:
            p50 = baseline_preds[h]
            p10, p90 = p50 * 0.7, p50 * 1.3
            cumulative_balance += p50
            rows.append({
                "enterprise_id": enterprise_id, "target_month": str(current_month + h), "horizon": h,
                "p10": min(p10, p50), "p50": p50, "p90": max(p90, p50),
                "projected_balance": cumulative_balance, "method": "baseline",
                "model_version": bundle.forecast_model_version, "generated_at": datetime.utcnow(),
            })
        return rows

    ent_series = ent_df.set_index("month")["net_flow"]
    for h in HORIZONS:
        lag_month = current_month - (12 - h)
        baseline_pred = float(ent_series.get(lag_month, np.nan))
        row_df = _build_prediction_row(current, FEATURE_COLUMNS + ["horizon"], bundle.forecast_sector_categories, horizon=h)
        model_pred = float(bundle.forecaster_p50.predict(row_df)[0])

        if np.isnan(baseline_pred):
            p50 = model_pred
        else:
            p50 = (1 - bundle.blend_weight) * baseline_pred + bundle.blend_weight * model_pred

        q10_off, q90_off = bundle.residual_offsets[h]["q10_offset"], bundle.residual_offsets[h]["q90_offset"]
        p10, p90 = min(p50 + q10_off, p50), max(p50 + q90_off, p50)
        cumulative_balance += p50

        rows.append({
            "enterprise_id": enterprise_id, "target_month": str(current_month + h), "horizon": h,
            "p10": p10, "p50": p50, "p90": p90,
            "projected_balance": cumulative_balance, "method": "model",
            "model_version": bundle.forecast_model_version, "generated_at": datetime.utcnow(),
        })
    return rows


def _build_prediction_row(
    current: pd.Series, feature_cols: list[str], sector_categories: list[str], horizon: int | None = None,
) -> pd.DataFrame:
    """A pandas Series slice of a mixed-dtype row collapses to dtype=object; rebuild a
    clean, correctly-typed single-row DataFrame for LightGBM instead."""
    values = {col: current[col] for col in feature_cols if col != "horizon"}
    if horizon is not None:
        values["horizon"] = horizon
    row_df = pd.DataFrame([values])
    for col in row_df.columns:
        if col == "sector":
            row_df[col] = pd.Categorical(row_df[col], categories=sector_categories)
        else:
            row_df[col] = row_df[col].astype(float)
    return row_df[feature_cols]


def _band_for_score(score: float) -> str:
    if score >= 70:
        return "green"
    if score >= 40:
        return "amber"
    return "red"


def _risk_for_enterprise(
    feature_df: pd.DataFrame, entries: pd.DataFrame, loans: pd.DataFrame,
    enterprise_id: str, forecast_rows: list[dict], bundle: ModelBundle,
) -> dict:
    ent_df = feature_df[feature_df["enterprise_id"] == enterprise_id].sort_values("month")
    current = ent_df.iloc[-1]
    row_features = _build_prediction_row(current, FEATURE_COLUMNS, bundle.risk_sector_categories)

    raw_prob = float(bundle.risk_booster.predict(row_features)[0])
    calibrated_prob = float(bundle.risk_calibrator.predict([raw_prob])[0])
    score = 100 * (1 - calibrated_prob)

    shap_values = bundle.risk_explainer.shap_values(row_features)
    if isinstance(shap_values, list):  # some SHAP/LightGBM combos return [neg_class, pos_class]
        shap_values = shap_values[-1]
    shap_row = dict(zip(FEATURE_COLUMNS, np.asarray(shap_values)[0]))
    feature_values = current[FEATURE_COLUMNS].to_dict()
    drivers = top_drivers_from_shap(feature_values, shap_row)

    cause_keys = {"applied": []}

    ent_entries = entries[entries["enterprise_id"] == enterprise_id]
    now = ent_entries["occurred_at"].max() if not ent_entries.empty else pd.Timestamp(current["month"].to_timestamp())

    if not ent_entries.empty:
        days_since_any_entry = (now - ent_entries["occurred_at"].max()).days
        if days_since_any_entry > DISENGAGEMENT_DAYS:
            score = min(score, 65)
            cause_keys["applied"].append("disengagement")

    repayments = ent_entries[ent_entries["type"] == "loan_repayment"]
    ent_loans = loans[loans["enterprise_id"] == enterprise_id]
    if not ent_loans.empty:
        if repayments.empty or (now - repayments["occurred_at"].max()).days > MISSED_EMI_GRACE_DAYS:
            score = min(score, 65)
            cause_keys["applied"].append("emi_pressure")

        # Flow-based liquidity check (deliberately NOT balance-based): a large
        # historical cash buffer can mask an acute, ongoing cash-flow problem, so
        # this compares the *rate* of money coming in/out against obligations
        # rather than the cumulative projected balance.
        next_month_forecast = next((f for f in forecast_rows if f["horizon"] == 1), None)
        monthly_outflow = float(ent_df["outflow"].tail(3).mean()) if len(ent_df) else 0.0
        obligation = float(ent_loans["emi_amount"].sum()) + monthly_outflow
        current_net_flow = float(current["net_flow"])
        next_month_net_flow = next_month_forecast["p50"] if next_month_forecast is not None else None
        if current_net_flow < -obligation * 0.5 or (next_month_net_flow is not None and next_month_net_flow < -obligation * 0.5):
            score = min(score, 39)
            cause_keys["applied"].append("liquidity_shortfall")

    band = _band_for_score(score)
    return {
        "enterprise_id": enterprise_id,
        "as_of": now.date() if hasattr(now, "date") else date.today(),
        "score": round(score, 1),
        "band": band,
        "drivers": drivers,
        "rule_overlay_applied": cause_keys["applied"],
        "model_version": bundle.risk_model_version,
    }


def _score_one_enterprise(db: Session, frames: dict[str, pd.DataFrame], feature_df: pd.DataFrame, enterprise_id: str, bundle: ModelBundle) -> dict:
    """The cheap, per-enterprise part of inference (small LightGBM predicts + one
    SHAP explain + a few DB writes) - assumes frames/feature_df are already built."""
    from cashflow.api import models as m
    from .suggestions import pick_suggestion

    forecast_rows = _forecast_for_enterprise(feature_df, frames["entries"], enterprise_id, bundle)
    risk_result = _risk_for_enterprise(feature_df, frames["entries"], frames["loans"], enterprise_id, forecast_rows, bundle)

    db.query(m.Forecast).filter(m.Forecast.enterprise_id == enterprise_id).delete()
    for row in forecast_rows:
        db.add(m.Forecast(**row))

    db.add(m.RiskScore(
        enterprise_id=enterprise_id, as_of=risk_result["as_of"], score=risk_result["score"],
        band=risk_result["band"], drivers=risk_result["drivers"], model_version=risk_result["model_version"],
    ))

    if risk_result["band"] != "green" and risk_result["drivers"]:
        top_driver = risk_result["drivers"][0]
        sector = frames["enterprises"].set_index("id").loc[enterprise_id, "sector"]
        suggestion = pick_suggestion(db, sector, top_driver["driver_key"])
        db.add(m.Alert(
            enterprise_id=enterprise_id, severity=risk_result["band"],
            cause_key=top_driver["driver_key"], cause_text_en=suggestion.text_en if suggestion else top_driver["human_text"],
            cause_text_hi=suggestion.text_hi if suggestion else top_driver["human_text"],
            suggestion_id=suggestion.id if suggestion else None, status="open",
        ))

    return {"forecast": forecast_rows, "risk": risk_result}


def run_inference_for_enterprise(db: Session, enterprise_id: str) -> dict:
    bundle = get_bundle()
    frames = _load_frames_from_db(db)
    feature_df = build_feature_table_from_frames(frames)
    result = _score_one_enterprise(db, frames, feature_df, enterprise_id, bundle)
    db.commit()
    return result


def run_inference_all(db: Session) -> dict:
    from cashflow.api import models as m

    bundle = get_bundle()
    frames = _load_frames_from_db(db)
    feature_df = build_feature_table_from_frames(frames)  # built once, shared across every enterprise

    enterprise_ids = [row[0] for row in db.query(m.Enterprise.id).all()]
    results = {eid: _score_one_enterprise(db, frames, feature_df, eid, bundle) for eid in enterprise_ids}
    db.commit()
    return {"n_enterprises": len(enterprise_ids), "results": results}
