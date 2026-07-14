"""Deterministic dataset generator — the "moat" of the demo (TRD.md §4).

Produces enterprises, loans, a daily transaction ledger (with realistic logging
defects), external signals (commodity/weather/UPI-proxy), injected shock events,
and ground-truth monthly stress labels for ML training.

Usage:
    python -m cashflow.simulator.generate --out backend/data --seed 42
"""
from __future__ import annotations

import argparse
import json
import uuid
from datetime import date, datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

from .external_signals import (
    generate_commodity_prices,
    generate_upi_activity_index,
    generate_weather,
)
from .sectors import FESTIVAL_PEAKS, SECTORS

N_PER_SECTOR = 10
N_MONTHS = 24
DISTRICTS = [
    {"district": "Sehore", "state": "Madhya Pradesh", "villages": ["Ichhawar", "Budni", "Nasrullaganj"]},
    {"district": "Solapur", "state": "Maharashtra", "villages": ["Akkalkot", "Barshi", "Mangalvedha"]},
    {"district": "Kurnool", "state": "Andhra Pradesh", "villages": ["Adoni", "Nandyal", "Yemmiganur"]},
]

FIRST_NAMES = ["Sunita", "Ramesh", "Lakshmi", "Suresh", "Kavita", "Manoj", "Geeta", "Anil",
               "Radha", "Vijay", "Meena", "Rakesh", "Shobha", "Deepak", "Anita", "Prakash"]
ENTERPRISE_NOUNS = {
    "dairy": "Dairy", "poultry": "Poultry Farm", "food_processing": "Food Processing Unit",
    "handicrafts": "Handicrafts", "rural_retail": "General Store",
}


def _festival_multiplier(dates: pd.DatetimeIndex, sensitivity: float) -> np.ndarray:
    mult = np.ones(len(dates))
    for month, day, strength in FESTIVAL_PEAKS:
        for i, d in enumerate(dates):
            delta = abs((d - pd.Timestamp(year=d.year, month=month, day=min(day, 28))).days)
            delta = min(delta, 365 - delta)
            if delta <= 10:
                mult[i] += strength * sensitivity * max(0, 1 - delta / 10)
    return mult


def _round_amount(x: float) -> float:
    x = max(x, 0.0)
    if x < 100:
        return round(x)
    if x < 1000:
        return round(x / 5) * 5
    return round(x / 10) * 10


def generate_dataset(seed: int, out_dir: Path) -> None:
    rng = np.random.default_rng(seed)
    start_date = date.today().replace(day=1) - pd.DateOffset(months=N_MONTHS)
    start_date = start_date.date() if hasattr(start_date, "date") else start_date
    dates = pd.date_range(start=start_date, periods=N_MONTHS * 30, freq="D")
    n_days = len(dates)

    # ---- external signals (shared across all enterprises / regions) ----
    commodities = generate_commodity_prices(rng, dates)
    weather_frames, upi_frames = [], []
    for d in DISTRICTS:
        rf, hi = generate_weather(rng, dates, region=d["district"])
        weather_frames += [rf, hi]
        upi_frames.append(generate_upi_activity_index(rng, dates, region=d["district"]))
    external = pd.concat([commodities] + weather_frames + upi_frames, ignore_index=True)
    commodity_pivot = commodities.pivot(index="date", columns="series_key", values="value")

    enterprises_rows = []
    loans_rows = []
    entries_rows = []
    shocks_rows = []
    monthly_labels_rows = []

    from .shocks import daily_multipliers, sample_shocks

    ent_counter = 0
    for sector_key, profile in SECTORS.items():
        for _ in range(N_PER_SECTOR):
            ent_counter += 1
            eid = f"ENT{ent_counter:04d}"
            district = DISTRICTS[rng.integers(0, len(DISTRICTS))]
            village = district["villages"][rng.integers(0, len(district["villages"]))]
            name = f"{rng.choice(FIRST_NAMES)} {ENTERPRISE_NOUNS[sector_key]}"
            base_level = float(rng.lognormal(mean=6.6, sigma=0.4))  # ~ INR 500-1200/day scale

            onboarded_at = dates[0] + pd.Timedelta(days=int(rng.integers(0, 60)))
            savings_balance_start = float(rng.uniform(2000, 15000))

            # ---- loan ----
            principal = float(rng.choice([15000, 25000, 40000, 60000, 80000]))
            term_months = int(rng.choice([12, 18, 24, 36]))
            emi_amount = round(principal / term_months * 1.09, 2)
            emi_due_day = int(rng.integers(1, 28))
            loan_start = dates[0] + pd.Timedelta(days=int(rng.integers(0, 90)))
            loans_rows.append({
                "id": f"LOAN{ent_counter:04d}", "enterprise_id": eid, "principal": principal,
                "outstanding": principal, "emi_amount": emi_amount, "emi_due_day": emi_due_day,
                "start_date": loan_start.date().isoformat(), "term_months": term_months,
            })

            # ---- shocks ----
            events = sample_shocks(rng, eid, sector_key, n_days)
            income_shock_mult, expense_shock_mult = daily_multipliers(events, n_days)
            for ev in events:
                shocks_rows.append({
                    "enterprise_id": eid, "shock_type": ev.shock_type,
                    "start_date": dates[ev.start_day].date().isoformat(),
                    "end_date": dates[min(ev.start_day + ev.duration_days, n_days - 1)].date().isoformat(),
                    "duration_days": ev.duration_days,
                })

            # ---- seasonality & external linkage, vectorized over all days ----
            months = dates.month.values
            income_season = np.array([profile.income_seasonality[m] for m in months])
            expense_season = np.array([profile.expense_seasonality[m] for m in months])
            festival_mult = _festival_multiplier(dates, profile.festival_sensitivity)

            out_price = commodity_pivot[profile.output_commodity].values
            in_price = commodity_pivot[profile.input_commodity].values
            out_price_z = (out_price - out_price.mean()) / out_price.std()
            in_price_z = (in_price - in_price.mean()) / in_price.std()

            rf_series = next(f for f in weather_frames
                              if f["series_key"].iloc[0] == "rainfall_anomaly_mm" and f["region"].iloc[0] == district["district"])
            hi_series = next(f for f in weather_frames
                              if f["series_key"].iloc[0] == "heat_index" and f["region"].iloc[0] == district["district"])
            rain_effect = 1 - profile.rain_sensitivity * np.clip(-rf_series["value"].values / 10, -1, 1)
            heat_effect = 1 - profile.heat_sensitivity * np.clip(hi_series["value"].values - 0.6, 0, 0.4) / 0.4

            income_mult_total = (income_season * festival_mult * (1 + 0.06 * out_price_z)
                                  * rain_effect * heat_effect * income_shock_mult)
            expense_mult_total = (expense_season * (1 + 0.08 * in_price_z) * expense_shock_mult)

            noise_income = rng.lognormal(mean=0, sigma=0.18, size=n_days)
            noise_expense = rng.lognormal(mean=0, sigma=0.15, size=n_days)

            if profile.batch_cycle_days > 0:
                cycle_phase = (np.arange(n_days) % profile.batch_cycle_days)
                batch_pulse = (cycle_phase > profile.batch_cycle_days - 5).astype(float) * 3.0 + 0.3
                daily_income = base_level * income_mult_total * noise_income * batch_pulse
            else:
                daily_income = base_level * income_mult_total * noise_income

            daily_expense = base_level * 0.55 * expense_mult_total * noise_expense

            # ---- logging defects: missing days + weekend clumping ----
            log_mask = rng.random(n_days) > rng.uniform(0.05, 0.15)  # 5-15% missing

            # ---- true (undefected) daily balance for ground-truth labeling ----
            true_balance = np.empty(n_days)
            bal = savings_balance_start
            emi_days = pd.Index(dates).day == emi_due_day
            for t in range(n_days):
                bal += daily_income[t] - daily_expense[t]
                if emi_days[t] and dates[t] >= loan_start:
                    bal -= emi_amount
                true_balance[t] = bal

            # ---- emit ledger entries (as logged, with defects) ----
            device_id = f"DEV-{eid}"
            for t in range(n_days):
                occurred_at = dates[t]
                if occurred_at < onboarded_at:
                    continue
                if not log_mask[t]:
                    continue
                if daily_income[t] > 5:
                    cat = rng.choice(profile.income_categories)
                    entries_rows.append({
                        "id": str(uuid.uuid4()), "enterprise_id": eid, "type": "income",
                        "category": cat, "amount": _round_amount(daily_income[t]),
                        "note": None, "occurred_at": occurred_at.date().isoformat(),
                        "created_at": occurred_at.date().isoformat(), "device_id": device_id,
                    })
                if daily_expense[t] > 5:
                    cat = rng.choice(profile.expense_categories[:-1])  # exclude loan_emi from random draws
                    entries_rows.append({
                        "id": str(uuid.uuid4()), "enterprise_id": eid, "type": "expense",
                        "category": cat, "amount": _round_amount(daily_expense[t]),
                        "note": None, "occurred_at": occurred_at.date().isoformat(),
                        "created_at": occurred_at.date().isoformat(), "device_id": device_id,
                    })
                if emi_days[t] and dates[t] >= loan_start:
                    entries_rows.append({
                        "id": str(uuid.uuid4()), "enterprise_id": eid, "type": "loan_repayment",
                        "category": "loan_emi", "amount": emi_amount,
                        "note": None, "occurred_at": occurred_at.date().isoformat(),
                        "created_at": occurred_at.date().isoformat(), "device_id": device_id,
                    })

            # ---- monthly ground-truth stress label ----
            month_periods = pd.Index(dates).to_period("M")
            df_bal = pd.DataFrame({"period": month_periods, "true_balance": true_balance})
            monthly_min_balance = df_bal.groupby("period")["true_balance"].min()
            for period, min_bal in monthly_min_balance.items():
                obligation = emi_amount + base_level * 0.55 * 30  # EMI + a typical month of fixed-ish costs
                stressed = int(min_bal < obligation * 0.5)
                monthly_labels_rows.append({
                    "enterprise_id": eid, "month": str(period), "min_balance": round(min_bal, 2),
                    "obligation_estimate": round(obligation, 2), "stressed": stressed,
                })

            enterprises_rows.append({
                "id": eid, "name": name, "sector": sector_key, "village": village,
                "district": district["district"], "state": district["state"],
                "onboarded_at": onboarded_at.date().isoformat(),
                "savings_balance": round(savings_balance_start, 2),
            })

    out_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(enterprises_rows).to_csv(out_dir / "enterprises.csv", index=False)
    pd.DataFrame(loans_rows).to_csv(out_dir / "loans.csv", index=False)
    pd.DataFrame(entries_rows).to_csv(out_dir / "entries.csv", index=False)
    external.to_csv(out_dir / "external_daily.csv", index=False)
    pd.DataFrame(shocks_rows).to_csv(out_dir / "shocks.csv", index=False)
    pd.DataFrame(monthly_labels_rows).to_csv(out_dir / "monthly_labels.csv", index=False)

    stress_rate = pd.DataFrame(monthly_labels_rows)["stressed"].mean()
    summary = {
        "seed": seed,
        "n_enterprises": len(enterprises_rows),
        "n_entries": len(entries_rows),
        "n_shocks": len(shocks_rows),
        "n_enterprise_months": len(monthly_labels_rows),
        "stress_rate": round(float(stress_rate), 4),
        "date_range": [dates[0].date().isoformat(), dates[-1].date().isoformat()],
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path("backend/data"))
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    generate_dataset(args.seed, args.out)


if __name__ == "__main__":
    main()
