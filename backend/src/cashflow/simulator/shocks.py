"""Shock event injection: per-enterprise stress episodes that double as ground-truth labels.

Each shock depresses income and/or inflates costs for a window of days. The
resulting simulated balance trajectory is what produces the "stressed" label
the risk classifier trains against (see TRD.md §4, §5.2).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

SHOCK_TYPES = [
    "feed_price_spike",
    "drought",
    "demand_collapse",
    "disease_outbreak",
    "emi_burden",
]

# income_mult / expense_mult applied for the duration of the shock window
SHOCK_EFFECTS = {
    "feed_price_spike": {"income_mult": 1.0, "expense_mult": 1.45, "sectors": ["dairy", "poultry"]},
    "drought": {"income_mult": 0.6, "expense_mult": 1.15, "sectors": ["dairy", "rural_retail", "food_processing"]},
    "demand_collapse": {"income_mult": 0.45, "expense_mult": 1.0, "sectors": ["handicrafts", "rural_retail", "food_processing"]},
    "disease_outbreak": {"income_mult": 0.35, "expense_mult": 1.3, "sectors": ["poultry", "dairy"]},
    "emi_burden": {"income_mult": 0.9, "expense_mult": 1.2, "sectors": ["dairy", "poultry", "food_processing", "handicrafts", "rural_retail"]},
}


@dataclass
class ShockEvent:
    enterprise_id: str
    shock_type: str
    start_day: int   # offset from simulation start
    duration_days: int
    income_mult: float
    expense_mult: float


def sample_shocks(rng: np.random.Generator, enterprise_id: str, sector: str,
                   n_days: int, max_shocks: int = 2) -> list[ShockEvent]:
    """Sample 0..max_shocks shock events for one enterprise across the simulation window."""
    eligible = [s for s, cfg in SHOCK_EFFECTS.items() if sector in cfg["sectors"]]
    if not eligible:
        eligible = list(SHOCK_EFFECTS.keys())

    n_shocks = rng.choice([0, 1, 2], p=[0.35, 0.4, 0.25])
    n_shocks = min(n_shocks, max_shocks)
    events: list[ShockEvent] = []
    # keep shocks away from the very start/end and from overlapping
    used_ranges: list[tuple[int, int]] = []
    attempts = 0
    while len(events) < n_shocks and attempts < 20:
        attempts += 1
        shock_type = rng.choice(eligible)
        duration = int(rng.integers(30, 90))
        start = int(rng.integers(60, max(n_days - duration - 30, 61)))
        window = (start, start + duration)
        if any(not (window[1] < r[0] or window[0] > r[1]) for r in used_ranges):
            continue
        used_ranges.append(window)
        cfg = SHOCK_EFFECTS[shock_type]
        events.append(ShockEvent(
            enterprise_id=enterprise_id,
            shock_type=shock_type,
            start_day=start,
            duration_days=duration,
            income_mult=cfg["income_mult"] * float(rng.uniform(0.9, 1.05)),
            expense_mult=cfg["expense_mult"] * float(rng.uniform(0.95, 1.1)),
        ))
    return events


def daily_multipliers(events: list[ShockEvent], n_days: int) -> tuple[np.ndarray, np.ndarray]:
    """Return (income_mult, expense_mult) arrays of length n_days, default 1.0."""
    income_mult = np.ones(n_days)
    expense_mult = np.ones(n_days)
    for ev in events:
        end = min(ev.start_day + ev.duration_days, n_days)
        if ev.start_day >= n_days:
            continue
        income_mult[ev.start_day:end] *= ev.income_mult
        expense_mult[ev.start_day:end] *= ev.expense_mult
    return income_mult, expense_mult
