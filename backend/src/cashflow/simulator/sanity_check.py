"""Quick visual sanity check: plot monthly net cash flow for a few enterprises per sector,
with shock windows shaded, to confirm the simulator "looks like real rural businesses"
before trusting it for ML (TRD.md §4 checkpoint).

Usage: python -m cashflow.simulator.sanity_check --data backend/data --out backend/reports
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--out", type=Path, default=Path("reports"))
    args = parser.parse_args()

    entries = pd.read_csv(args.data / "entries.csv", parse_dates=["occurred_at"])
    enterprises = pd.read_csv(args.data / "enterprises.csv")
    shocks = pd.read_csv(args.data / "shocks.csv", parse_dates=["start_date", "end_date"])

    entries["month"] = entries["occurred_at"].dt.to_period("M").dt.to_timestamp()
    sign = entries["type"].map({"income": 1, "expense": -1, "loan_repayment": -1})
    entries["signed_amount"] = entries["amount"] * sign
    monthly = entries.groupby(["enterprise_id", "month"])["signed_amount"].sum().reset_index()

    sectors = enterprises["sector"].unique()
    fig, axes = plt.subplots(len(sectors), 1, figsize=(11, 3 * len(sectors)), sharex=True)
    args.out.mkdir(parents=True, exist_ok=True)

    for ax, sector in zip(axes, sectors):
        sample_ids = enterprises[enterprises["sector"] == sector]["id"].iloc[:3]
        for eid in sample_ids:
            series = monthly[monthly["enterprise_id"] == eid]
            ax.plot(series["month"], series["signed_amount"], marker="o", markersize=2, label=eid)
            for _, s in shocks[shocks["enterprise_id"] == eid].iterrows():
                ax.axvspan(s["start_date"], s["end_date"], alpha=0.15, color="red")
        ax.set_title(f"Sector: {sector}")
        ax.axhline(0, color="grey", linewidth=0.5)
        ax.legend(fontsize=7, loc="upper left")

    fig.tight_layout()
    out_path = args.out / "simulator_sanity_check.png"
    fig.savefig(out_path, dpi=130)
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
