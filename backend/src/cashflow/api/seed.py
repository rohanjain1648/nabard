"""Load simulator CSV output + suggestion library into the DB, and create demo users.

Usage: python -m cashflow.api.seed --data backend/data
"""
from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

import pandas as pd
import yaml

from .db import Base, SessionLocal, engine
from .security import hash_password
from . import models as m

CONFIG_DIR = Path(__file__).resolve().parent / "config_data"
N_OFFICERS = 3

# Demo credentials (prototype only — not for production use).
DEMO_OWNER_PHONE = "9990000001"
DEMO_OWNER_PASSWORD = "owner123"
DEMO_OFFICER_PHONE = "9990000002"
DEMO_OFFICER_PASSWORD = "officer123"


def _reset_schema() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def load_data(data_dir: Path) -> None:
    _reset_schema()
    db = SessionLocal()
    try:
        date_cols = {
            "enterprises.csv": ["onboarded_at"],
            "loans.csv": ["start_date"],
            "entries.csv": ["occurred_at"],
            "external_daily.csv": ["date"],
        }
        enterprises = pd.read_csv(data_dir / "enterprises.csv", parse_dates=date_cols["enterprises.csv"])
        loans = pd.read_csv(data_dir / "loans.csv", parse_dates=date_cols["loans.csv"])
        entries = pd.read_csv(data_dir / "entries.csv", parse_dates=date_cols["entries.csv"])
        external = pd.read_csv(data_dir / "external_daily.csv", parse_dates=date_cols["external_daily.csv"])

        for df, cols in [(enterprises, date_cols["enterprises.csv"]),
                          (loans, date_cols["loans.csv"]),
                          (entries, date_cols["entries.csv"]),
                          (external, date_cols["external_daily.csv"])]:
            for col in cols:
                df[col] = df[col].dt.date

        db.bulk_insert_mappings(m.Enterprise, enterprises.to_dict(orient="records"))
        db.bulk_insert_mappings(m.Loan, loans.to_dict(orient="records"))

        entries = entries.copy()
        entries["created_at"] = pd.Timestamp.now(tz="UTC").to_pydatetime()
        entries["synced_at"] = datetime.utcnow()
        db.bulk_insert_mappings(m.Entry, entries.to_dict(orient="records"))

        db.bulk_insert_mappings(m.ExternalSignal, external[["date", "series_key", "region", "value"]].to_dict(orient="records"))

        with open(CONFIG_DIR / "suggestions.yaml", encoding="utf-8") as f:
            suggestions = yaml.safe_load(f)
        db.bulk_insert_mappings(m.Suggestion, suggestions)

        # ---- officers: round-robin assignment across all enterprises ----
        officer_ids = [f"OFF{i+1:03d}" for i in range(N_OFFICERS)]
        officer_names = ["Rajesh Kumar", "Priya Sharma", "Ahmed Khan"]
        db.bulk_insert_mappings(m.Officer, [
            {"id": oid, "name": name} for oid, name in zip(officer_ids, officer_names)
        ])
        ent_ids = enterprises["id"].tolist()
        assignments = [
            {"officer_id": officer_ids[i % N_OFFICERS], "enterprise_id": eid}
            for i, eid in enumerate(ent_ids)
        ]
        db.bulk_insert_mappings(m.OfficerAssignment, assignments)

        # ---- demo users ----
        db.bulk_insert_mappings(m.User, [
            {
                "id": "USER_OWNER_DEMO", "role": "owner", "enterprise_id": ent_ids[0],
                "officer_id": None, "phone": DEMO_OWNER_PHONE,
                "password_hash": hash_password(DEMO_OWNER_PASSWORD), "active": True,
            },
            {
                "id": "USER_OFFICER_DEMO", "role": "officer", "enterprise_id": None,
                "officer_id": officer_ids[0], "phone": DEMO_OFFICER_PHONE,
                "password_hash": hash_password(DEMO_OFFICER_PASSWORD), "active": True,
            },
        ])

        db.commit()
        print(f"Seeded {len(enterprises)} enterprises, {len(entries)} entries, "
              f"{len(suggestions)} suggestions, {N_OFFICERS} officers.")
        print(f"Demo owner login: {DEMO_OWNER_PHONE} / {DEMO_OWNER_PASSWORD} (enterprise {ent_ids[0]})")
        print(f"Demo officer login: {DEMO_OFFICER_PHONE} / {DEMO_OFFICER_PASSWORD} (officer {officer_ids[0]})")
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=Path("data"))
    args = parser.parse_args()
    load_data(args.data)


if __name__ == "__main__":
    main()
