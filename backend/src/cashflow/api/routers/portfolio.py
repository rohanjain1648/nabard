from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from .. import models as m
from ..db import get_db
from ..deps import CurrentUser, require_officer
from ..schemas import PortfolioItem, PortfolioSummary

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


def _assigned_enterprise_ids(officer_id: str, db: Session) -> list[str]:
    return [
        row[0] for row in
        db.query(m.OfficerAssignment.enterprise_id).filter(m.OfficerAssignment.officer_id == officer_id).all()
    ]


def _latest_scores(enterprise_ids: list[str], db: Session) -> dict[str, m.RiskScore]:
    # latest RiskScore row per enterprise, via a correlated subquery on max(as_of)
    subq = (
        db.query(m.RiskScore.enterprise_id, func.max(m.RiskScore.as_of).label("max_as_of"))
        .filter(m.RiskScore.enterprise_id.in_(enterprise_ids))
        .group_by(m.RiskScore.enterprise_id)
        .subquery()
    )
    rows = (
        db.query(m.RiskScore)
        .join(subq, (m.RiskScore.enterprise_id == subq.c.enterprise_id) & (m.RiskScore.as_of == subq.c.max_as_of))
        .all()
    )
    return {r.enterprise_id: r for r in rows}


@router.get("", response_model=list[PortfolioItem])
def list_portfolio(
    band: str | None = Query(default=None),
    sector: str | None = Query(default=None),
    q: str | None = Query(default=None),
    sort: str = Query(default="score"),
    user: CurrentUser = Depends(require_officer),
    db: Session = Depends(get_db),
) -> list[PortfolioItem]:
    enterprise_ids = _assigned_enterprise_ids(user.officer_id, db)
    enterprises = db.query(m.Enterprise).filter(m.Enterprise.id.in_(enterprise_ids)).all()
    scores = _latest_scores(enterprise_ids, db)

    last_entries = dict(
        db.query(m.Entry.enterprise_id, func.max(m.Entry.occurred_at))
        .filter(m.Entry.enterprise_id.in_(enterprise_ids))
        .group_by(m.Entry.enterprise_id)
        .all()
    )

    items = []
    for ent in enterprises:
        score_row = scores.get(ent.id)
        item = PortfolioItem(
            enterprise_id=ent.id, name=ent.name, sector=ent.sector, village=ent.village, district=ent.district,
            band=score_row.band if score_row else "unknown",
            score=score_row.score if score_row else 0.0,
            last_entry_at=last_entries.get(ent.id),
        )
        if band and item.band != band:
            continue
        if sector and item.sector != sector:
            continue
        if q and q.lower() not in item.name.lower() and q.lower() not in item.village.lower():
            continue
        items.append(item)

    band_priority = {"red": 0, "amber": 1, "unknown": 2, "green": 3}
    if sort == "score":
        items.sort(key=lambda i: (band_priority.get(i.band, 2), i.score))
    elif sort == "name":
        items.sort(key=lambda i: i.name)
    elif sort == "last_entry":
        items.sort(key=lambda i: i.last_entry_at or date.min)
    return items


@router.get("/summary", response_model=PortfolioSummary)
def portfolio_summary(user: CurrentUser = Depends(require_officer), db: Session = Depends(get_db)) -> PortfolioSummary:
    enterprise_ids = _assigned_enterprise_ids(user.officer_id, db)
    enterprises = {e.id: e for e in db.query(m.Enterprise).filter(m.Enterprise.id.in_(enterprise_ids)).all()}
    scores = _latest_scores(enterprise_ids, db)

    counts = {"green": 0, "amber": 0, "red": 0}
    heatmap: dict[str, dict[str, int]] = {}
    for eid, ent in enterprises.items():
        score_row = scores.get(eid)
        band = score_row.band if score_row else "green"
        counts[band] = counts.get(band, 0) + 1
        heatmap.setdefault(ent.sector, {"green": 0, "amber": 0, "red": 0})
        heatmap[ent.sector][band] = heatmap[ent.sector].get(band, 0) + 1

    return PortfolioSummary(
        green=counts["green"], amber=counts["amber"], red=counts["red"],
        total=len(enterprises), sector_heatmap=heatmap,
    )
