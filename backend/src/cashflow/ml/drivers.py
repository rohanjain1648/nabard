"""Maps raw model feature names to the human-facing driver taxonomy used by
alerts and the suggestion library (TRD.md FR-4.1, FR-5; suggestions.yaml).

`sign` says which direction of the feature pushes risk up: "high" means a large
value increases risk (e.g. days_since_last_entry), "low" means a small/negative
value increases risk (e.g. savings_runway_months).
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DriverMapping:
    driver_key: str
    risk_increasing_direction: str  # "high" | "low"


FEATURE_TO_DRIVER: dict[str, DriverMapping] = {
    "savings_runway_months": DriverMapping("liquidity_shortfall", "low"),
    "inflow_outflow_ratio": DriverMapping("liquidity_shortfall", "low"),
    "emi_coverage": DriverMapping("emi_pressure", "low"),
    "days_since_last_entry": DriverMapping("disengagement", "high"),
    "entry_regularity": DriverMapping("disengagement", "low"),
    "input_level_z": DriverMapping("commodity_input_price_spike", "high"),
    "input_momentum_3m": DriverMapping("commodity_input_price_spike", "high"),
    "input_volatility": DriverMapping("commodity_input_price_spike", "high"),
    "output_level_z": DriverMapping("commodity_output_price_drop", "low"),
    "output_momentum_3m": DriverMapping("commodity_output_price_drop", "low"),
    "heat_index": DriverMapping("climate_heat_stress", "high"),
    "heat_index_pctile": DriverMapping("climate_heat_stress", "high"),
    "rainfall_anomaly_mm": DriverMapping("climate_rainfall_anomaly", "high"),
    "months_to_festival": DriverMapping("demand_seasonal_dip", "high"),
    "calendar_month": DriverMapping("demand_seasonal_dip", "high"),
    "net_flow_roll_std3": DriverMapping("income_volatility", "high"),
    "net_flow_roll_std6": DriverMapping("income_volatility", "high"),
    "net_flow_lag1": DriverMapping("income_volatility", "low"),
    "net_flow_lag2": DriverMapping("income_volatility", "low"),
    "net_flow_lag3": DriverMapping("income_volatility", "low"),
    "net_flow_lag6": DriverMapping("income_volatility", "low"),
    "net_flow_lag12": DriverMapping("income_volatility", "low"),
    "net_flow_roll_mean3": DriverMapping("liquidity_shortfall", "low"),
    "net_flow_roll_mean6": DriverMapping("liquidity_shortfall", "low"),
}

DRIVER_LABELS_EN: dict[str, str] = {
    "liquidity_shortfall": "Projected balance may fall short of upcoming obligations",
    "emi_pressure": "Loan repayment coverage is tight",
    "disengagement": "Irregular or missing transaction logging",
    "commodity_input_price_spike": "Rising input/raw-material costs",
    "commodity_output_price_drop": "Falling prices for what you sell",
    "climate_heat_stress": "Heat stress affecting output",
    "climate_rainfall_anomaly": "Unusual rainfall pattern",
    "demand_seasonal_dip": "Seasonally low-demand period",
    "income_volatility": "Income more unpredictable than usual",
}


def top_drivers_from_shap(feature_row: dict[str, float], shap_row: dict[str, float], top_n: int = 3) -> list[dict]:
    """Given one prediction's feature values and SHAP contributions (toward higher risk),
    return the top-N drivers whose direction is consistent with actually increasing risk.
    """
    candidates = []
    for feat, shap_val in shap_row.items():
        mapping = FEATURE_TO_DRIVER.get(feat)
        if mapping is None or shap_val <= 0:
            continue  # only features actually pushing risk up are "drivers"
        candidates.append({
            "feature": feat,
            "driver_key": mapping.driver_key,
            "weight": float(shap_val),
            "human_text": DRIVER_LABELS_EN[mapping.driver_key],
        })
    candidates.sort(key=lambda c: c["weight"], reverse=True)

    # de-duplicate by driver_key (several features can map to the same driver), keep strongest
    seen: set[str] = set()
    deduped = []
    for c in candidates:
        if c["driver_key"] in seen:
            continue
        seen.add(c["driver_key"])
        deduped.append(c)
    return deduped[:top_n]
