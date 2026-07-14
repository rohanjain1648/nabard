"""Simulated external signal generators: commodity prices, weather/climate, UPI-activity proxy.

These stand behind the same interface real adapters (Agmarknet/e-NAM, IMD/ERA5,
AA-framework/NPCI aggregates) would implement later — see ARCHITECTURE.md §7.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

COMMODITY_SERIES = [
    "fodder_price", "milk_price", "feed_price", "broiler_price",
    "raw_grain_price", "processed_food_price", "raw_material_price",
    "handicraft_export_price", "wholesale_price", "retail_price",
]

COMMODITY_BASE_LEVEL = {
    "fodder_price": 18.0, "milk_price": 42.0, "feed_price": 32.0, "broiler_price": 110.0,
    "raw_grain_price": 24.0, "processed_food_price": 55.0, "raw_material_price": 40.0,
    "handicraft_export_price": 300.0, "wholesale_price": 20.0, "retail_price": 26.0,
}


def _mean_reverting_walk(rng: np.random.Generator, n_days: int, base: float,
                          vol: float = 0.01, reversion: float = 0.02,
                          jump_prob: float = 0.01, jump_scale: float = 0.15) -> np.ndarray:
    """Ornstein-Uhlenbeck-ish random walk with occasional jumps (price shocks)."""
    series = np.empty(n_days)
    level = base
    for t in range(n_days):
        shock = rng.normal(0, vol) * base
        pull = reversion * (base - level)
        level = level + pull + shock
        if rng.random() < jump_prob:
            direction = rng.choice([-1, 1])
            level += direction * jump_scale * base * rng.random()
        level = max(level, base * 0.3)
        series[t] = level
    return series


def generate_commodity_prices(rng: np.random.Generator, dates: pd.DatetimeIndex) -> pd.DataFrame:
    n = len(dates)
    frames = []
    for series_key, base in COMMODITY_BASE_LEVEL.items():
        values = _mean_reverting_walk(rng, n, base)
        frames.append(pd.DataFrame({
            "date": dates, "series_key": series_key, "region": "ALL", "value": values,
        }))
    return pd.concat(frames, ignore_index=True)


def generate_weather(rng: np.random.Generator, dates: pd.DatetimeIndex, region: str) -> pd.DataFrame:
    """Rainfall anomaly (mm deviation from climatology) and heat index (0-1 percentile-like)."""
    doy = dates.dayofyear.values
    # Monsoon-shaped climatology: peak rainfall around day ~180-240 (Jun-Sep)
    monsoon_shape = np.clip(np.sin((doy - 150) / 120 * np.pi), 0, 1)
    climatology = monsoon_shape * 12.0  # mm/day expected in-season
    noise = rng.normal(0, 4.0, size=len(dates))
    # occasional anomaly blocks (drought or excess rain runs of 5-20 days)
    anomaly = np.zeros(len(dates))
    i = 0
    while i < len(dates):
        if rng.random() < 0.015:
            run_len = rng.integers(5, 20)
            magnitude = rng.choice([-1, 1]) * rng.uniform(4, 10)
            anomaly[i:i + run_len] = magnitude
            i += run_len
        else:
            i += 1
    rainfall = np.clip(climatology + noise + anomaly, 0, None)
    rainfall_anomaly = rainfall - climatology

    heat_shape = np.clip(np.sin((doy - 60) / 150 * np.pi), -0.2, 1)
    heat_index = np.clip(heat_shape + rng.normal(0, 0.05, size=len(dates)), 0, 1)

    return pd.DataFrame({
        "date": dates, "series_key": "rainfall_anomaly_mm", "region": region, "value": rainfall_anomaly,
    }), pd.DataFrame({
        "date": dates, "series_key": "heat_index", "region": region, "value": heat_index,
    })


def generate_upi_activity_index(rng: np.random.Generator, dates: pd.DatetimeIndex, region: str) -> pd.DataFrame:
    """Aggregate, non-personal proxy: relative digital-payment activity level for the region (0-1)."""
    trend = np.linspace(0.4, 0.75, len(dates))  # secular UPI adoption growth
    weekly = 0.05 * np.sin(2 * np.pi * np.arange(len(dates)) / 7)
    noise = rng.normal(0, 0.03, size=len(dates))
    values = np.clip(trend + weekly + noise, 0, 1)
    return pd.DataFrame({
        "date": dates, "series_key": "upi_activity_index", "region": region, "value": values,
    })
