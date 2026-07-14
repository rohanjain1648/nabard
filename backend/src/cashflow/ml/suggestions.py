"""Suggestion lookup: (sector, driver_key) -> Suggestion row, falling back to the
sector-agnostic "all" entries in suggestions.yaml (TRD.md FR-5)."""
from __future__ import annotations

from sqlalchemy.orm import Session


def pick_suggestion(db: Session, sector: str, driver_key: str):
    from cashflow.api import models as m

    suggestion = (
        db.query(m.Suggestion)
        .filter(m.Suggestion.sector == sector, m.Suggestion.driver_key == driver_key)
        .first()
    )
    if suggestion is None:
        suggestion = (
            db.query(m.Suggestion)
            .filter(m.Suggestion.sector == "all", m.Suggestion.driver_key == driver_key)
            .first()
        )
    return suggestion
