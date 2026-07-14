"""Monthly feature builder — shared by training (reads CSVs) and inference (reads DB via callers).

Produces one row per (enterprise_id, month) with the feature set from TRD.md §5.1:
lags/rolling stats of net flow, entry regularity, savings runway, EMI coverage,
sector seasonality, festival proximity, commodity level/momentum/volatility,
and climate signals — joined from the enterprise's own district.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from cashflow.simulator.sectors import FESTIVAL_PEAKS, SECTORS

LAGS = [1, 2, 3, 6, 12]
ROLLING_WINDOWS = [3, 6]


def _months_to_nearest_festival(period: pd.Period) -> float:
    month = period.month
    best = 12
    for fm, _fd, _strength in FESTIVAL_PEAKS:
        diff = min(abs(fm - month), 12 - abs(fm - month))
        best = min(best, diff)
    return float(best)


def _load_raw(data_dir: Path) -> dict[str, pd.DataFrame]:
    enterprises = pd.read_csv(data_dir / "enterprises.csv", parse_dates=["onboarded_at"])
    loans = pd.read_csv(data_dir / "loans.csv", parse_dates=["start_date"])
    entries = pd.read_csv(data_dir / "entries.csv", parse_dates=["occurred_at"])
    external = pd.read_csv(data_dir / "external_daily.csv", parse_dates=["date"])
    return {"enterprises": enterprises, "loans": loans, "entries": entries, "external": external}


def _monthly_ledger_aggregates(entries: pd.DataFrame) -> pd.DataFrame:
    e = entries.copy()
    e["month"] = e["occurred_at"].dt.to_period("M")
    sign = e["type"].map({"income": 1, "expense": -1, "loan_repayment": -1, "savings_deposit": 0, "savings_withdrawal": 0})
    e["signed_amount"] = e["amount"] * sign
    e["is_income"] = (e["type"] == "income").astype(float) * e["amount"]
    e["is_expense"] = (e["type"].isin(["expense", "loan_repayment"])).astype(float) * e["amount"]

    grp = e.groupby(["enterprise_id", "month"])
    agg = grp.agg(
        net_flow=("signed_amount", "sum"),
        inflow=("is_income", "sum"),
        outflow=("is_expense", "sum"),
        entry_count=("signed_amount", "count"),
        last_entry_date=("occurred_at", "max"),
    ).reset_index()
    return agg


def _commodity_monthly(external: pd.DataFrame) -> pd.DataFrame:
    commodity_keys = {p.input_commodity for p in SECTORS.values()} | {p.output_commodity for p in SECTORS.values()}
    c = external[external["series_key"].isin(commodity_keys)].copy()
    c["month"] = c["date"].dt.to_period("M")
    monthly = c.groupby(["series_key", "month"])["value"].mean().reset_index()
    monthly = monthly.sort_values(["series_key", "month"])
    monthly["level_z"] = monthly.groupby("series_key")["value"].transform(lambda s: (s - s.mean()) / s.std())
    monthly["momentum_3m"] = monthly.groupby("series_key")["value"].transform(lambda s: s.pct_change(3))
    monthly["volatility"] = monthly.groupby("series_key")["value"].transform(lambda s: s.pct_change().rolling(3).std())
    return monthly


def _climate_monthly(external: pd.DataFrame) -> pd.DataFrame:
    climate = external[external["series_key"].isin(["rainfall_anomaly_mm", "heat_index"])].copy()
    climate["month"] = climate["date"].dt.to_period("M")
    monthly = climate.groupby(["region", "series_key", "month"])["value"].mean().reset_index()
    pivot = monthly.pivot_table(index=["region", "month"], columns="series_key", values="value").reset_index()
    pivot["heat_index_pctile"] = pivot.groupby("region")["heat_index"].rank(pct=True)
    return pivot


def build_feature_table(data_dir: Path) -> pd.DataFrame:
    return build_feature_table_from_frames(_load_raw(data_dir))


def build_feature_table_from_frames(raw: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Same pipeline as build_feature_table, but from already-loaded frames (used by
    inference, which sources them from the DB instead of the simulator's CSVs)."""
    enterprises, loans = raw["enterprises"], raw["loans"]
    ledger = _monthly_ledger_aggregates(raw["entries"])
    commodity = _commodity_monthly(raw["external"])
    climate = _climate_monthly(raw["external"])

    # ---- full enterprise x month grid (fills gaps where an enterprise had zero entries that month) ----
    all_months = pd.period_range(raw["entries"]["occurred_at"].dt.to_period("M").min(),
                                  raw["entries"]["occurred_at"].dt.to_period("M").max(), freq="M")
    grid = pd.MultiIndex.from_product([enterprises["id"], all_months], names=["enterprise_id", "month"]).to_frame(index=False)
    df = grid.merge(ledger, on=["enterprise_id", "month"], how="left")
    df[["net_flow", "inflow", "outflow", "entry_count"]] = df[["net_flow", "inflow", "outflow", "entry_count"]].fillna(0)

    df = df.merge(
        enterprises[["id", "sector", "district", "savings_balance"]].rename(columns={"id": "enterprise_id"}),
        on="enterprise_id", how="left",
    )
    df = df.merge(loans[["enterprise_id", "emi_amount", "emi_due_day"]], on="enterprise_id", how="left")

    df = df.sort_values(["enterprise_id", "month"]).reset_index(drop=True)

    # ---- lags & rolling stats of net flow ----
    grp = df.groupby("enterprise_id")["net_flow"]
    for lag in LAGS:
        df[f"net_flow_lag{lag}"] = grp.shift(lag)
    for win in ROLLING_WINDOWS:
        df[f"net_flow_roll_mean{win}"] = grp.transform(lambda s, w=win: s.shift(1).rolling(w).mean())
        df[f"net_flow_roll_std{win}"] = grp.transform(lambda s, w=win: s.shift(1).rolling(w).std())

    df["inflow_outflow_ratio"] = df["inflow"] / df["outflow"].replace(0, np.nan)
    df["inflow_outflow_ratio"] = df["inflow_outflow_ratio"].fillna(df["inflow_outflow_ratio"].median())

    df["entry_regularity"] = df.groupby("enterprise_id")["entry_count"].transform(lambda s: s.shift(1).rolling(3).mean())
    df["emi_coverage"] = df["net_flow"] / df["emi_amount"].replace(0, np.nan)

    # cumulative "observed" balance (starting savings + cumulative logged net flow) — a noisy proxy,
    # since logged entries have missingness by design (TRD.md §4 realism defects).
    df["cum_net_flow"] = df.groupby("enterprise_id")["net_flow"].cumsum()
    df["observed_balance"] = df["savings_balance"] + df["cum_net_flow"]
    avg_outflow = df.groupby("enterprise_id")["outflow"].transform(lambda s: s.shift(1).rolling(6).mean())
    df["savings_runway_months"] = df["observed_balance"] / avg_outflow.replace(0, np.nan)

    df["month_end"] = df["month"].dt.to_timestamp(how="end")
    df["days_since_last_entry"] = (df["month_end"] - pd.to_datetime(df["last_entry_date"])).dt.days

    df["months_to_festival"] = df["month"].apply(_months_to_nearest_festival)
    df["calendar_month"] = df["month"].dt.month

    # ---- sector-linked commodity features ----
    sector_input = {k: v.input_commodity for k, v in SECTORS.items()}
    sector_output = {k: v.output_commodity for k, v in SECTORS.items()}
    df["input_commodity"] = df["sector"].map(sector_input)
    df["output_commodity"] = df["sector"].map(sector_output)

    com = commodity.set_index(["series_key", "month"])
    for prefix, col in [("input", "input_commodity"), ("output", "output_commodity")]:
        for feat in ["level_z", "momentum_3m", "volatility"]:
            df[f"{prefix}_{feat}"] = df.apply(
                lambda r, feat=feat, col=col: com.loc[(r[col], r["month"]), feat]
                if (r[col], r["month"]) in com.index else np.nan, axis=1)

    # ---- climate (regional, joined on district + month) ----
    climate_idx = climate.set_index(["region", "month"])
    for feat in ["rainfall_anomaly_mm", "heat_index", "heat_index_pctile"]:
        df[feat] = df.apply(
            lambda r, feat=feat: climate_idx.loc[(r["district"], r["month"]), feat]
            if (r["district"], r["month"]) in climate_idx.index else np.nan, axis=1)

    return df


FEATURE_COLUMNS = (
    [f"net_flow_lag{l}" for l in LAGS]
    + [f"net_flow_roll_mean{w}" for w in ROLLING_WINDOWS]
    + [f"net_flow_roll_std{w}" for w in ROLLING_WINDOWS]
    + ["inflow_outflow_ratio", "entry_regularity", "emi_coverage", "savings_runway_months",
       "days_since_last_entry", "months_to_festival", "calendar_month",
       "input_level_z", "input_momentum_3m", "input_volatility",
       "output_level_z", "output_momentum_3m", "output_volatility",
       "rainfall_anomaly_mm", "heat_index", "heat_index_pctile", "sector"]
)
