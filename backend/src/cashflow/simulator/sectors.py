"""Sector definitions: seasonality curves, category sets, and commodity/climate linkage.

All curves are indexed by calendar month (1-12) and expressed as multipliers
around 1.0 so `base_level * curve[month]` gives an intuitive scale.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class SectorProfile:
    key: str
    label: str
    # income seasonality multiplier by month (1-12)
    income_seasonality: dict[int, float]
    # expense seasonality multiplier by month (1-12)
    expense_seasonality: dict[int, float]
    # which simulated commodity series drives this sector's costs/income
    input_commodity: str
    output_commodity: str
    income_categories: list[str]
    expense_categories: list[str]
    # batch-cycle length in days (0 = continuous/daily income, e.g. poultry ~50)
    batch_cycle_days: int = 0
    # sensitivity multipliers (how strongly external shocks move this sector)
    heat_sensitivity: float = 0.3
    rain_sensitivity: float = 0.3
    festival_sensitivity: float = 0.2


DAIRY = SectorProfile(
    key="dairy",
    label="Dairy",
    income_seasonality={1: 1.05, 2: 1.05, 3: 1.0, 4: 0.9, 5: 0.8, 6: 0.85,
                         7: 0.95, 8: 1.0, 9: 1.0, 10: 1.05, 11: 1.1, 12: 1.1},
    expense_seasonality={1: 1.0, 2: 1.0, 3: 1.0, 4: 1.05, 5: 1.15, 6: 1.1,
                          7: 1.0, 8: 1.0, 9: 1.0, 10: 1.0, 11: 1.0, 12: 1.0},
    input_commodity="fodder_price",
    output_commodity="milk_price",
    income_categories=["milk_sale", "ghee_sale", "cattle_sale", "manure_sale"],
    expense_categories=["fodder", "veterinary", "cattle_feed", "labour", "loan_emi"],
    heat_sensitivity=0.6,
    rain_sensitivity=0.2,
    festival_sensitivity=0.1,
)

POULTRY = SectorProfile(
    key="poultry",
    label="Poultry",
    income_seasonality={1: 1.05, 2: 1.0, 3: 0.95, 4: 0.9, 5: 0.85, 6: 0.9,
                         7: 0.95, 8: 1.0, 9: 1.05, 10: 1.15, 11: 1.2, 12: 1.1},
    expense_seasonality={1: 1.0, 2: 1.0, 3: 1.0, 4: 1.05, 5: 1.1, 6: 1.05,
                          7: 1.0, 8: 1.0, 9: 1.0, 10: 1.0, 11: 1.0, 12: 1.0},
    input_commodity="feed_price",
    output_commodity="broiler_price",
    income_categories=["broiler_sale", "egg_sale"],
    expense_categories=["feed", "chicks", "veterinary", "labour", "loan_emi"],
    batch_cycle_days=49,
    heat_sensitivity=0.5,
    rain_sensitivity=0.15,
    festival_sensitivity=0.35,
)

FOOD_PROCESSING = SectorProfile(
    key="food_processing",
    label="Food Processing",
    income_seasonality={1: 1.1, 2: 1.05, 3: 1.0, 4: 0.9, 5: 0.85, 6: 0.85,
                         7: 0.9, 8: 0.95, 9: 1.05, 10: 1.2, 11: 1.25, 12: 1.15},
    expense_seasonality={1: 1.15, 2: 1.05, 3: 0.95, 4: 0.85, 5: 0.85, 6: 0.9,
                          7: 0.95, 8: 1.0, 9: 1.1, 10: 1.15, 11: 1.05, 12: 1.0},
    input_commodity="raw_grain_price",
    output_commodity="processed_food_price",
    income_categories=["product_sale", "bulk_order", "retail_order"],
    expense_categories=["raw_material", "packaging", "labour", "storage", "loan_emi"],
    heat_sensitivity=0.2,
    rain_sensitivity=0.35,
    festival_sensitivity=0.4,
)

HANDICRAFTS = SectorProfile(
    key="handicrafts",
    label="Handicrafts",
    income_seasonality={1: 0.9, 2: 0.85, 3: 0.85, 4: 0.8, 5: 0.8, 6: 0.85,
                         7: 0.9, 8: 1.0, 9: 1.2, 10: 1.5, 11: 1.6, 12: 1.2},
    expense_seasonality={1: 0.9, 2: 0.9, 3: 0.9, 4: 0.85, 5: 0.85, 6: 0.9,
                          7: 0.95, 8: 1.05, 9: 1.2, 10: 1.3, 11: 1.1, 12: 0.95},
    input_commodity="raw_material_price",
    output_commodity="handicraft_export_price",
    income_categories=["retail_sale", "export_order", "exhibition_sale"],
    expense_categories=["raw_material", "tools", "labour", "transport", "loan_emi"],
    heat_sensitivity=0.1,
    rain_sensitivity=0.15,
    festival_sensitivity=0.7,
)

RURAL_RETAIL = SectorProfile(
    key="rural_retail",
    label="Rural Retail",
    income_seasonality={1: 1.1, 2: 1.0, 3: 0.95, 4: 0.9, 5: 0.9, 6: 0.9,
                         7: 0.9, 8: 0.95, 9: 1.0, 10: 1.2, 11: 1.25, 12: 1.15},
    expense_seasonality={1: 1.0, 2: 1.0, 3: 1.0, 4: 1.0, 5: 1.0, 6: 1.0,
                          7: 1.0, 8: 1.0, 9: 1.05, 10: 1.1, 11: 1.05, 12: 1.0},
    input_commodity="wholesale_price",
    output_commodity="retail_price",
    income_categories=["daily_sale", "credit_sale_collection"],
    expense_categories=["stock_purchase", "transport", "rent", "labour", "loan_emi"],
    heat_sensitivity=0.15,
    rain_sensitivity=0.4,
    festival_sensitivity=0.5,
)

SECTORS: dict[str, SectorProfile] = {
    s.key: s for s in [DAIRY, POULTRY, FOOD_PROCESSING, HANDICRAFTS, RURAL_RETAIL]
}

# Festival peaks (month, day-of-month, strength) used for demand spikes across sectors.
FESTIVAL_PEAKS: list[tuple[int, int, float]] = [
    (3, 8, 0.6),    # Holi
    (8, 19, 0.5),   # Raksha Bandhan / Independence season
    (10, 12, 1.0),  # Dussehra
    (10, 31, 1.4),  # Diwali
    (12, 25, 0.4),  # Wedding season lead-in
]
